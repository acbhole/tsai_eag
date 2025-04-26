import json
from typing import Any, Dict, Union


def clean_json_response(response: Union[str, dict, Any]) -> Dict[str, Any]:
    """
    Cleans and parses JSON response from tool outputs or action dictionaries.
    
    Args:
        response: Can be:
            - dict: Python dictionary
            - str: JSON string
            - object with text attribute
    
    Returns:
        Dict containing parsed data
    
    Example:
        >>> text = "{'type': 'function_call', 'tool_name': 'find_fibonacci'}"
        >>> clean_json_response(text)
        {'type': 'function_call', 'tool_name': 'find_fibonacci'}
    """
    try:
        # If input is None, return empty dict
        if response is None:
            return {}

        # If already a dict, return as is
        if isinstance(response, dict):
            return response

        # If has text attribute (like TextContent), get the text
        if hasattr(response, 'text'):
            response = response.text

        # Convert to string if not already
        if not isinstance(response, str):
            response = str(response)

        # Handle Python dict-like strings
        if response.startswith("{'") or response.startswith("{\""):
            try:
                # First try direct JSON parsing
                return json.loads(response)
            except json.JSONDecodeError:
                # If fails, convert Python single quotes to double quotes
                response = response.replace("'", '"')
                return json.loads(response)

        return json.loads(response)

    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return {"error": str(e), "original": str(response)}