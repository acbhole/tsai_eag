# coding: utf-8
"""
Decision logic for tool selection and LLM-based summarization.
"""

import json
import os
import re

from perception import Perception
from prompt_loader import load_prompt

# Initialize the Perception client
api_key = os.getenv("GEMINI_API_KEY")
perception_client = Perception(api_key)

def parse_llm_json(llm_json):
    """
    Remove markdown code block if present and parse JSON.
    """
    match = re.search(r'{.*}', llm_json, re.DOTALL)
    if match:
        llm_json = match.group(0)
    return json.loads(llm_json)

async def generate_summary(markdown: str, query: str = None, source_urls=None) -> str:
    """
    Call Gemini-2.0-Flash to summarize or answer a question with provided context. Returns JSON format.
    """
    if source_urls is None:
        source_urls = []
    urls_json = json.dumps(source_urls, ensure_ascii=False)

    if query:
        prompt = load_prompt(
            "user_query_prompt.txt",
            urls_json=urls_json,
            markdown=markdown,
            query=query,
        )
    else:
        prompt = load_prompt(
            "summarize_prompt.txt",
            urls_json=urls_json,
            markdown=markdown,
        )
    try:
        response = await perception_client.get_llm_response(prompt)
        return response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    except Exception as e:
        return json.dumps({"answer": f"[Gemini API error: {e}]", "found_answer": False, "source_urls": []})

async def select_tool_for_task(tools, user_input):
    """Selects the appropriate tool based on user input and available tools.

    Args:
        tools (list): A list of available tools.
        user_input (str): The input provided by the user.

    Returns:
        str: The name of the selected tool or None if no tool is selected.
    """
    
    tools_json = json.dumps([
        {"name": t.name, "description": getattr(t, 'description', '')} for t in tools
    ], ensure_ascii=False)

    prompt = load_prompt(
        "tool_selection_prompt.txt",
        tools_json=tools_json,
        user_input=user_input,
    )
    try:
        response = await perception_client.get_llm_response(prompt)
        return response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip().strip('"')
    except Exception:
        return None
