import os
from contextlib import AsyncExitStack

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()


class MCPClient:
    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(self):
        server_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "mcp_server",
                "server.py",
            )
        )

        server_params = StdioServerParameters(
            command="python",
            args=[server_path],
            env=os.environ.copy(),
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        self.stdio, self.write = stdio_transport

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        response = await self.session.list_tools()

        print("Connected to MCP server.")
        print("Available tools:")

        for tool in response.tools:
            print(f"  - {tool.name}")

    async def cleanup(self):
        await self.exit_stack.aclose()