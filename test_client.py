import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def test_local_subsea_connection():
    # Routing directly to the local SSE server you started
    local_endpoint = "http://127.0.0.1:8000/sse"
    
    print(f"Connecting to {local_endpoint}...")
    
    # Establish the Server-Sent Events connection locally
    async with sse_client(local_endpoint) as streams:
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