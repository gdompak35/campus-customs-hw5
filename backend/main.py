"""FastAPI backend for the Campus Customs operations dashboard."""
import json
import shutil
import sqlite3
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

try:
    from .team import resolve_ticket
except ImportError:  # supports `uvicorn main:app` from backend/
    from team import resolve_ticket

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "campus_customs_new.db"
ORIGINAL_DB = ROOT / "data" / "campus_customs.db"
AUDIT = ROOT / "output" / "audit_trail.json"
app = FastAPI(title="Campus Customs Operations API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/", response_class=HTMLResponse)
def navigation() -> str:
    return """<!doctype html><html><head><title>Campus Customs API</title>
    <style>body{font:16px Arial;max-width:760px;margin:40px auto;color:#172b4d}a{display:block;margin:12px 0;color:#1769aa}code{background:#eef3f8;padding:3px 6px}</style>
    </head><body><h1>Campus Customs Operations API</h1><p>Backend is running.</p>
    <h2>Navigation</h2><a href="/docs">Interactive API documentation</a>
    <a href="/api/tickets">View tickets</a><a href="/api/events">View recent agent events</a>
    <a href="/api/cash">View checking balance</a><p>POST actions are available in <a href="/docs">the interactive docs</a>.</p>
    </body></html>"""

class ApprovalRequest(BaseModel):
    kind: Literal["invoice", "lease", "purchase"]
    ref_id: int
    approved_by: str = Field(min_length=1)

class ResolutionRequest(BaseModel):
    outcome: str = Field(min_length=1)
    approved_by: str = Field(min_length=1)

def query(sql: str, params: tuple = ()) -> list[dict]:
    with sqlite3.connect(DB) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute(sql, params).fetchall()]

def append_audit(agent: str, step: str, ticket_id: int | None, detail: object) -> None:
    records = []
    if AUDIT.exists():
        try: records = json.loads(AUDIT.read_text(encoding="utf-8"))
        except json.JSONDecodeError: records = []
    if not isinstance(records, list): records = []
    from datetime import datetime, timezone
    records.append({"timestamp": datetime.now(timezone.utc).isoformat(), "agent": agent, "step": step, "ticket_id": ticket_id, "detail": detail})
    AUDIT.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")

@app.get("/api/tickets")
def get_tickets() -> list[dict]:
    return query("SELECT id, type, requester, subject, sku, size, qty, status, notes, created_at FROM tickets ORDER BY id")

