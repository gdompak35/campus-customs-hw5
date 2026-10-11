# Dashboard design

The dashboard is a calm operations desk rather than a dense admin console. A navy header establishes Campus Customs as a real shop, while warm coral actions, pale blue-gray surfaces, and a gold balance accent keep long sessions comfortable. The layout has three layers: the checking balance and shop identity at the top, a ticket rail on the left, and the selected ticket workspace on the right.

Each ticket is one click away in the rail and carries a clear open/resolved indicator. The workspace puts the ticket context and the primary “Start agent team” action first, followed by five color-coded agent cards. Each role has a distinct accent and a short activity label so a human can scan who is standing by, calling MCP, or has completed a step without reading a wall of text. The live activity panel provides the chronological evidence, while the ticket brief keeps the original request visible.

Resolved work uses a green status treatment; open work uses amber. The checking balance is always visible in the header and refreshes after an approved payment or purchase, making the real business consequence of approval easy to notice. The approval action is visually separate from agent activity and asks for the approval type, database reference, and human approver.

The handsome Dan/bulldog mascot from the earlier Campus Customs work returns as a friendly desk companion in the hero area. It adds warmth and continuity without competing with ticket controls. The page is responsive, uses generous spacing and rounded cards, and keeps action labels plain so a human supervisor can understand the board at a glance.

The frontend calls the FastAPI backend at `http://localhost:8000`. It refreshes tickets, cash, and audit events together so the board remains a view of the backend state rather than a second source of truth.
