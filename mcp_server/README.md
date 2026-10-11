# Campus Customs MCP Server

This FastMCP server provides tools for the three seeded tickets. It uses the writable working database at `data/campus_customs_new.db`; the original `data/campus_customs.db` remains unchanged as the reset source.

Tools:

- `check_customer_order_and_restock` — ticket 101: requested stock, related open invoices, and vendor restock facts.
- `check_rent_payment_status` — ticket 102: lease, shop date, cash accounts, and related payments.
- `evaluate_bulk_order_and_restock` — ticket 103: size-specific stock, pricing, open invoices, and vendor restock facts.

Agent roles call these MCP tools over stdio; they do not query SQLite directly. The working database is writable for future state-changing tools, while the current tools only read facts.

All results come from database records; the tools do not invent prices, quantities, dates, vendors, or payment status. Future state-changing tools must update only the working copy.
