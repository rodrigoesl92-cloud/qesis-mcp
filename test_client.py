import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

from qesis_endpoints import describe, resolve

async def test_local_subsea_connection():
    # Routing to the declared horizon endpoint. Set QESIS_HORIZON_ENDPOINT to
    # the exact URL the SSE server printed in the terminal; the declared default
    # is loopback and only resolves when that server is already running here.
    horizon = resolve("horizon")

    # G-01b: say which plane and which source answered, every time. A URL
    # printed without its provenance cannot be told apart from a stale default.
    print(f"Connecting to {describe('horizon')}...")

    # Establish the Server-Sent Events connection
    async with sse_client(horizon.url) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            print("Connection established successfully!\n")
            
            # Dynamically discover what tools the TeleGeography MCP provides
            tools_response = await session.list_tools()
            print("Available Tools in this MCP:")
            for tool in tools_response.tools:
                print(f"- {tool.name}: {tool.description}")
            
            # Call the specific tool you built
            try:
                print("\nAttempting to call tool for Berlin...")
                result = await session.call_tool(
                    "fetch_cables_by_landing_point", 
                    arguments={"landing_point": "Berlin"}
                )
                print(f"Agent retrieved data:\n{result.content}")
            except Exception as e:
                print(f"Tool call failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_local_subsea_connection())