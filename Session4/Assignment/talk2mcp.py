from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
import sys

async def main():
    # Create server parameters for stdio connection
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_usecase_server.py"]
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                print("Connected to MCP server")

                # Open Paint
                print("Opening Paint...")
                result = await session.call_tool("open_paint")
                print(result.content[0].text)

                # Draw a rectangle with more appropriate dimensions
                print("Drawing rectangle...")
                result = await session.call_tool(
                    "draw_rectangle",
                    arguments={
                        "x1": 50,    # Starting from origin
                        "y1": 0,    # Starting from origin
                        "x2": 300,  # Width of rectangle
                        "y2": 200   # Height of rectangle
                    }
                )
                print(result.content[0].text)

                print(50*"+", "DONE", 50*"+")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 