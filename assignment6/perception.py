import asyncio
import json

from google import genai


class Perception:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)

    async def get_llm_response(self, prompt):
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
            }

        )
        response_text = response.text.strip()
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response", "raw_response": response_text}