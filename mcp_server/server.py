"""FastMCP tools for Campus Customs ticket resolution."""
import json
import sqlite3
from pathlib import Path
from typing import Any
from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "campus_customs_new.db"
mcp = FastMCP("Campus Customs Operations")

def _query(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute(sql, params).fetchall()]

def _result(tool: str, ticket_id: int, **data: Any) -> str:
    return json.dumps({"tool": tool, "ticket_id": ticket_id, "data": data}, default=str)

@mcp.tool()
def check_customer_order_and_restock(ticket_id: int = 101) -> str:
    """Check customer-order stock, invoices, and vendor restock facts."""
    tickets = _query("SELECT * FROM tickets WHERE id = ? AND type = 'customer_order'", (ticket_id,))
    if not tickets: return _result("check_customer_order_and_restock", ticket_id, error="No matching customer-order ticket found.")
    t = tickets[0]
    stock = _query("SELECT * FROM inventory WHERE sku = ? AND size = ?", (t["sku"], t["size"]))
    invoices = _query("SELECT i.*, v.name AS vendor_name, v.specialty, v.lead_days FROM invoices i LEFT JOIN vendors v ON v.id=i.vendor_id WHERE i.status='open' AND i.description LIKE ?", (f"%{t['sku']}%",))
    return _result("check_customer_order_and_restock", ticket_id, ticket=t, inventory=stock, open_related_invoices=invoices)

@mcp.tool()
def check_rent_payment_status(ticket_id: int = 102) -> str:
    """Check a rent ticket against its lease, shop date, cash, and payments."""
    tickets = _query("SELECT * FROM tickets WHERE id = ? AND type = 'rent_notice'", (ticket_id,))
    if not tickets: return _result("check_rent_payment_status", ticket_id, error="No matching rent-notice ticket found.")
    t = tickets[0]
    return _result("check_rent_payment_status", ticket_id, ticket=t, lease=_query("SELECT * FROM leases WHERE id=?", (t["lease_id"],)), desk=_query("SELECT * FROM desk"), cash_accounts=_query("SELECT * FROM cash_accounts"), related_payments=_query("SELECT * FROM payments WHERE kind='lease' AND ref_id=?", (t["lease_id"],)))

@mcp.tool()
def evaluate_bulk_order_and_restock(ticket_id: int = 103) -> str:
    """Evaluate bulk-order stock, pricing, invoices, and vendor lead times."""
    tickets = _query("SELECT * FROM tickets WHERE id = ? AND type = 'price_override'", (ticket_id,))
    if not tickets: return _result("evaluate_bulk_order_and_restock", ticket_id, error="No matching bulk-order ticket found.")
    t = tickets[0]
    stock = _query("SELECT * FROM inventory WHERE sku=? AND size=?", (t["sku"], t["size"]))
    pricing = _query("SELECT * FROM pricing WHERE sku=?", (t["sku"],))
    invoices = _query("SELECT i.*, v.name AS vendor_name, v.specialty, v.lead_days FROM invoices i LEFT JOIN vendors v ON v.id=i.vendor_id WHERE i.status='open' AND i.description LIKE ?", (f"%{t['sku']}%",))
    return _result("evaluate_bulk_order_and_restock", ticket_id, ticket=t, inventory=stock, pricing=pricing, open_related_invoices=invoices)

if __name__ == "__main__": mcp.run()
