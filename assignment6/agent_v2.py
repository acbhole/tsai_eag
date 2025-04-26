import asyncio
import json
import logging
import os
from typing import Dict, List, Optional

from action import Action
from decision_making import DecisionMaking
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from memory import Memory
from perception import Perception
from prompt_loader import load_prompt
from pydantic import BaseModel
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.prompt import Prompt
from utils import clean_json_response

logging.basicConfig(
    filename="agent.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

console = Console(soft_wrap=True)
logger = logging.getLogger(__name__)


class Property(BaseModel):
    type: str
    description: Optional[str]
    items: Optional[Dict[str, str]] = None
    title: Optional[str]


class Parameters(BaseModel):
    type: str
    properties: Dict[str, Property]
    required: List[str]


class Function(BaseModel):
    name: str
    description: str
    parameters: Parameters


class Tool(BaseModel):
    type: str
    function: Function

def generate_tool_descriptions(tools):
    new_tools_description = []
    for tool in tools:
        params = tool.inputSchema
        desc = getattr(tool, "description", "No description available")
        name = getattr(tool, "name", "unknown_tool")
        # schema = str(params).replace("'", '"')
        schema = json.dumps(
            params.model_dump() if hasattr(params, "model_dump") else params
        )
        schema_properties = extract_schema(schema)
        parameters = Parameters(
            properties=schema_properties["properties"],
            type=schema_properties["type"],
            required=schema_properties["required"],
        )
        function = Function(name=name, description=desc, parameters=parameters)
        pydantic_tool = Tool(type="function", function=function)
        new_tools_description.append(
            pydantic_tool.model_dump_json(
                exclude_none=True,
                exclude={"function": {"parameters": {"properties": {"title"}}}},
            )
        )
    return new_tools_description


def extract_schema(schema):
    schema = json.loads(schema)
    defs = schema.get("$defs", {})
    for key, value in defs.items():
        if isinstance(value, dict) and "properties" in value:
            return {
                "properties": value["properties"],
                "type": value.get("type", "object"),
                "required": value.get("required", []),
            }
    return {"properties": {}, "type": "object", "required": []}


def parse_tool_input_values(tool_input):
    """
    Parse tool input values, converting stringified representations into their appropriate Python types.

    Args:
        tool_input (dict): A dictionary containing key-value pairs where values may be strings
                          representing various types or already in their native Python form.

    Returns:
        dict: A dictionary with parsed values, where string representations are converted to
              their corresponding Python types (int, float, list, dict, bool) when possible.

    Supported Types:
        - Strings: Kept as strings if not representing another type.
        - Integers: e.g., "42" -> 42
        - Floats: e.g., "3.14" -> 3.14
        - Lists: e.g., "[1, 2, 3]" -> [1, 2, 3]
        - Dictionaries: e.g., "{\"key\": \"value\"}" -> {"key": "value"}
        - Booleans: e.g., "true" -> True, "false" -> False

    Behavior:
        - If a value is a string and can be parsed as JSON, it is converted to the appropriate type.
        - If a value is a string but cannot be parsed (e.g., malformed JSON), it remains a string.
        - If a value is not a string, it is returned unchanged.
    """
    parsed_input = {}
    for key, value in tool_input.items():
        if isinstance(value, str):
            try:
                # Attempt to parse the string as JSON
                parsed_value = json.loads(value)
                parsed_input[key] = parsed_value
            except json.JSONDecodeError:
                # If parsing fails, keep the original string value
                parsed_input[key] = value
        else:
            # If not a string, use the value as-is
            parsed_input[key] = value
    return parsed_input


async def main():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    # Ask the user for their preference
    # preferences = input("Please enter your preference for responses: ")
    # preferences = console.input("Please enter your preference for responses:")

    preferences = Prompt.ask("Please enter your preference for responses:")
    server_params = StdioServerParameters(
        command="python", args=["mcp_server_pydantic.py"]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Initialize cognitive layers
            perception = Perception(api_key)
            memory = Memory()
            memory.preferences = preferences  # Store preference in memory
            decision_making = DecisionMaking()
            action = Action(session)

            # Prepare tools and prompt
            tools_result = await session.list_tools()
            tools_description = generate_tool_descriptions(tools_result.tools)
            logger.info("Tools Description:")
            logger.info(tools_description)

            system_prompt = load_prompt(
                "system_prompt.txt",
                preferences=memory.preferences,
                tools_description=tools_description,
            )
            query = load_prompt("user_prompt.txt")

            logger.info("System Prompt:")
            logger.info(system_prompt)

            logger.info("User Prompt:")
            logger.info(query)

            while memory.iteration < memory.max_iterations:
                # print(f"\n--- Iteration {memory.iteration + 1} ---")
                console.rule(f"[bold blue]Iteration {memory.iteration + 1}")
                logger.info(f"\n--- Iteration {memory.iteration + 1} ---")

                current_query = (
                    query + "\n\n" + memory.get_history() + " What should I do next?"
                )
                # current_query = (query + "\n\n" + memory.get_history() + " What should I do next?")
                prompt = f"{system_prompt}\n\nQuery: {current_query}"

                # Perception: Get LLM response
                llm_response = await perception.get_llm_response(prompt)
                # print(f"LLM Response: {llm_response}")
                # print(f"LLM Reasoning :{llm_response.get('reasoning', 'No reasoning provided')}")
                # print(f"LLM Action: {llm_response.get('action', 'No action provided')}")
                # console.print(f"[bold green]LLM Reasoning:[/bold green] {llm_response.get('reasoning', 'No reasoning provided')}")
                # console.print(f"[bold yellow]LLM Action:[/bold yellow] {llm_response.get('action', 'No action provided')}")
                logger.debug(f"LLM Response: {llm_response}")

                # Prepare split screen panels
                reasoning_panel = Panel(
                    f"[italic]{llm_response.get('reasoning', 'No reasoning provided')}[/italic]",
                    title="[bold green][italic]LLM Reasoning[/italic][/bold green]",
                    border_style="green",
                )
                # action_panel = Panel(
                #     str(llm_response.get('action', 'No action provided')),
                #     title="[bold yellow]LLM Action[/bold yellow]",
                #     border_style="yellow"
                # )
                console.print(reasoning_panel)

                action_panel = Panel(
                    JSON.from_data(
                        clean_json_response(
                            llm_response.get("action", "No action provided")
                        ),
                        indent=2,
                    ),
                    title="[bold yellow]LLM Action[/bold yellow]",
                    border_style="yellow",
                )

                console.print(action_panel)
                # clean_action_response = clean_json_response(llm_response.get('action'))
                # print(f"Cleaned Action Response: {clean_action_response}")
                # console.print(clean_action_response)
                # console.print(Columns([reasoning_panel, action_panel]))  # Re-enable printing of the columns
                # Decision-Making: Interpret response
                next_action = decision_making.decide_next_action(llm_response)

                if next_action["type"] == "tool_call":
                    # Action: Execute tool call
                    tool_name = next_action["tool_name"]
                    raw_tool_input = next_action["tool_input"]

                    parsed_tool_input = parse_tool_input_values(raw_tool_input)

                    result = await action.call_tool(tool_name, parsed_tool_input)

                    logger.debug(f"Tool Result: {result}")
                    content_result = result.content[0].text

                    clean_json_response_result = clean_json_response(content_result)

                    output_panel = Panel(
                        JSON.from_data(clean_json_response_result),
                        # content_result,
                        title="[bright_magenta]LLM Tool Output[/bright_magenta]",
                        border_style="magenta",
                        expand=True,
                        padding=(1, 2),
                    )
                    console.print(output_panel)
                    # Format and store result
                    # result_str = str(
                    #     result.get("content", result)
                    #     if isinstance(result, dict)
                    #     else result
                    # )
                    # response_text = f"In iteration {memory.iteration + 1}, called {tool_name} with {parsed_tool_input}, got {content_result}"
                    memory.add_response(
                        memory.iteration + 1,
                        tool_name,
                        parsed_tool_input,
                        content_result,
                    )
                    # memory.add_response(response_text)
                    # logger.debug(response_text)

                    # add function to get last added response from memory

                    last_response = memory.get_last_response()

                    # print(f"Last added response: {last_response}")

                elif next_action["type"] == "final_answer":
                    # print(f"Final Answer: {next_action['answer']}")
                    final_answer = next_action["answer"]
                    final_answer_panel = Panel(
                        JSON.from_data(clean_json_response(final_answer)),
                        # content_result,
                        title="[bright_red]Final Answer[/bright_red]",
                        border_style="red",
                    )
                    console.print(final_answer_panel)

                    logger.info(f"Final Answer: {next_action['answer']}")
                    logger.debug(f"Final Answer logged: {next_action['answer']}")
                    break

                elif next_action["type"] == "error" or next_action["type"] == "unknown":
                    print(f"Error: {next_action.get('message', 'Unknown error')}")
                    logger.error(
                        f"Error: {next_action.get('message', 'Unknown error')}"
                    )
                    break
                # console.print(Columns([reasoning_panel, action_panel, output_panel]))
                memory.update_iteration()

            if memory.iteration >= memory.max_iterations:
                print("Maximum iterations reached")


if __name__ == "__main__":
    asyncio.run(main())