@app.post("/api/tickets/{ticket_id}/run")
async def run_ticket(ticket_id: int) -> dict:
    rows = query("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    if not rows: raise HTTPException(404, "Ticket not found")
    append_audit("backend", "ticket_run_requested", ticket_id, {"ticket": rows[0]})
    decision = await resolve_ticket(json.dumps(rows[0]), ticket_id)
    if decision.status == "resolved":
        with sqlite3.connect(DB) as db:
            db.execute("UPDATE tickets SET status = 'resolved' WHERE id = ?", (ticket_id,))
            db.commit()
    append_audit("backend", "ticket_run_complete", ticket_id, decision.model_dump())
    return decision.model_dump()

@app.get("/api/events")
def get_events(limit: int = Query(100, ge=1, le=500)) -> list[dict]:
    if not AUDIT.exists(): return []
    try: records = json.loads(AUDIT.read_text(encoding="utf-8"))
    except json.JSONDecodeError: return []
    return records[-limit:]

@app.post("/api/tickets/{ticket_id}/finalize")
def finalize_ticket(ticket_id: int) -> dict:
    """Finalize a ticket only when its linked invoice has already been paid."""
    with sqlite3.connect(DB) as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT t.*, i.status AS invoice_status FROM tickets t LEFT JOIN invoices i ON i.id=t.invoice_id WHERE t.id=?", (ticket_id,)).fetchone()
        if not row: raise HTTPException(404, "Ticket not found")
        paid_lease = db.execute("SELECT 1 FROM payments WHERE kind='lease' AND ref_id=?", (row["lease_id"],)).fetchone() if row["lease_id"] is not None else None
        if row["invoice_status"] != "paid" and not paid_lease: raise HTTPException(409, "Ticket cannot be finalized until its linked invoice or lease is paid")
        db.execute("UPDATE tickets SET status='resolved' WHERE id=?", (ticket_id,))
        db.commit()
    append_audit("backend", "ticket_finalized", ticket_id, {"reason": "linked invoice is paid"})
    return {"ticket_id": ticket_id, "status": "resolved"}

@app.post("/api/tickets/{ticket_id}/resolve")
def resolve_with_human_decision(ticket_id: int, request: ResolutionRequest) -> dict:
    """Close a ticket only with an explicit human decision and recorded outcome."""
    with sqlite3.connect(DB) as db:
        row = db.execute("SELECT id, status FROM tickets WHERE id=?", (ticket_id,)).fetchone()
        if not row: raise HTTPException(404, "Ticket not found")
        db.execute("UPDATE tickets SET status='resolved', notes=notes || ' Resolution: ' || ? WHERE id=?", (request.outcome, ticket_id))
        db.commit()
    append_audit("human_approval", "ticket_resolved", ticket_id, {"outcome": request.outcome, "approved_by": request.approved_by})
    return {"ticket_id": ticket_id, "status": "resolved", "outcome": request.outcome, "approved_by": request.approved_by}

@app.post("/api/approvals")
def approve_payment_or_purchase(request: ApprovalRequest) -> dict:
    """Apply an explicitly human-approved invoice/lease payment to the working DB."""
    with sqlite3.connect(DB) as db:
        db.row_factory = sqlite3.Row
        if request.kind in ("invoice", "purchase"):
            row = db.execute("SELECT * FROM invoices WHERE id = ? AND status = 'open'", (request.ref_id,)).fetchone()
            if not row: raise HTTPException(404, "Open invoice not found")
            amount, account, kind = row["amount"], "checking", "invoice"
            db.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (request.ref_id,))
        else:
            row = db.execute("SELECT * FROM leases WHERE id = ?", (request.ref_id,)).fetchone()
            if not row: raise HTTPException(404, "Lease not found")
            amount, account, kind = row["monthly_rent"], "checking", "lease"
        balance = db.execute("SELECT balance FROM cash_accounts WHERE name = ?", (account,)).fetchone()
        if not balance or balance[0] < amount: raise HTTPException(409, "Payment refused: insufficient cash")
        db.execute("UPDATE cash_accounts SET balance = balance - ?, date = (SELECT date_today FROM desk) WHERE name = ?", (amount, account))
        cursor = db.execute("INSERT INTO payments(kind, ref_id, amount, account, paid_at, approved_by) VALUES (?, ?, ?, ?, (SELECT date_today FROM desk), ?)", (kind, request.ref_id, amount, account, request.approved_by))
        if kind == "lease":
            resolved = db.execute("UPDATE tickets SET status = 'resolved' WHERE lease_id = ? AND status = 'open'", (request.ref_id,)).rowcount
        else:
            resolved = db.execute("UPDATE tickets SET status = 'resolved' WHERE invoice_id = ? AND status = 'open'", (request.ref_id,)).rowcount
        db.commit()
    append_audit("human_approval", "payment_applied", None, {"kind": kind, "ref_id": request.ref_id, "amount": amount, "approved_by": request.approved_by, "tickets_resolved": resolved})
    return {"status": "paid", "kind": kind, "ref_id": request.ref_id, "amount": amount, "approved_by": request.approved_by, "tickets_resolved": resolved}

@app.get("/api/cash")
def get_cash() -> dict:
    rows = query("SELECT * FROM cash_accounts WHERE name = 'checking'")
    if not rows: raise HTTPException(404, "Checking account not found")
    return rows[0]

@app.post("/api/reset")
def reset_database() -> dict:
    shutil.copy2(ORIGINAL_DB, DB)
    append_audit("backend", "database_reset", None, {"source": str(ORIGINAL_DB), "working": str(DB)})
    return {"status": "reset", "database": "data/campus_customs_new.db"}
