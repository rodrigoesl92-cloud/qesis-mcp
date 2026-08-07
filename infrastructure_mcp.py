import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def fetch_physical_infrastructure(landing_point: str) -> str:
    """Connects to the local Subsea MCP and retrieves cable data."""
    local_endpoint = "http://127.0.0.1:8000/sse"
    
    async with sse_client(local_endpoint) as streams:
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