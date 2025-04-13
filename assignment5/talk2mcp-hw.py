import asyncio
import json
import logging
import os
import random
from concurrent.futures import TimeoutError
from typing import Dict, List, Optional

from dotenv import load_dotenv
from google import genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    filename="assignment5_iter3.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class Property(BaseModel):
    type: str
    description: Optional[str]
    items: Optional[Dict[str, str]] = None  # For array types, e.g., {"type": "integer"}
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


# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

max_iterations = 9
last_response = None
iteration = 0
iteration_response = []


async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
    logging.info("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash", contents=prompt
                ),
            ),
            timeout=timeout,
        )
        logging.info("LLM generation completed")
        return response
    except TimeoutError:
        logging.info("LLM generation timed out!")
        raise
    except Exception as e:
        logging.info(f"Error in LLM generation: {e}")
        raise


def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []


async def main():
    reset_state()  # Reset at the start of main
    logging.info("Starting main execution...")
    try:
        logging.info("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python", args=["mcp_server_pydantic.py"]
        )

        async with stdio_client(server_params) as (read, write):
            logging.info("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                logging.info("Session created, initializing...")
                await session.initialize()

                # Get available tools
                logging.info("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                logging.info(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt with available tools
                logging.info("Creating system prompt...")
                logging.info(f"Number of tools: {len(tools)}")

                # tools_description = generate_tool_descriptions_old(tools)
                tools_description = generate_tool_descriptions(tools)

                logging.info("Created system prompt...")
                logging.info(tools_description)
                system_prompt = generate_system_prompt(tools_description)

                logging.info(f"System prompt: {system_prompt}")
                print(f"System prompt: {system_prompt}")

                logging.info("\nStarting iteration loop...")

                query = generate_user_prompt()

                # Use global iteration variables
                global iteration, last_response

                while iteration < max_iterations:
                    logging.info(f"\n--- Iteration {iteration + 1} ---")
                    if last_response is None:
                        current_query = query
                    else:
                        current_query = (
                            current_query + "\n\n" + " ".join(iteration_response)
                        )
                        current_query = current_query + "  What should I do next?"

                    # Get model's response with timeout
                    logging.info("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    try:
                        response = await generate_with_timeout(client, prompt)
                        response_text = response.text.strip()
                        logging.info(f"LLM Response: {response_text}")

                        # Find the FUNCTION_CALL line in the response
                        for line in response_text.split("\n"):
                            line = line.strip()
                            if line.startswith("FUNCTION_CALL:"):
                                response_text = line
                                break

                    except Exception as e:
                        logging.info(f"Failed to get LLM response: {e}")
                        break

                    if response_text.startswith("FUNCTION_CALL:"):
                        _, function_info = response_text.split(":", 1)
                        try:
                            function_call = json.loads(
                                function_info.strip()
                            )  # Parse JSON structure
                            func_name = function_call["tool_name"]
                            params = function_call["tool_input"]

                            logging.debug(f"Function name: {func_name}")
                            logging.debug(f"Parameters: {params}")

                            # Find the matching tool to get its input schema
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                logging.debug(
                                    f"Available tools: {[t.name for t in tools]}"
                                )
                                raise ValueError(f"Unknown tool: {func_name}")

                            logging.debug(f"Found tool: {tool.name}")
                            logging.debug(f"Tool schema: {tool.inputSchema}")

                            logging.debug(f"Final arguments: {params}")
                            logging.debug(f"Calling tool {func_name}")
                            result = {}
                            input_data = {"input_data": params}

                            try:
                                result = await session.call_tool(
                                    # func_name, arguments=arguments
                                    func_name, input_data
                                )
                                logging.debug(f"Raw result: {result}")
                            except Exception as e:
                                print(e)


                            # Get the full result content
                            if hasattr(result, "content"):
                                logging.debug("Result has content attribute")
                                # Handle multiple content items
                                if isinstance(result.content, list):
                                    iteration_result = [
                                        item.text
                                        if hasattr(item, "text")
                                        else str(item)
                                        for item in result.content
                                    ]
                                elif hasattr(result.content, "text"):
                                    iteration_result = result.content.text
                                else:
                                    iteration_result = str(result.content)
                            else:
                                logging.info("DEBUG: Result has no content attribute")
                                iteration_result = str(result)

                            logging.info(
                                f"DEBUG: Final iteration result: {iteration_result}"
                            )

                            # Format the response based on result type
                            if isinstance(iteration_result, list):
                                result_str = (
                                    f"[{', '.join(map(str, iteration_result))}]"
                                )
                            elif isinstance(iteration_result, str):
                                result_str = iteration_result
                            else:
                                result_str = str(iteration_result)

                            iteration_response.append(
                                f"In the {iteration + 1} iteration you called {func_name} with {params} parameters, "
                                f"and the function returned {result_str}."
                            )
                            last_response = iteration_result
                        except json.JSONDecodeError as json_e:
                            logging.error(
                                f"DEBUG: Failed to parse function call JSON: {function_info.strip()}. Error: {json_e}"
                            )
                            iteration_response.append(
                                f"Error in iteration {iteration + 1}: Invalid function call format. {str(json_e)}"
                            )
                            break
                        except ValueError as ve:
                            logging.error(
                                f"DEBUG: Value error during function call processing: {str(ve)}"
                            )
                            iteration_response.append(
                                f"Error in iteration {iteration + 1}: {str(ve)}"
                            )
                            break
                        except Exception as e:
                            logging.info(f"DEBUG: Error details: {str(e)}")
                            logging.info(f"DEBUG: Error type: {type(e)}")
                            import traceback

                            traceback.print_exc()
                            iteration_response.append(
                                f"Error in iteration {iteration + 1}: {str(e)}"
                            )
                            break

                    elif response_text.startswith("FINAL_ANSWER:"):
                        logging.info("\n=== Agent Execution Complete ===")
                        iteration_response.append(
                            f"Final answer received: {response_text}"
                        )
                        break

                    iteration += 1

    except Exception as e:
        logging.info(f"Error in main execution: {e}")
        import traceback

        traceback.print_exc()
    finally:
        reset_state()

def generate_user_prompt():
    query= """
                You are an AI agent that performs tasks step-by-step using external tools. Follow each instruction in order, using exactly one tool function call per response, and track your reasoning process internally.
Task Instructions:
Please perform the following steps in sequence:
[Reasoning Type: Lookup] Find first 10 fibonacci_numbers using the appropriate tool.
[Reasoning Type: Arithmetic] Use the list from step 1 to compute the cubes of the first 10 fibonacci numbers.
[Reasoning Type: Arithmetic] Compute the sum of the cubes from step 2.
[Reasoning Type: Tool-Use] Open Microsoft Paint.
[Reasoning Type: Tool-Use] Draw a rectangle using coordinates (200, 200) to (500, 400).
[Reasoning Type: Communication] Add the text Final Answer :-: [sum] to the Paint canvas using the result from step 3.
[Reasoning Type: Communication] Send an email to bhole.atul@gmail.com with an appropriate subject, and include the sum from step 3 in the message body along with all the steps taken.
Output Format Rules:
You MUST respond with exactly one line that begins with either:
FUNCTION_CALL: or FINAL_ANSWER:
For tool usage, format the function call like this:
FUNCTION_CALL: {{"tool_name": "function_name", "tool_input":{{ "<parameter_name>": "<parameter_value>", ... }}}}
The final step must return the completed answer like this:
FINAL_ANSWER: [computed_sum]
Reasoning Instructions:
Think step-by-step before calling a function.
Briefly verify the logic of each output before proceeding.
Internally tag each step with the type of reasoning used (e.g., arithmetic, lookup, planning, validation).
If a tool call fails (e.g., returns an empty or null value), retry once if reasonable.
If retry fails, skip that step and continue.
Store intermediate results as variables and reuse them as needed.
Do not guess or hallucinate any values—only use verified tool outputs.
Do not miss any instruction.
Always aim to complete the task as fully as possible using available tools, even with partial results.
Example Output:
FUNCTION_CALL: {{ "tool_name": "find_first_fibonacci_numbers", "tool_input":{{ "n" : 4 }} }}
FUNCTION_CALL: {{ "tool_name": "calculate_cubes", "tool_input":{{ "numbers" : [0 ,1 ,1 ,2] }} }}
After receiving the response, move to the next logical step.
                """
    
    return query


def generate_system_prompt(tools_description):
    system_prompt = f"""You are an AI agent that solves tasks iteratively using tools. You must reason step-by-step, store intermediate results as needed, and issue one tool command at a time using the strict formats below. You should **verify intermediate results**, handle tool errors, and internally track the **type of reasoning** being used (e.g., arithmetic, lookup, planning).
---
✅ Available Tools:
{tools_description}
---
✅ Output Rules:

- You MUST respond with **exactly one line** starting with either `FUNCTION_CALL:` or `FINAL_ANSWER:`.
- Use this format for function calls:  
  `FUNCTION_CALL: {{"tool_name": "function_name", "tool_input":{{ "<parameter_name>": "<parameter_value>", ... }}}}`
- Use this format for final output:  
  `FINAL_ANSWER: [number]`
- Do NOT repeat function calls with the same parameters.
- If a function result is reused later, store it in a variable internally (e.g., result1 = [values]).
- Internally track the **reasoning type** for each step: [lookup, arithmetic, planning, tool-use, validation, communication].

---

✅ Error Handling:

- If a tool returns an unexpected result (e.g., empty list, null), retry once if logical.
- If retry fails or is not applicable, skip the step and continue.
- Use placeholder messages (e.g., "Unable to compute") in later steps if data is missing.
- Always aim to complete the task using available tools, even with partial success.

---

✅ Reasoning Instructions:

- Think before you act. Always verify intermediate steps logically.
- Separate reasoning from tool use: reason internally, then call a tool.
- Always process and store tool outputs for future use.
- Do not guess values—rely on tool outputs.
- Make sure final answers are based on verified data.

---

✅ Example Function calls:

- FUNCTION_CALL: {{ "tool_name": "strings_to_chars_to_int", "tool_input":{{ "string": "BHARAT" }} }}
- FUNCTION_CALL: {{ "tool_name": "int_list_to_exponential_sum", "tool_input":{{ "int_list": [73, 78, 68, 73, 65] }} }}
- FUNCTION_CALL: {{ "tool_name": "find_first_fibonacci_numbers", "tool_input":{{ "n" : 4 }} }}
- FUNCTION_CALL: {{ "tool_name": "calculate_cubes", "tool_input":{{ "numbers" : [0 ,1 ,1 ,2] }} }}
- FUNCTION_CALL: {{ "tool_name": "calculate_sum", "tool_input":{{ "numbers": [0,1,1,8] }} }}
- FUNCTION_CALL: {{ "tool_name": "open_paint", "tool_input":{{}} }}
- FUNCTION_CALL: {{ "tool_name": "draw_rectangle", "tool_input":{{ "x1": 200, "y1": 200, "x2": 400, "y2": 400 }} }}
- FUNCTION_CALL: {{ "tool_name": "add_text_in_paint", "tool_input":{{ "text": "24440777.89" }} }}
- FUNCTION_CALL: {{ "tool_name": "send_email", "tool_input":{{ "to_email": "bhole.atul@gmail.com", "subject": "some_valid_subject", "body": "24440777.89" }} }}

---

✅ Example Session:

FUNCTION_CALL: {{ "tool_name": "find_first_fibonacci_numbers", "tool_input":{{ "n" : 4 }} }}
[waits for tool response: [0 ,1 ,1 ,2 ]]  
FUNCTION_CALL: {{ "tool_name": "calculate_cubes", "tool_input":{{ "numbers" : [0 ,1 ,1 ,2 ] }} }}
[waits for tool response: [0,1,1,8]]
FUNCTION_CALL: {{ "tool_name": "calculate_sum", "tool_input":{{ "numbers" : [0,1,1,8] }} }}
[waits for tool response: [10]]
FUNCTION_CALL: {{ "tool_name": "open_paint", "tool_input":{{}} }}
FUNCTION_CALL: {{ "tool_name": "draw_rectangle", "tool_input":{{ "x1": 200, "y1": 200, "x2": 400, "y2": 400 }} }}
FUNCTION_CALL: {{ "tool_name": "add_text_in_paint", "tool_input":{{ "text": "text-in-the-paint" }} }}
FUNCTION_CALL: {{ "tool_name": "send_email", "tool_input":{{ "to_email": "bhole.atul@gmail.com", "subject": "some_valid_subject", "body": "10" }} }}
FINAL_ANSWER: 245398.23

"""

    # print(f" system prompt \n{system_prompt}")

    return system_prompt


def generate_tool_descriptions(tools):
    try:
        new_tools_description = []

        for i, tool in enumerate(tools):
            try:
                # Get tool properties
                params = tool.inputSchema
                desc = getattr(tool, "description", "No description available")
                name = getattr(tool, "name", f"tool_{i}")
                logging.info(f"-----------\n\nProcessing tool --> {i}: {name} : {desc}")
                # print(f"params : {tool}")
                schema = str(params).replace("'", '"')
                # print(f"schema :: {schema}")
                schema_properties = extract_schema(schema)
                # print(f"schema_properties :: {schema_properties}")

                # logging.debug(f"Extracted schema properties: {schema_properties}")

                parameters = Parameters(
                    properties=schema_properties["properties"],
                    type=schema_properties["type"],
                    required=schema_properties["required"],
                )
                # logging.debug(f"--------Parameters: {parameters}")
                function = Function(name=name, description=desc, parameters=parameters)
                pydantic_tool = Tool(type="function", function=function)
                logging.info(f"TOOL_DESCRIPTION:\n{pydantic_tool.model_dump_json(
                        indent=4,
                        exclude_none=True,
                        exclude={"function": {"parameters": {"properties": {"title"}}}},
                    )}")
                # tools.append(tool)
                new_tools_description.append(
                    pydantic_tool.model_dump_json(
                        exclude_none=True,
                        exclude={"function": {"parameters": {"properties": {"title"}}}},
                    )
                )
                # print(
                #     f"New tool description: {tool.model_dump_json(indent=4, exclude_none=True, exclude={'function': {'parameters': {'properties': {'title'}}}})}"
                # )

            except Exception as e:
                print(f"Error processing tool {i}: {e}")
                logging.error(f"Error processing tool {i}: {e}")
                new_tools_description.append(
                    json.dumps({"error": f"Failed to process tool {i}: {str(e)}"})
                )

        print(f"Successfully created tools description: {new_tools_description}")
        return new_tools_description
    except Exception as e:
        print(f"Error creating tools description: {e}")
        return []


def generate_tool_descriptions_old(tools):
    try:
        tools_description = []
        for i, tool in enumerate(tools):
            try:
                # Get tool properties
                params = tool.inputSchema
                desc = getattr(tool, "description", "No description available")
                name = getattr(tool, "name", f"tool_{i}")

                # Format the input schema in a more readable way
                if "properties" in params:
                    param_details = []
                    for param_name, param_info in params["properties"].items():
                        param_type = param_info.get("type", "unknown")
                        param_details.append(f"{param_name}: {param_type}")
                    params_str = ", ".join(param_details)
                else:
                    params_str = "no parameters"

                tool_desc = f"{i + 1}. {name}({params_str}) - {desc}"
                tools_description.append(tool_desc)
                logging.info(f"Added description for tool: {tool_desc}")
            except Exception as e:
                logging.info(f"Error processing tool {i}: {e}")
                tools_description.append(f"{i + 1}. Error processing tool")

        tools_description = "\n".join(tools_description)
        logging.info("Successfully created tools description")
    except Exception as e:
        logging.info(f"Error creating tools description: {e}")
        tools_description = "Error loading tools"
    return tools_description  # Reset at the end of main


def extract_schema(schema):
    schema = json.loads(schema)
    defs = schema.get("$defs", {})
    properties = {}
    for key, value in defs.items():
        # Check if the value is a dictionary and contains 'properties'
        # print(f"Extracting properties for key: {key} and value: {value}")
        if isinstance(value, dict) and "properties" in value:
            # Extract the properties from the schema
            properties["properties"] = value["properties"]
            properties["type"] = value.get("type", "object")
            properties["required"] = value.get("required", [])
            return properties
        # elif isinstance(value, dict):
        #     # If it's a nested schema, recursively extract properties
        #     properties[key] = extract_properties(value)
    return {"properties": {}, "type": "object", "required": []}


def generate_argument(schema, tool_input):
    """
    Generate sample data based on the given schema properties and tool_input.
    """
    sample_data = {}
    for key, value in schema.get("properties", {}).items():
        if key in tool_input:
            # Use the value from tool_input if it exists
            sample_data[key] = tool_input[key]
        else:
            # Generate sample data based on the type
            data_type = value.get("type")
            if data_type == "string":
                sample_data[key] = "Sample Text"
            elif data_type == "integer":
                sample_data[key] = random.randint(1, 1000)
            elif data_type == "array":
                item_type = value.get("items", {}).get("type")
                if item_type == "integer":
                    sample_data[key] = [random.randint(1, 100) for _ in range(5)]
                elif item_type == "string":
                    sample_data[key] = ["Sample1", "Sample2", "Sample3"]
            elif data_type == "boolean":
                sample_data[key] = random.choice([True, False])
            elif data_type == "number":
                sample_data[key] = random.uniform(1.0, 100.0)
            else:
                sample_data[key] = None  # Default for unsupported types
    return sample_data


def generate_json_from_schema(input_schema, tool_input):
    """
    Generate JSON data based on the input schemas and tool_input.
    """
    return generate_argument(input_schema, tool_input)


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
