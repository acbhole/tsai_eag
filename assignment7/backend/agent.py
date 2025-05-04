import os

import faiss
import numpy as np
from action import index_page_action, search_action
from decision import generate_summary
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from memory import Memory
from models import QueryRequest, URLRequest

# Load environment variables from .env file
# This is useful for storing sensitive information like API keys
load_dotenv()
app = FastAPI()

# Initialize the memory manager
memory = Memory()
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")

@app.post("/indexed-pages")
async def index_page(request: Request):
    """Index a page and log its URL.

    Args:
        request (Request): The incoming request containing the URL to index.

    Returns:
        dict: A dictionary containing the status of the indexing and the URL.
    """
    data = await request.json()
    url = data["url"]

    return await index_page_action(url, memory, MCP_SERVER_URL)

@app.post("/queries")
async def queries(request: QueryRequest):
    """
    Handle a user query.

    Args:
    request (QueryRequest): The incoming search request with query and k.

    Returns:
    The result of the search action.
    """
    query = request.query
    k = request.k
    return search_action(query, memory, k)

@app.post("/summaries")
async def summaries(request: URLRequest):
    """
    Generate a summary for a given URL.

    Args:
    request (URLRequest): The incoming summary request with URL.

    Returns:
    The generated summary for the URL.
    """
    url = request.url
    # Find all chunks for the url
    chunks = [c["chunk"] for c in memory.chunks if c["url"] == url]
    if not chunks:
        return {"error": "No content found for this URL. Please index it first."}
    context = "\n\n".join(chunks)
    summary_text = generate_summary(context)
    return {"url": url, "summary": summary_text}

@app.get("/indexed-pages")
async def list_pages():
    """
    List all unique URLs indexed.

    Returns:
    A list of unique URLs.
    """
    # Return unique URLs indexed
    urls = list({c["url"] for c in memory.chunks})
    return {"urls": urls}

@app.post("/delete-indexed-pages")
async def delete_page(request: URLRequest):
    """Delete indexed pages for a given URL.

    Args:
        request (URLRequest): The incoming request containing the URL to delete.

    Returns:
        dict: A dictionary containing the status of the deletion and the URL.
    """
    url = request.url
    # Remove all chunks for this URL and rebuild index
    old_indices = [i for i, c in enumerate(memory.chunks) if c["url"] == url]
    if not old_indices:
        return {"status": "not_found", "url": url}
    keep_indices = [i for i in range(len(memory.chunks)) if i not in old_indices]
    if keep_indices:
        kept_embs = [memory.chunks[i]["embedding"] for i in keep_indices]
        memory.index = faiss.IndexFlatL2(memory.model.get_sentence_embedding_dimension())
        if kept_embs:
            memory.index.add(np.array(kept_embs).astype('float32'))
        memory.chunks = [memory.chunks[i] for i in keep_indices]
    else:
        memory.index = faiss.IndexFlatL2(memory.model.get_sentence_embedding_dimension())
        memory.chunks = []
    memory._save_index()
    return {"status": "deleted", "url": url}

@app.get("/health")
async def health():
    """
    Check the health of the application.

    Returns:
    The health status of the application.
    """
    # Check if embedding model and FAISS index are loaded
    try:
        dim = memory.model.get_sentence_embedding_dimension()
        num_vecs = memory.index.ntotal
        return {"status": "ok", "embedding_model_dim": dim, "faiss_vectors": num_vecs}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/index-stats")
async def faiss_stats():
    """Get statistics about the FAISS index.
    Returns:
        dict: A dictionary containing the number of pages, embedding dimension, number of chunks, and FAISS index type.
    """
    try:
        dim = memory.model.get_sentence_embedding_dimension()
        num_pages = len(list({c["url"] for c in memory.chunks}))
        return {
            "num_pages": num_pages,
            "embedding_dim": dim,
            "num_chunks": len(memory.chunks),
            "faiss_index_type": type(memory.index).__name__
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
