import logging
import traceback

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

from action import invoke_tool
from credentials import config
from decision import build_prompt, generate_tool_descriptions
from memory import log_iteration, reset_state
from perception import generate_with_timeout, parse_response

log = logging.getLogger(__name__)
logging.basicConfig(
    filename="logs1.log",
    format='%(asctime)s - %(process)d - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO)

TELEGRAM_TOKEN = config.telegram_token
MAX_CYCLES = 25

async def process_query(user_input):
    reset_state()
    cycle_count = 0

    server_config = StdioServerParameters(command="python", args=["server.py"])
    async with stdio_client(server_config) as (reader, writer):
        async with ClientSession(reader, writer) as client_session:
            await client_session.initialize()
            available_tools = (await client_session.list_tools()).tools
            tool_descriptions = generate_tool_descriptions(available_tools)

            while cycle_count < MAX_CYCLES:
                print(f"\n--- Cycle {cycle_count + 1} ---")
                
                prompt = build_prompt(tool_descriptions, user_input)

                try:
                    response = await generate_with_timeout(prompt)
                    parsed_response = parse_response(response.text)
                except Exception as error:
                    log_iteration(f"Error in LLM response schema: {error}")
                    cycle_count += 1
                    continue
                
                log.info(f"Parsed LLM response: {parsed_response}")
                function_name = parsed_response.get("function_name")
                if function_name and function_name != "None":
                    try:
                        tool = next(t for t in available_tools if t.name == function_name)
                        arguments, result = await invoke_tool(client_session, tool, function_name, parsed_response["params"])
                        
                        iteration_result = {
                            "llm_response": parsed_response,
                            "tool": function_name,
                            "params": arguments,
                            "result": result,
                        }
                        log_iteration(iteration_result)

                        if function_name == "finish_task":
                            print(f"{result}")
                            break
                    except Exception as error:
                        traceback.print_exc()
                        log_iteration(f"Error executing {function_name}: {error}")
                        break
                else:
                    log_iteration({"Exception": parsed_response})

                cycle_count += 1

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    print(f"Received message: {user_message}")

    await process_query(user_message)

def start_bot():
    bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))

    print("Bot is now active...")
    bot_app.run_polling()

if __name__ == "__main__":
    start_bot()
