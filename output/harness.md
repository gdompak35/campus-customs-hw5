# Campus Customs Data Harness

## Database handling

`data/campus_customs.db` is the preserved original seed database and must remain unchanged. All ticket-resolution updates may target the writable working copy, `data/campus_customs_new.db`.

The shop's reference date is `desk.date_today` (`2026-08-31`), which determines overdue status.

## Tables and fields

### `desk`

| Field | Why it matters for the agents |
|---|---|
| `date_today` | Establishes the shop's current date for due dates and overdue checks. |
| `notes` | Stores shop-wide operating context. |

### `tickets`

| Field | Why it matters for the agents |
|---|---|
| `id` | Identifies each work item and anchors the resolution history. |
| `type` | Helps the Boss route the ticket to the appropriate specialist. |
| `requester` | Identifies the customer, organization, landlord, or other party involved. |
| `subject` | Gives agents the short human-readable issue summary. |
| `sku` | Links product-related tickets to `inventory` and `pricing`. |
| `size` | Identifies the requested product size for inventory checks. |
| `qty` | States the requested quantity for stock and purchasing decisions. |
| `lease_id` | Links rent notices to the relevant record in `leases`. |
| `invoice_id` | Links payment-related work to the relevant record in `invoices`. |
| `status` | Shows whether the ticket remains open or has been resolved. |
| `notes` | Contains operational details needed to act on the ticket. |
| `created_at` | Provides timing and supports prioritization and auditability. |

### `inventory`

| Field | Why it matters for the agents |
|---|---|
| `sku` | Connects stock to ticket requests and pricing records. |
| `name` | Provides the product name agents can use in explanations. |
| `size` | Supports size-specific availability checks. |
| `qty` | Shows available stock and prevents agents from promising unavailable goods. |
| `location` | Tells shop staff where stock can be found. |

### `pricing`

| Field | Why it matters for the agents |
|---|---|
| `sku` | Connects costs and prices to a product. |
| `unit_cost` | Supports margin calculations and purchasing decisions. |
| `list_price` | Provides the standard customer-facing price before any approved override. |

### `vendors`

| Field | Why it matters for the agents |
|---|---|
| `id` | Identifies a vendor and links it to invoices. |
| `name` | Identifies the vendor for restock or payment planning. |
| `specialty` | Helps Inventory select a vendor capable of supplying the needed goods. |
| `lead_days` | Supports realistic restock timing. |

### `leases`

| Field | Why it matters for the agents |
|---|---|
| `id` | Links a rent ticket to the correct lease. |
| `space_name` | Identifies the shop space covered by the lease. |
| `landlord` | Identifies the party associated with the rent obligation. |
| `monthly_rent` | States the amount Facilities or Accounting may need to pay. |
| `next_due` | Supports due-date and overdue analysis. |
| `notes` | Holds lease-specific context. |

### `cash_accounts`

| Field | Why it matters for the agents |
|---|---|
| `name` | Identifies the cash account available for payments. |
| `balance` | Lets Accounting check whether a payment can be made without creating a negative balance. |
| `date` | Dates the recorded balance for cash-control decisions. |

### `payments`

| Field | Why it matters for the agents |
|---|---|
| `id` | Identifies a payment record. |
| `kind` | Describes what obligation the payment settles. |
| `ref_id` | Links the payment to the relevant invoice, lease, or other reference. |
| `amount` | States the cash leaving the account. |
| `account` | Identifies the cash account charged. |
| `paid_at` | Records when the payment occurred. |
| `approved_by` | Records the required human approval. |

### `invoices`

| Field | Why it matters for the agents |
|---|---|
| `id` | Identifies an invoice and links it to tickets or payments. |
| `vendor_id` | Connects the invoice to a vendor in `vendors`. |
| `amount` | States the amount Accounting may need to pay. |
| `due_date` | Supports overdue and payment-priority decisions. |
| `status` | Shows whether the invoice remains unpaid or has been settled. |
| `description` | Explains what was purchased and may identify the affected SKU or size. |

## MCP tools

### `check_customer_order_and_restock`

Reads `tickets`, `inventory`, `invoices`, and `vendors`. It unlocks ticket 101 by checking the requested `CC-TEE-WHITE` size S quantity and identifying the open rush-reprint invoice and vendor lead-time facts.

### `check_rent_payment_status`

Reads `tickets`, `leases`, `desk`, `cash_accounts`, and `payments`. It unlocks ticket 102 by connecting the rent notice to lease 1, comparing its due date with `desk.date_today`, and exposing cash and payment records needed before approval.

### `evaluate_bulk_order_and_restock`

Reads `tickets`, `inventory`, `pricing`, `invoices`, and `vendors`. It unlocks ticket 103 by comparing the requested 20 size-M hoodies with the recorded 8 units in stock and supplying actual cost, list price, and related vendor-restock facts for approval.

