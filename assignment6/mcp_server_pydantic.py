import logging
import math
import os
import smtplib
import subprocess
import sys
import time
from email.mime.text import MIMEText

import psutil
import pyautogui
import requests
from dotenv import find_dotenv, load_dotenv
from mcp.server.fastmcp import FastMCP
from models import (  # Import all Pydantic models from models.py
    ASCIIInput,
    ASCIIOutput,
    CubeInput,
    CubeOutput,
    EmailInput,
    ExponentialInput,
    ExponentialOutput,
    FibonacciInput,
    FibonacciOutput,
    PaintOutput,
    RectangleInput,
    SquareInput,
    SquareOutput,
    SumInput,
    SumOutput,
    TelegramInput,
    TextInput,
)
from pydantic import ValidationError
from pywinauto.application import Application

# instantiate an MCP server client
mcp = FastMCP("Grok_pydantic")
logging.basicConfig(
    filename="mcp_server.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


@mcp.tool()
def strings_to_chars_to_int(input_data: ASCIIInput) -> ASCIIOutput:
    """Return the ASCII values of the characters in a word."""
    # ascii_values = [ord(char) for char in input_data.string]
    # return ASCIIOutput(ascii_values=ascii_values)
    try:
        # Validate and parse the input data
        if not isinstance(input_data, ASCIIInput):
            input_data = ASCIIInput(**input_data)

        # Process the input
        ascii_values = [ord(char) for char in input_data.string]
        return ASCIIOutput(ascii_values=ascii_values)
    except ValidationError as e:
        # Handle validation errors
        raise ValueError(f"Validation error for strings_to_chars_to_int: {e}")


@mcp.tool()
def int_list_to_exponential_sum(input_data: ExponentialInput) -> ExponentialOutput:
    """Return sum of exponentials of numbers in a list."""
    sum_exponentials = sum(math.exp(i) for i in input_data.int_list)
    return ExponentialOutput(sum_exponentials=sum_exponentials)


@mcp.tool()
async def open_paint() -> PaintOutput:
    """Opens Microsoft Paint, maximizes it, and resets the canvas."""
    try:
        if not is_paint_open():
            subprocess.Popen("mspaint.exe")
            time.sleep(2)  # Wait for Paint to open
        else:
            # Bring Paint to focus
            for proc in psutil.process_iter(attrs=["pid", "name"]):
                if proc.info["name"] and "mspaint" in proc.info["name"].lower():
                    app = Application().connect(process=proc.info["pid"])
                    app.top_window().set_focus()
                    break

        # Reset the canvas
        pyautogui.hotkey("ctrl", "n")  # New canvas
        time.sleep(0.5)
        pyautogui.press("enter")  # Confirm new canvas
        pyautogui.hotkey("win", "up")  # Maximize the window
        time.sleep(0.2)

        return PaintOutput(
            message="Microsoft Paint has been successfully launched, brought to focus, and the canvas has been reset."
        )
    except Exception as e:
        return PaintOutput(
            message=f"An error occurred while attempting to open Microsoft Paint: {str(e)}."
        )


@mcp.tool()
async def draw_rectangle(input_data: RectangleInput) -> PaintOutput:
    """Draws a rectangle in Microsoft Paint from (x1, y1) to (x2, y2)."""
    try:
        if not is_paint_open():
            await open_paint()
            time.sleep(0.5)  # Wait for Paint to be ready
        else:
            # Bring Paint to focus
            for proc in psutil.process_iter(attrs=["pid", "name"]):
                if proc.info["name"] and "mspaint" in proc.info["name"].lower():
                    app = Application().connect(process=proc.info["pid"])
                    app.top_window().set_focus()
                    break

        pyautogui.click(
            440, 93
        )  # Click the rectangle tool (adjust coordinates as needed)
        time.sleep(0.5)
        pyautogui.moveTo(input_data.x1, input_data.y1)
        pyautogui.mouseDown(button="left")
        pyautogui.moveTo(input_data.x2, input_data.y2, duration=0.5)
        pyautogui.mouseUp(button="left")

        return PaintOutput(
            message=f"A rectangle has been successfully drawn from ({input_data.x1}, {input_data.y1}) to ({input_data.x2}, {input_data.y2})."
        )
    except Exception as e:
        return PaintOutput(
            message=f"An error occurred while attempting to draw the rectangle: {str(e)}."
        )


@mcp.tool()
async def add_text_in_paint(input_data: TextInput) -> PaintOutput:
    """Adds the specified text to the canvas in Microsoft Paint."""
    try:
        if not is_paint_open():
            await open_paint()
            time.sleep(0.5)
        else:
            # Bring Paint to focus
            for proc in psutil.process_iter(attrs=["pid", "name"]):
                if proc.info["name"] and "mspaint" in proc.info["name"].lower():
                    app = Application().connect(process=proc.info["pid"])
                    app.top_window().set_focus()
                    break

        pyautogui.click(291, 101)  # Click the text tool (adjust coordinates as needed)
        time.sleep(0.5)
        pyautogui.click(250, 250)  # Click where to type text
        pyautogui.write(input_data.text, interval=0.1)
        pyautogui.click(600, 500)  # Click outside to confirm

        return PaintOutput(
            message=f"The text '{input_data.text}' has been successfully added to the canvas."
        )
    except Exception as e:
        return PaintOutput(
            message=f"An error occurred while attempting to add text: {str(e)}."
        )


def is_paint_open() -> bool:
    """Check if Microsoft Paint is running."""
    for proc in psutil.process_iter(attrs=["name"]):
        if proc.info["name"] and "mspaint" in proc.info["name"].lower():
            return True
    return False

@mcp.tool()
async def send_email(input_data: EmailInput) -> PaintOutput:
    """Send an email via Gmail's SMTP server."""
    try:
        # Validate input JSON
        # validate_function_input_output("send_email", input_json)
        logging.info(f"input_json: {input_data}")
        if not isinstance(input_data, EmailInput):
            input_data = EmailInput(**input_data)

        gmail_user = os.getenv("SENDER_EMAIL")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")

        if not gmail_user or not gmail_password:
            raise ValueError(
                "GMAIL_USERNAME or GMAIL_PASSWORD environment variables not set."
            )

        sent_from = gmail_user
        msg = MIMEText(input_data.body)
        msg["Subject"] = input_data.subject
        msg["From"] = sent_from
        msg["To"] = input_data.recipient_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(sent_from, input_data.recipient_email, msg.as_string())

        output_data = PaintOutput(
            message=f"Email sent successfully to {input_data.recipient_email}"
        )

        # Validate output JSON
        # validate_function_input_output("send_email", input_json, output_data.model_dump())

        return output_data.model_dump()
    except ValidationError as e:
        print(f"Validation error: {e}")
        output_data = PaintOutput(message=f"Validation error: {str(e)}")
        return output_data.model_dump()
        # return {"error": str(e)}
    except Exception as e:
        print(f"Error sending email: {e}")
        output_data = PaintOutput(message=f"Error sending email: {str(e)}")
        return output_data.model_dump()

@mcp.tool()
def find_first_fibonacci_numbers(input_data: FibonacciInput) -> FibonacciOutput:
    """Generate the first n Fibonacci numbers."""
    try:
        n = input_data.n
        if n <= 0:
            raise ValueError("n must be a positive integer.")
        
        fibonacci_numbers = []
        a, b = 1, 1
        for _ in range(n):
            fibonacci_numbers.append(a)
            a, b = b, a + b
        
        return FibonacciOutput(fibonacci_numbers=fibonacci_numbers)
    except Exception as e:
        raise ValueError(f"Error generating Fibonacci numbers: {e}")


@mcp.tool()
def calculate_cubes(input_data: CubeInput) -> CubeOutput:
    """Calculate the cubes of a list of numbers."""
    try:
        numbers = input_data.numbers
        cubes = [x**3 for x in numbers]
        return CubeOutput(cubes=cubes)
    except Exception as e:
        raise ValueError(f"Error calculating cubes: {e}")

@mcp.tool()
def calculate_squares(input_data: SquareInput) -> SquareOutput:
    """Calculate the squares of a list of numbers."""
    try:
        numbers = input_data.numbers
        squares = [x**2 for x in numbers]
        return SquareOutput(squares=squares)
    except Exception as e:
        raise ValueError(f"Error calculating squares: {e}")

@mcp.tool()
def calculate_sum(input_data: SumInput) -> SumOutput:
    """Calculate the sum of a list of numbers."""
    try:
        numbers = input_data.numbers
        total = sum(numbers)
        return SumOutput(total=total)
    except Exception as e:
        raise ValueError(f"Error calculating sum: {e}")

@mcp.tool()
async def send_telegram(input_data: TelegramInput) -> PaintOutput:
    """Sends a Telegram message using the Telegram Bot API."""	

        
    """
    Parameters:
    chat_id (str): The unique identifier for the target chat.
    message (str): The content of the message to be sent.

    Returns:
    Dict[str, Any]: A dictionary containing the status of the operation.
    """
    bot_token = os.getenv("TELEGRAM_API_KEY")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": input_data.chat_id, "text": input_data.message}
        
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"HTTP Status Code: {response.status_code}, Response: {response.json()}")
        if response.status_code != 200:
            output_data = PaintOutput(
                message=f"Failed to send message: {response.text}"
            )
            return output_data.model_dump()
        
        output_data = PaintOutput(
            message=f"The message '{input_data.message}' has been successfully transmitted to the chat with ID {input_data.chat_id}."
        )
        return output_data.model_dump()

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return PaintOutput(
            message=f"Failed to send the message '{input_data.message}' to the chat with ID {input_data.chat_id}. Error: {e}"
        )


if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    load_dotenv(override=True)
    env_path = find_dotenv()
    print(env_path)
    print(os.getenv("GMAIL_APP_PASSWORD"))  
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
