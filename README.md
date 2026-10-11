# Campus Customs Multi-Agent Operations

Campus Customs is a multi-agent operations desk built for Homework 5. It includes a FastMCP server, a PydanticAI agent team, a FastAPI backend, and a React/Vite dashboard.

## Fresh run

The original database is `data/campus_customs.db`. Before a clean run, copy it over the writable working database:

```powershell
Copy-Item data/campus_customs.db data/campus_customs_new.db -Force
```

The MCP server and backend use `data/campus_customs_new.db`; the original is preserved as the reset source.

## Run the services

Install Python dependencies and start the MCP server when needed:

```powershell
py -m pip install -r requirements.txt
py -m mcp_server.server
```

In a second terminal, start the FastAPI backend:

```powershell
cd backend
py -m uvicorn main:app --reload --port 8000
```

In a third terminal, install frontend dependencies and start the React dashboard:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

The dashboard runs at `http://localhost:5173` and the backend at `http://localhost:8000`.

Human approval is required before payments or purchase actions. The agents do not email customers or contact vendors; drafts stay on the board. Keep `.env` private and use `.env.example` as the submission template.
