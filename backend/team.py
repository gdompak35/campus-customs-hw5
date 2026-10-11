"""PydanticAI multi-agent team; every role uses gpt-6-luna through Portkey."""
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
try:
    from .models import AgentFinding, Delegation, Role, TicketDecision
    from .mcp_client import call_mcp_tool
except ImportError:  # supports direct imports when uvicorn runs inside backend/
    from models import AgentFinding, Delegation, Role, TicketDecision
    from mcp_client import call_mcp_tool

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=True)
MODEL_NAME = "gpt-6-luna"

def _model() -> OpenAIChatModel:
    key = os.environ["PORTKEY_API_KEY"]
    settings = OpenAIChatModelSettings(openai_reasoning_effort="none")
    return OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(api_key=key, base_url="https://api.portkey.ai/v1"), settings=settings)

def _prompt(role: str) -> str:
    return (ROOT / "backend" / "prompts" / f"{role}.md").read_text(encoding="utf-8")

class TeamDeps:
    def __init__(self, ticket_id: int):
        self.ticket_id = ticket_id
        self.current_role: Role = "boss"
        self.delegations: list[Delegation] = []
        self.findings: list[AgentFinding] = []

    def delegate(self, from_role: Role, to_role: Role, task: str) -> str:
        self.delegations.append(Delegation(from_role=from_role, to_role=to_role, task=task, ticket_id=self.ticket_id))
        return f"Delegated to {to_role}; use that role's database-backed finding before deciding."

def _audit(agent: Role, step: str, ticket_id: int, detail: object) -> None:
    path = ROOT / "output" / "audit_trail.json"
    records = []
    if path.exists():
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            records = []
    if not isinstance(records, list):
        records = []
    records.append({"timestamp": datetime.now(timezone.utc).isoformat(), "agent": agent, "step": step, "ticket_id": ticket_id, "detail": detail})
    path.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")

def _agent(role: Role, output_type: Any = AgentFinding) -> Agent:
    return Agent(_model(), output_type=output_type, system_prompt=_prompt(role))

boss = _agent("boss", TicketDecision)
inventory = _agent("inventory")
accounting = _agent("accounting")
facilities = _agent("facilities")
customer_service = _agent("customer_service")
SPECIALISTS: dict[Role, Agent] = {"inventory": inventory, "accounting": accounting, "facilities": facilities, "customer_service": customer_service}

async def _database_tool(ctx: RunContext[TeamDeps], tool: str) -> str:
    tool = {101: "check_customer_order_and_restock", 102: "check_rent_payment_status", 103: "evaluate_bulk_order_and_restock"}.get(ctx.deps.ticket_id, tool)
    _audit(ctx.deps.current_role, "mcp_call_start", ctx.deps.ticket_id, {"tool": tool})
    result = await call_mcp_tool(tool, {"ticket_id": ctx.deps.ticket_id})
    _audit(ctx.deps.current_role, "mcp_call_complete", ctx.deps.ticket_id, {"tool": tool, "result": result})
    return json.dumps(result)

for _role, _agent_obj, _tool_name in [
    ("boss", boss, "check_customer_order_and_restock"),
    ("inventory", inventory, "check_customer_order_and_restock"),
    ("accounting", accounting, "check_rent_payment_status"),
    ("facilities", facilities, "check_rent_payment_status"),
    ("customer_service", customer_service, "check_customer_order_and_restock"),
]:
    async def query_shop_facts(ctx: RunContext[TeamDeps], _tool_name=_tool_name) -> str:
        return await _database_tool(ctx, _tool_name)
    query_shop_facts.__name__ = f"{_role}_query_shop_facts"
    _agent_obj.tool(query_shop_facts)

@boss.tool
def boss_delegate_inventory(ctx: RunContext[TeamDeps], task: str) -> str:
    return ctx.deps.delegate("boss", "inventory", task)

@boss.tool
def boss_delegate_accounting(ctx: RunContext[TeamDeps], task: str) -> str:
    return ctx.deps.delegate("boss", "accounting", task)

@boss.tool
def boss_delegate_facilities(ctx: RunContext[TeamDeps], task: str) -> str:
    return ctx.deps.delegate("boss", "facilities", task)

@boss.tool
def boss_delegate_customer_service(ctx: RunContext[TeamDeps], task: str) -> str:
    return ctx.deps.delegate("boss", "customer_service", task)

