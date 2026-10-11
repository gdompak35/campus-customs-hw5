from typing import Literal
from pydantic import BaseModel, Field

Role = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]

class Ticket(BaseModel):
    id: int
    type: str
    requester: str
    subject: str
    sku: str | None = None
    size: str | None = None
    qty: int | None = None
    lease_id: int | None = None
    invoice_id: int | None = None
    status: str
    notes: str
    created_at: str

class Delegation(BaseModel):
    from_role: Role
    to_role: Role
    task: str = Field(min_length=1)
    ticket_id: int

class AgentFinding(BaseModel):
    role: Role
    ticket_id: int
    summary: str
    facts: dict[str, object] = Field(default_factory=dict)
    needs_human_approval: bool = False

class TicketDecision(BaseModel):
    ticket_id: int
    status: Literal["open", "in_progress", "awaiting_approval", "resolved"]
    decision: str
    delegations: list[Delegation] = Field(default_factory=list)
    findings: list[AgentFinding] = Field(default_factory=list)
