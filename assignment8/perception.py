import asyncio
import json
import os
from ast import literal_eval
from concurrent.futures import TimeoutError

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

load_dotenv()

class Response(BaseModel):
    function_name: str
    params: list[str]
    final_ans: str
    reasoning_type: str


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

async def generate_with_timeout(prompt, timeout=10):
    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(

                    model="gemini-2.0-flash",
                    contents=prompt,
                    config={
                        'response_mime_type': 'application/json',
                        'response_schema': Response,
                    },
                )
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

def validate_response(response_text):
    try:
        parsed = literal_eval(json.loads(json.dumps(response_text.strip())))
        Response(**parsed)
        return parsed
    except Exception as e:
        raise ValueError(f"Invalid response format: {e}")

