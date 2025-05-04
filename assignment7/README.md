# WebRAG: Web Research and Analysis Guide

## Welcome to WebRAG: Your Friendly Guide to Web Wisdom

Imagine having a trusty companion who can sift through the endless waves of the internet, pulling out just the pearls of knowledge you need. That’s **WebRAG: Web Research and Analysis Guide**, a delightful Chrome extension designed to make your web adventures smarter, faster, and more insightful. Whether you’re a curious student, a busy professional, or just someone who loves to learn, WebRAG is here to help you explore the web like never before.

WebRAG is your personal web whisperer, offering three magical powers right in your Chrome browser:

- **Page Indexing**: Turn any web page into a neat, searchable treasure map, so you can find exactly what you need later.  
- **Quick Summaries**: Get the gist of long articles or blogs in a snap, with short, friendly summaries that capture the heart of the content.  
- **Smart Q&A**: Ask questions about a page, and WebRAG will dig through its index to give you clear, spot-on answers, like chatting with a wise friend.

Built with some of the coolest tech around—like AI language models, semantic search, and clever indexing—WebRAG makes browsing feel like a breeze. It’s perfect for diving into research, prepping for a big meeting, or just satisfying your curiosity without getting lost in a sea of tabs.

---

## What WebRAG Can Do for You

Here’s a peek at the superpowers WebRAG brings to your browser:

1. **Index Pages Like a Librarian**: WebRAG organizes web pages into a tidy, searchable format, so you can revisit key info anytime. It’s like having a personal library for the internet!  
2. **Summarize with Style**: No time to read a 10-page article? WebRAG boils it down to a short, easy-to-read summary that keeps all the good stuff.  
3. **Answer Your Questions**: Got a question about something you’ve indexed? Ask away, and WebRAG will find the answer in the page’s content, giving you a clear, helpful response.

---

## How It Works: The Magic Behind WebRAG

WebRAG is powered by a clever mix of technologies that work together like a well-rehearsed band. Here’s a friendly look at what’s happening under the hood:

### 1. **Turning Web Pages into Readable Notes**  
   - **MCP Markdown Server**: Think of this as WebRAG’s note-taker. It grabs messy web content (all that HTML clutter) and turns it into clean, simple Markdown text. This makes it easy to store and search later.  
   - **Storage**: Those Markdown notes are saved locally as an index, like a digital filing cabinet that’s always ready when you need it.

### 2. **Understanding the Web’s Meaning**  
   - **Nomic Embedding Model**: This is WebRAG’s brain for understanding text. It turns words into special number patterns (called embeddings) that capture what the content is really about.  
   - **FAISS (Fast Similarity Search)**: FAISS is like a super-speedy librarian who can find the most relevant bits of your indexed pages in a flash, using those embeddings to match your searches.

### 3. **Chatting with the Web**  
   - **Gemini Language Model**: This is WebRAG’s storyteller. It writes clear summaries and answers your questions in a friendly, natural way, pulling insights from the indexed content.

---

## Usage: Mastering the Art of WebRAG

WebRAG’s interface is as intuitive as it is powerful, designed to make knowledge exploration feel like second nature. Here’s how to wield its capabilities:

1. **Indexing a Page: Crafting the Foundation**  
   - Navigate to a web page of interest.  
   - Summon WebRAG by clicking its icon in the Chrome toolbar.  
   - Select **Index Page** to transform the page into a searchable index, laying the groundwork for deeper exploration.

2. **Summarizing a Page: Distilling the Essence**  
   - On an indexed page, invoke WebRAG via the toolbar icon.  
   - Choose **Summarize Page** to conjure a concise, insightful summary, crafted by the Gemini LLM.  

3. **Asking Questions: Conversing with Knowledge**  
   - Open the WebRAG interface through the toolbar icon.  
   - Pose your question in the provided text box, as if consulting an ancient oracle.  
   - Submit to receive a response that is both precise and deeply rooted in the indexed content.

---
## How It Works: The Magic Behind WebRAG

WebRAG combines a polished Chrome extension with a robust backend to deliver its magic. Here’s a friendly look at the tech that powers it:

### Frontend: The Chrome Extension

The WebRAG Chrome extension is your gateway to the action, built with a sleek interface and smooth functionality. Based on the provided files (`popup.html`, `popup.css`, `popup.js`, `manifest.json`), here’s what makes it tick:

- **User Interface (`popup.html`, `popup.css`)**:  
  - A clean, modern popup window (600px wide) with tabs for **Main**, **Indexed Pages**, **Stats**, and **Settings**.  
  - Styled with Semantic UI and the Inter font for a professional, approachable look.  
  - Features a gradient-text logo (“WebRAG”) with a deep space vibe (shades of bronze to purple).  
  - Buttons for indexing, summarizing, and querying, plus a textarea for asking questions that auto-expands as you type.  
  - A backend status indicator (green for online, red for offline) keeps you in the loop.  
  - Indexed pages are listed with clickable URLs and delete buttons, styled for clarity and ease of use.  
  - Stats are displayed in a neat table, showing details like the number of indexed pages and embedding dimensions.