## Problem 5 agent team

| Agent | MCP tool access | Tables used |
|---|---|---|
| Boss | Routes work and calls the ticket-specific MCP tool | Ticket 101: `tickets`, `inventory`, `invoices`, `vendors`; ticket 102: `tickets`, `leases`, `desk`, `cash_accounts`, `payments`; ticket 103: `tickets`, `inventory`, `pricing`, `invoices`, `vendors` |
| Inventory | Calls ticket-specific MCP data for stock and restock facts; delegates financial or customer-message work | `tickets`, `inventory`, `invoices`, `vendors`, and `pricing` for bulk requests |
| Accounting | Calls the rent or bulk-order MCP tool and delegates stock, lease, or customer work | `tickets`, `leases`, `desk`, `cash_accounts`, `payments`, `pricing`, `invoices`, `vendors` |
| Facilities | Calls the rent MCP tool and delegates cash or stock questions | `tickets`, `leases`, `desk`, `cash_accounts`, `payments` |
| Customer Service | Calls ticket-specific MCP data before drafting a board-only customer message | `tickets`, `inventory`, `invoices`, `vendors`, `pricing`, or rent tables as applicable |

Agents receive shop facts through the MCP server over stdio. They do not create a parallel SQLite shop-tools layer. Agent run starts, MCP calls, MCP results, and run completions append to `output/audit_trail.json`; the audit file is never cleared by the team.

## Safety and token controls

Real-business guardrails should require human approval before payments, discounts, purchase orders, refunds, account changes, customer commitments, or vendor contact; prevent negative cash balances; keep credentials and private customer data out of prompts and responses; redact sensitive information; validate every state-changing request; and preserve an append-only audit trail. Customer and vendor messages should remain drafts until a human approves them.

Token use should be bounded with one ticket per run, explicit specialist routing, concise MCP results, limited delegation depth, a maximum model-request count, bounded history, and a stop condition when required facts are missing or approval is required.

## Problem 7 backend routes

- `GET /api/tickets` — returns all three tickets with their current open/resolved status and operational fields.
- `POST /api/tickets/{ticket_id}/run` — runs the agent team for one ticket and returns its typed decision, delegations, and findings.
- `POST /api/tickets/{ticket_id}/resolve` — records an explicit human-approved non-payment resolution, such as declining an unaffordable fulfillment request, and marks the ticket resolved.
- `GET /api/events?limit=100` — returns recent append-only audit events, including agent steps, MCP tools/results, and human approvals.
- `POST /api/approvals` — applies a human-approved invoice, purchase, or lease payment to the working database, updates the relevant payment/status tables, and refuses insufficient cash.
- `GET /api/cash` — returns the current `checking` row from `cash_accounts`.
- `POST /api/reset` — copies preserved `data/campus_customs.db` over writable `data/campus_customs_new.db` for a clean run.

## Problem 9 full-run results

- Reset source: `data/campus_customs.db`; working target: `data/campus_customs_new.db`.
- Starting checking balance: `$3,400`.
- Ticket 101: resolved after human-approved invoice 501 payment of `$840`.
- Ticket 102: resolved after human-approved lease 1 payment of `$2,400`.
- Ticket 103: resolved by human-approved decline of fulfillment; 8 of 20 size-M hoodies were available, and the `$264` restock exceeded the `$160` balance. No purchase or discount was made.
- Ending checking balance: `$160`, matching `cash_accounts`; cash math is `$3,400 - $840 - $2,400 = $160`.
- Evidence: `output/resolved_tickets.json`, `output/resolved_board.html`, `output/desk_tickets.html`, and append-only `output/audit_trail.json`.

## Open tickets and relationships

### Ticket 101 — customer order

Tauhid Zaman requests one `CC-TEE-WHITE` Bulldog tee in size S. The ticket links to `inventory`, where size S has quantity 0, and to invoice 501, which is an open vendor invoice for a rush reprint of that same SKU and size. The related product's price and cost would come from `pricing`.

### Ticket 102 — rent notice

Elm City Properties reports that rent is due in two days. The ticket links to lease 1 in `leases`, for the Chapel Street shop, with monthly rent of $2,400 due on 2026-09-02. The `desk.date_today` value of 2026-08-31 establishes that this is not yet overdue. Any payment would require human approval and must be checked against `cash_accounts`.

### Ticket 103 — price override

Yale AI Club requests 20 `CC-HOOD-NAVY` hoodies in size M and asks for a bulk discount. The ticket links to `inventory`, where only 8 are currently available in size M, and to `pricing`, where the list price is $58 and unit cost is $22. The Boss and Accounting should treat any discount or purchase commitment as requiring the appropriate approval; the ticket itself does not authorize an external commitment.
