import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

from qesis_endpoints import resolve

async def fetch_physical_infrastructure(landing_point: str) -> str:
    """Connects to the Subsea MCP and retrieves cable data.

    The address is resolved from data/endpoints.json, never written here. It
    used to be a literal on this line and an identical literal in test_client.py,
    with a third copy in the untracked file that carried the operator
    instruction. Three copies, one of them unread. (L-089 family.)
    """
    horizon = resolve("horizon")

    async with sse_client(horizon.url) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            
            try:
                result = await session.call_tool(
                    "fetch_cables_by_landing_point", 
                    arguments={"landing_point": landing_point}
                )
                return result.content
            except Exception as e:
                return f'{{"error": "Failed to retrieve constraints: {e}"}}'