@inventory.tool
def inventory_delegate(ctx: RunContext[TeamDeps], task: str) -> str:
    return ctx.deps.delegate("inventory", "accounting", task)

@inventory.tool
def inventory_delegate_customer_service(ctx: RunContext[TeamDeps], task: str) -> str:
    return ctx.deps.delegate("inventory", "customer_service", task)

@accounting.tool
def accounting_delegate_inventory(ctx: RunContext[TeamDeps], task: str) -> str:
    return ctx.deps.delegate("accounting", "inventory", task)

@accounting.tool
def accounting_delegate_facilities(ctx: RunContext[TeamDeps], task: str) -> str:
    return ctx.deps.delegate("accounting", "facilities", task)

@accounting.tool
def accounting_delegate_customer_service(ctx: RunContext[TeamDeps], task: str) -> str:
    return ctx.deps.delegate("accounting", "customer_service", task)

@facilities.tool
def facilities_delegate_accounting(ctx: RunContext[TeamDeps], task: str) -> str:
    return ctx.deps.delegate("facilities", "accounting", task)

@facilities.tool
def facilities_delegate_inventory(ctx: RunContext[TeamDeps], task: str) -> str:
    return ctx.deps.delegate("facilities", "inventory", task)

@customer_service.tool
def customer_service_delegate_inventory(ctx: RunContext[TeamDeps], task: str) -> str:
    return ctx.deps.delegate("customer_service", "inventory", task)

@customer_service.tool
def customer_service_delegate_accounting(ctx: RunContext[TeamDeps], task: str) -> str:
    return ctx.deps.delegate("customer_service", "accounting", task)

async def resolve_ticket(ticket_text: str, ticket_id: int) -> TicketDecision:
    deps = TeamDeps(ticket_id)
    deps.current_role = "boss"
    _audit("boss", "run_start", ticket_id, {"input": ticket_text})
    result = await boss.run(ticket_text, deps=deps)
    usage = result.usage
    usage_data = usage.model_dump() if hasattr(usage, "model_dump") else {"input_tokens": getattr(usage, "input_tokens", None), "output_tokens": getattr(usage, "output_tokens", None), "total_tokens": getattr(usage, "total_tokens", None), "model_requests": getattr(usage, "requests", None)}
    _audit("boss", "run_complete", ticket_id, {"status": result.output.status, "decision": result.output.decision, "usage": usage_data})
    decision = result.output
    decision.delegations = deps.delegations
    initial_delegations = list(deps.delegations)
    for delegation in initial_delegations:
        specialist = SPECIALISTS.get(delegation.to_role)
        if specialist is None:
            continue
        deps.current_role = delegation.to_role
        _audit(delegation.to_role, "run_start", ticket_id, {"input": delegation.task, "delegated_by": delegation.from_role})
        specialist_result = await specialist.run(delegation.task, deps=deps)
        finding = specialist_result.output
        deps.findings.append(finding)
        specialist_usage = specialist_result.usage
        usage_data = specialist_usage.model_dump() if hasattr(specialist_usage, "model_dump") else {"input_tokens": getattr(specialist_usage, "input_tokens", None), "output_tokens": getattr(specialist_usage, "output_tokens", None), "total_tokens": getattr(specialist_usage, "total_tokens", None)}
        _audit(delegation.to_role, "run_complete", ticket_id, {"finding": finding.model_dump(), "usage": usage_data})
    if deps.findings:
        deps.current_role = "boss"
        evidence = "\nSPECIALIST FINDINGS FROM MCP-BACKED RUNS:\n" + "\n".join(json.dumps(f.model_dump(), default=str) for f in deps.findings)
        _audit("boss", "synthesis_start", ticket_id, {"finding_count": len(deps.findings)})
        final_result = await boss.run(ticket_text + evidence, deps=deps)
        decision = final_result.output
        final_usage = final_result.usage
        final_usage_data = final_usage.model_dump() if hasattr(final_usage, "model_dump") else {"input_tokens": getattr(final_usage, "input_tokens", None), "output_tokens": getattr(final_usage, "output_tokens", None), "total_tokens": getattr(final_usage, "total_tokens", None)}
        _audit("boss", "synthesis_complete", ticket_id, {"status": decision.status, "decision": decision.decision, "usage": final_usage_data})
    decision.delegations = deps.delegations
    decision.findings = deps.findings
    return decision
