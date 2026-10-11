"""Small stdio bridge: agent tools obtain shop facts from the MCP server."""
import json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]

async def call_mcp_tool(name: str, arguments: dict) -> dict:
    server = StdioServerParameters(command="py", args=["-m", "mcp_server.server"], cwd=str(ROOT))
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            if result.isError:
                raise RuntimeError(f"MCP tool failed: {name}")
            for item in result.content:
                if hasattr(item, "text"):
                    return json.loads(item.text)
    raise RuntimeError(f"MCP tool returned no content: {name}")
