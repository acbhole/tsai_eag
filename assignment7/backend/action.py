# coding: utf-8
"""
Actions for tool selection and page logging using FastMCP.
"""

from decision import generate_summary, parse_llm_json, select_tool_for_task
from fastmcp import Client
from memory import Memory

INDEXED = "indexed"

async def index_page_action(url: str, memory_manager: Memory, mcp_server_url: str) -> dict:
    """Index a page and its HTML content.

    Args:
        url (str): The URL of the page to index.
        memory_manager (Memory): The memory manager instance.
        mcp_server_url (str): The URL of the MCP server.

    Returns:
        dict: The result of the indexing action.
    """
    async with Client(mcp_server_url) as client:
        tools = await client.list_tools()
        tool_name = select_tool_for_task(tools, url)
        if not tool_name:
            return {"status": "error", "reason": "No suitable tool found by LLM."}

        result = await invoke_tool(client, tool_name, url)
        markdown = extract_markdown_from_result(result)
        chunks = memory_manager.chunk_text(markdown)
        memory_manager.add_to_index(url, chunks)
        summary = generate_summary(markdown)

        return build_index_response(url, chunks, summary)

async def get_tools(mcp_server_url: str):
    """Get the list of tools available from the MCP server.

    Args:
        mcp_server_url (str): The URL of the MCP server.

    Returns:
        list: A list of available tools from the MCP server.
    """
    client = Client(mcp_server_url)
    async with client:
        tools = await client.list_tools()
    return tools, client

async def invoke_tool(client: Client, tool_name: str, url: str):
    """Invoke a tool with the given URL.

    Args:
        client (Client): The client instance for making requests.
        tool_name (str): The name of the tool to invoke.
        url (str): The URL to be processed by the tool.

    Returns:
        dict: The result of the tool invocation.
    """
    return await client.call_tool(tool_name, {"uri": url})

def build_index_response(url: str, chunks: list, summary: str) -> dict:
    """Build the response for the indexed page.

    Args:
        url (str): The URL of the indexed page.
        chunks (list): The chunks of text indexed from the page.
        summary (str): A summary of the indexed content.

    Returns:
        dict: A dictionary containing the status, URL, number of chunks, and summary.
    """

    return {
        "status": INDEXED,
        "url": url,
        "num_chunks": len(chunks),
        "summary": summary
    }

def extract_markdown_from_result(result) -> str:
    """Extract markdown text from the result.

    Args:
        result (Union[list, dict]): The result from which to extract markdown.

    Returns:
        str: The extracted markdown text.
    """
    if isinstance(result, list) and result:
        markdown = getattr(result[0], "text", str(result[0]))
    elif hasattr(result, "text"):
        markdown = result.text
    elif isinstance(result, dict) and "text" in result:
        markdown = result["text"]
    else:
        markdown = str(result)
    return markdown

def search_action(query: str, memory_manager: Memory, k: int = 5) -> dict:
    """Search for relevant content based on the query.

    Args:
        query (str): The search query.
        memory_manager (Memory): The memory manager instance.
        k (int, optional): The number of results to return. Defaults to 5.

    Returns:
        dict: A dictionary containing the search results, answer, and source URLs.
    """
    results = memory_manager.search(query, k)
    context = "\n\n".join([r["chunk"] for r in results])
    source_urls = list({r["url"] for r in results if "url" in r})
    llm_json = generate_summary(context, query, source_urls)
    try:
        parsed = parse_llm_json(llm_json)
        answer = parsed.get("answer", "")
        found_answer = parsed.get("found_answer", False)
        urls = parsed.get("source_urls", source_urls)
    except Exception:
        answer = llm_json
        found_answer = False
        urls = source_urls
    return {
        "results": results,
        "answer": answer,
        "found_answer": found_answer,
        "source_urls": urls
    }
