import asyncio
import json
import os

from dotenv import load_dotenv
from groq import Groq

from mcp_client import MCPClient


load_dotenv(
    os.path.join(
        os.path.dirname(__file__),
        ".env",
    )
)

MODEL = "openai/gpt-oss-120b"


SYSTEM_INSTRUCTION = """
You are an AI assistant for an inventory management system.

You have access to inventory tools through an MCP server.

Rules:
1. Never invent inventory information.
2. Use the available tools whenever the user asks about
   actual inventory, products, locations, stock, expiry,
   consumption, or movement.
3. Explain inventory information clearly and concisely.
4. For inventory-changing operations, carefully use the
   appropriate tool and its arguments.
5. After receiving a tool result, interpret the result and
   provide a natural-language response to the user.
6. NEVER substitute one inventory-changing operation for
   another. For example, if a move_item operation fails,
   do NOT use consume_item and add_inventory as a substitute.
7. If an inventory-changing tool returns an error or fails
   to execute, stop the operation and clearly tell the user
   that the requested operation was not completed.
8. NEVER claim that an inventory-changing operation succeeded
   unless the appropriate tool returned a successful result.
9. If a tool call fails, do not repeatedly retry the same
   operation unless there is a clear reason that retrying
   could resolve the problem.
"""


async def ask_inventory_ai(
    user_input: str,
    mcp_client: MCPClient,
    groq: Groq,
    tools: list,
) -> str:

    messages = [
        {
            "role": "system",
            "content": SYSTEM_INSTRUCTION,
        },
        {
            "role": "user",
            "content": user_input,
        },
    ]

    while True:
        response = groq.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        message = response.choices[0].message

        # The model wants to call one or more MCP tools
        if message.tool_calls:

            messages.append(message)

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name

                try:
                    arguments = json.loads(
                        tool_call.function.arguments
                    )
                except json.JSONDecodeError:
                    arguments = {}

                tool_result = await mcp_client.session.call_tool(
                    tool_name,
                    arguments=arguments,
                )

                # Extract text returned by MCP
                result_text = ""

                for item in tool_result.content:
                    if hasattr(item, "text"):
                        result_text += item.text

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text,
                    }
                )

            continue

        # No more tools required → final answer
        return message.content or ""


async def create_ai_client():
    mcp_client = MCPClient()

    await mcp_client.connect_to_server()

    groq = Groq(
        api_key=os.environ["GROQ_API_KEY"]
    )

    # Discover MCP tools
    mcp_response = await mcp_client.session.list_tools()

    tools = []

    for tool in mcp_response.tools:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                },
            }
        )

    return mcp_client, groq, tools


async def main():
    mcp_client = None

    try:
        mcp_client, groq, tools = await create_ai_client()

        print("\n===================================")
        print("       Inventory AI Assistant")
        print("===================================")
        print("Type 'exit' to quit.\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() == "exit":
                break

            if not user_input:
                continue

            answer = await ask_inventory_ai(
                user_input,
                mcp_client,
                groq,
                tools,
            )

            print(f"\nAI: {answer}\n")

    finally:
        if mcp_client:
            await mcp_client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())