- **Functionality (`popup.js`)**:  
  - **Index a Page**: Click the “Index Page” button to save the current page’s content to the backend.  
  - **Summarize**: Hit the “Summarize” button to get a concise summary of the current page.  
  - **Query**: Type a question in the textarea, click “Ask,” and WebRAG fetches answers from the indexed content.  
  - **Manage Pages**: View all indexed pages in the “Indexed Pages” tab, with options to visit or delete them.  
  - **Stats**: The “Stats” tab shows nerdy details like the number of chunks and FAISS index type.  
  - **Settings**: Update the backend API URL in the “Settings” tab, saved via Chrome’s storage API.  
  - Handles API calls to the backend (at `http://127.0.0.1:8000` by default) for indexing, summarizing, querying, and more.  
  - Uses Semantic UI components (tabs, accordions, modals) for a smooth, interactive experience.  

- **Manifest (`manifest.json`)**:  
  - Runs as a Chrome Manifest V3 extension with permissions for scripting, storage, and tab access.  
  - Supports all URLs for maximum flexibility.  
  - Includes icons (16px, 48px, 128px) for a polished look in the Chrome toolbar.  
  - Bundles jQuery and Semantic UI for frontend functionality and styling.

### Backend: The Engine Room of WebRAG

The WebRAG backend is the heart of the extension, quietly working behind the scenes to make everything run smoothly. Built with Python and a suite of powerful libraries, it’s designed to be fast, reliable, and easy to extend. Here’s a closer look at how it’s put together, based on the provided code:

#### Key Components

1. **Memory Management (`memory.py`)**  
   The backend uses a `Memory` class to handle all the indexing and searching magic. It:  
   - Splits web content into bite-sized chunks (1000 tokens each) for easier processing.  
   - Creates embeddings using the Nomic model (`nomic-ai/nomic-embed-text-v1.5`).  
   - Stores these embeddings in a FAISS index for lightning-fast searches.  
   - Saves everything locally (in `faiss_index.bin` and `chunks.pickle`) so your data stays private and accessible.  
   - Supports searching for relevant content by comparing your query to the indexed chunks, returning the top matches.

2. **Decision Logic (`decision.py`)**  
   This is where WebRAG decides what to do with your requests:  
   - **Tool Selection**: Uses the Gemini model to pick the best tool for a task, like choosing the right tool to process a URL.  
   - **Summarization and Q&A**: Calls the Gemini API to create summaries or answer questions based on indexed content, returning results in clean JSON format.  
   - **JSON Parsing**: Strips away any extra formatting (like Markdown code blocks) to ensure responses are tidy and usable.

3. **API Endpoints (`agent.py`)**  
   The backend runs a FastAPI server that powers WebRAG’s features through simple, secure endpoints:  
   - **`POST /indexed-pages`**: Indexes a web page by fetching its content, converting it to Markdown, and storing it in the FAISS index.  
   - **`POST /queries`**: Searches the index for answers to your questions, combining relevant chunks and using Gemini to craft a response.  
   - **`POST /summaries`**: Generates a summary for a specific URL using the indexed content.  
   - **`GET /indexed-pages`**: Shows all the URLs you’ve indexed.  
   - **`POST /delete-indexed-pages`**: Removes a page and its chunks from the index.  
   - **`GET /health`**: Checks the system’s status 
   - **`GET /index-stats`**: Provides stats like the number of indexed pages and chunks.

4. **Actions (`action.py`)**  
   These are the tasks WebRAG performs:  
   - **Indexing**: Connects to the MCP server to fetch and process web content, then indexes it with the `Memory` class.  
   - **Searching**: Finds relevant chunks for a query and uses Gemini to generate a clear, friendly answer.  
   - **Tool Invocation**: Works with the MCP server to pick and run the right tool for processing web pages.

5. **Data Models (`models.py`)**  
   WebRAG uses Pydantic models to keep things organized:  
   - `URLRequest`: Handles requests to index a page.
   - `QueryRequest`: Processes search queries with an optional limit (default: 5 results).  

### Backend Setup

To get the backend up and running, you’ll need:  
- **Python 3.8+** and dependencies like `fastapi`, `sentence-transformers`, `faiss-cpu`, `requests`, and `pydantic`.  
- Environment variables:  
  - `GEMINI_API_KEY`: For accessing the Gemini API.  
  - `MCP_SERVER_URL`: The address of your MCP Markdown server.  
- Local storage for the FAISS index and chunk data.  

Run the FastAPI server with `uvicorn agent:app --reload` (after installing dependencies), and WebRAG’s backend will be ready to handle requests from the Chrome extension.

## Acknowledgments: Honoring the Architects

The WebRAG saga is enriched by the contributions of many:  
- The open-source community, whose work on Nomic, FAISS, and Gemini forms the bedrock of our innovation.  
- The MCP Markdown Server artisans, who enable the seamless transformation of web content.

---
