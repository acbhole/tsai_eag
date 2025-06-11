# F1 Standings Automation Agent

## Overview

This project is a **data processing agent** designed to automate the retrieval, processing, and sharing of the latest Formula 1 standings. The agent fetches the standings, uploads the data to Google Sheets, and emails the generated link to the user. It leverages **Google APIs**, **Telegram Bot**, and **LLM-based decision-making** to provide a seamless experience.

---

## Features

1. **Fetch Latest F1 Standings**  
   - Retrieves the current Formula 1 driver standings using the Jolpica F1 open source API for querying Formula 1 data, with backwards compatible endpoints for the soon to be deprecated Ergast API.
   - Processes and structures the data for further use.

2. **Upload Data to Google Sheets**  
   - Automatically uploads the standings to a Google Sheet.
   - Shares the sheet with public read-only access.

3. **Email the Google Sheets Link**  
   - Sends the generated Google Sheets link to the user via email.

4. **Telegram Bot Integration**  
   - Allows users to interact with the agent through a Telegram bot.

5. **LLM-Based Decision Making**  
   - Uses a large language model to decide the next steps in the workflow.

---

## Architecture

The project is built using a modular architecture with the following components:

### 1. **Core Tools**
- **`get_current_f1_standings`**: Fetches the latest F1 standings.
- **`upload_data_to_sheets`**: Uploads the standings to Google Sheets and returns the link.
- **`send_email`**: Sends the Google Sheets link to the user's email.

### 2. **LLM Integration**
- Uses **Gemini 2.0 Flash** for reasoning and decision-making.
- Validates and processes responses using Pydantic schemas.

### 3. **State Management**
- Tracks the workflow's progress using a JSON-based state file (`app_state.json`).
- Logs each iteration for debugging and auditing.

### 4. **Telegram Bot**
- Provides a user-friendly interface for triggering the workflow.
- Built using the **Python Telegram Bot** library.

---

## Installation

### Prerequisites
- Python 3.9 or higher
- Google Cloud Service Account credentials (credentials_sa.json)
- Telegram Bot Token
- Gmail API credentials (token.json)

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/acbhole/tsai_eag.git
   cd assignment8
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a .env file in the root directory.
   - Add the following variables:
     ```env
     GEMINI_API_KEY=your-gemini-api-key
     TELEGRAM_API_KEY=your-telegram-bot-token
     SENDER_EMAIL=your-email@example.com
     SSE_PORT=9135
     ```

4. Add Google Cloud credentials:
   - Place your credentials_sa.json file in the root directory.
   - Ensure the service account has access to Google Sheets and Drive APIs.

5. Set up Gmail API:
   - Follow the [Gmail API Quickstart Guide](https://developers.google.com/gmail/api/quickstart/python) to generate token.json.

---

## Usage

### 1. Start the Server
Run the server to enable the tools and SSE communication:
```bash
python mcp_sse_server.py
```

### 2. Start the Telegram Bot
Launch the Telegram bot to interact with the agent:
```bash
python mcp_sse_client.py
```

### 3. Interact with the Bot
- Send a message to the bot (e.g., "Fetch F1 standings").
- The bot will process the request and provide updates.

---

## File Structure

```plaintext
assignment8
├── action.py               # Executes tools based on LLM decisions
├── decision.py             # Builds prompts and processes tool descriptions
├── memory.py               # Manages state and logs iterations
├── mcp_sse_client.py       # Telegram bot client
├── mcp_sse_server.py       # SSE server for tool execution
├── perception.py           # Handles LLM responses and validation
├── prompt_loader.py        # Loads user and system prompts
├── user_prompt.txt         # User-facing prompt template
├── system_prompt.txt       # System-facing prompt template
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---

## Logging and Debugging

- Logs are stored in assignment8.log.
- Each step of the workflow is logged for easy debugging.

---

## Future Enhancements

- Add support for additional APIs (e.g., constructor standings).
- Enhance error handling and retry mechanisms.
- Improve user experience with richer Telegram bot interactions.
