# AI Prompt Log

Sequential log of prompts entered into the vibe coder for Homework 5.

## 1. PROBLEM 2: STUDY THE CAMPUS CUSTOMS DATABASE

Read through data/campus_customs.db, and understand its tables and fields. We've already created campus_customs_new.db. Problems should update this working copy. The original file should be preserved.

Understand the three open tickets and how they link to other tables. Share this with me.

Begin output/harness.md. For each table, list the fields and one line on why that table matters for the agents.

## 2. PROBLEM 3: BUILD THE MCP SERVER

Write an MCP server in mcp_server/ using FastMCP to interact with data/campus_customs_new.db. It does not need to connect or run in this problem but it will. Every agent in this homework will use the tools in this MCP server. Write three tools that we will need for the tickets in the database. Keep the names clear, never invent any data, and only use info from the database. Suggest three to me and do not write until I provide approval.

Once they're made, update output/harness.md listing the three MCP tools, including which table it reads, which ticket it helps unlock (101, 102, or 103) and one sentence on why that tool is the right one for that ticket. Vague lines like "reads inventory" are insufficient. The sentence should demonstrate the relationship between the tool and the ticket.

Add a short mcp_server/README.md that explains what the MCP server is for, which database file it uses, and the tools it has.

Clarification: Changes can be made to `campus_customs_new.db`; the original `campus_customs.db` should remain unchanged.

## 3. PROBLEM 4: ADD THE MCP SERVER TO VIBE CODER AND TEST EACH TOOL

Please add the MCP server to this project so Codex can call the tools. Save the connection JSON text in .mcp.json at the project root or however Codex saves local MCP server lists.

Once connected, test each of the three MCP tools. Save the evidence of functionality in output/mcp_smoke.json. For each tool, include the prompt needed to implement the tool for the ticket, the tool name, and the tool output, which must match values in data/campus_customs_new.db.

Problem 4 troubleshooting: The installed package was MCP 2.x, which removed `mcp.server.fastmcp.FastMCP`. Pin the project dependency to `mcp<2` so the FastMCP server and test client use the compatible API.

## 4. PROBLEM 5: BUILD THE AGENT TEAM AND GROW THE MCP TOOLS

Build the agentic team for Campus Customs using PydanticAI: Boss, Inventory, Accounting, Facilities, and Customer Service. Create prompts, models, and agent loops for each of the agents so they can delegate work to each other with full connectivity.

Put the agent prompts in backend/prompts/, one file per agent. Put data types in backend/models.py and the agent files under backend/. Use my Portkey from the .env and only gpt-6-luna for each agent.

For the prompts, use shop rules that the agent needs. More detailed prompts that cover all aspects of the agent's work and scope score higher.

Correction to Problem 5: Any tools the agents need can be added to the MCP server so they can work on open tickets. Shop facts must come from the MCP server over `campus_customs_new.db`; do not invent a second shop-tools layer that bypasses MCP. Agents must append `output/audit_trail.json` as they run, recording enough to audit every agent-loop step without wiping prior records. Update `output/harness.md` with every agent and MCP tool, the tables each tool uses, business safety guardrails, and token-use limits. Update `mcp_server/README.md` with the current tool list.

Problem 5 troubleshooting: The installed PydanticAI version does not expose `OpenAIModel`; use its `OpenAIChatModel` API while retaining the required `gpt-6-luna` model through Portkey.

Problem 5 troubleshooting: Portkey rejected function tools because `gpt-6-luna` does not support the default reasoning effort on chat completions. Configure PydanticAI with `reasoning_effort="none"`, as required by the returned API error.

Problem 5 troubleshooting: PydanticAI v2.43.0 requires the provider-specific setting name `openai_reasoning_effort="none"` for the Portkey chat-completions request.

## 5. PROBLEM 6: PLAN THE THREE TICKETS

Build output/desk_tickets.html, a page that can be double clicked with one tab per ticket (101, 102, and 103). Also add empty cash and reflection tabs for later problems. On each ticket tab, fill an expected section anticipating what we expect the agentic team to do on each open ticket.

Create an actual section that we will fill after running the agents.

## 6. PROBLEM 7: BACKEND ROUTES

In backend/main.py, use FastAPI and add routes that return the three tickets and whether each is open or resolved; take a ticket ID and run the agent team; return recent agent events, what each agent said and which tools they used; approve a payment or purchase after a human approves; return the current checking balance; and reset the database to the original values for each fresh run. From backend/, start with uvicorn main:app --reload --port 8000. Document each route in output/harness.md.

## 7. PROBLEM 8: AGENT DASHBOARD

Build the frontend dashboard in frontend/ with React + Vite + Typescript. The page should call the routes built in Problem 7. At minimum the board should list all three tickets, let me pick one ticket and start the agent team, show each agent and what they are saying or doing while the ticket runs, mark a ticket resolved when the run finishes, show a short summary of what each agent did, let a human approve a pay or purchase when asked, and show the checking balance dropping after an approved pay. Make the dashboard pleasant, easy to interpret, and navigable. Reuse the handsome Dan popup/mascot visual from the prior Campus Customs assignment. Point the frontend to `http://localhost:8000`, allow the Vite origin on the backend, let the board start with `npm run dev`, and write `output/design.md` explaining the look and creative choices.
## 8. PROBLEM 9: RESOLVE THE TICKETS

Reset the working database `campus_customs_new.db` again so we can start fresh for a full test. Note the starting checking balance. Then we'll run all three tickets on the board until each is resolved. Open `output/desk_tickets.html` from Problem 6. On each ticket tab, fill the Actual section from this run: which agents work, what they delegated, and which tools they used. Keep the expected section as is to compare.

On the cash tab of the same HTML, itemize the money: starting checking balance after the reset; for each ticket how cash changed when that ticket resolved, and why (which payment or purchase, dollar amount); and ending checking balance, which must match `cash_accounts` in the working database.

Wrong cash math loses points even if the board shows the tickets are resolved.

Also save `output/resolved_tickets.json` for each ticket ID, including its ID, final status, short outcome, what each agent contributed, and any human approvals. Save `output/resolved_board.html`, append real runs to `output/audit_trail.json`, and finish `output/harness.md` so it includes tables, MCP tools, the five agents, API routes, the dashboard, and safety rules.
