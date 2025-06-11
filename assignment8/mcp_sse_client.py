import logging
import os
import traceback

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

from action import execute_tool
from decision import build_prompt, generate_tool_descriptions
from memory import clear_state, log_iteration
from perception import generate_with_timeout, validate_response

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="assignment8.log",
    format='%(asctime)s - %(process)d - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO)

load_dotenv()

MAX_ITERATIONS = 9

async def client(query):
    clear_state()
    iteration_count = 0
    SSE_PORT = os.getenv("SSE_PORT", "9135")
    async with sse_client(f"http://localhost:{SSE_PORT}/sse") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            available_tools = (await session.list_tools()).tools
            tool_description = generate_tool_descriptions(available_tools)

            while iteration_count < MAX_ITERATIONS:
                print(f"\n--- Iteration {iteration_count + 1} ---")
                
                prompt = build_prompt(tool_description, query)

                try:
                    ai_response = await generate_with_timeout(prompt)
                    logger.info(f"LLM response: {ai_response}")
                    parsed_llm_response = validate_response(ai_response.text)
                except Exception as e:
                    log_iteration(f"Issue in JSON response schema from LLM as: {e}")
                    iteration_count += 1
                    continue
                
                logger.info(f"Parsed llm response: {parsed_llm_response}")
                func_name = parsed_llm_response.get("function_name")
                if func_name and func_name != "None":
                    try:
                        tool = next(t for t in available_tools if t.name == func_name)
                        args, output = await execute_tool(session, tool, func_name, parsed_llm_response["params"])
                        
                        result = {
                            "llm_response": parsed_llm_response,
                            "tool": func_name,
                            "params": args,
                            "result": output,
                        }
                        log_iteration(result)

                        if func_name == "finish_task":
                            print(f"{output}")
                            return output
                    except Exception as e:
                        traceback.print_exc()
                        log_iteration(f"Error executing {func_name}: {e}")
                        return str(e)
                else:
                    log_iteration({"Exception": parsed_llm_response})

                iteration_count += 1

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle incoming messages from the user and respond with the processed result.
    """
    user_message = update.message.text
    print(f"Received user message: {user_message}")

    bot_response = await client(user_message)
    await update.message.reply_text(bot_response)

def start_bot():
    print("Starting bot...")
    """
    Initialize and start the Telegram bot.
    """
    TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
    bot_app = ApplicationBuilder().token(TELEGRAM_API_KEY).build()
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))

    print("TelegramBot is now active...")
    bot_app.run_polling()

if __name__ == "__main__":
    load_dotenv()
    start_bot()
