from mcp import ClientSession
from mcp.types import CallToolResult


class Action:
    def __init__(self, session: ClientSession):
        self.session = session

    async def call_tool(self, tool_name, tool_input) -> CallToolResult | None: 
        try:
            input_data = {"input_data": tool_input}
            result = await self.session.call_tool(tool_name, input_data)
            return result
        except Exception as e:
            return {"error": str(e)}