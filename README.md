# AI Assistant with RAG Memory

A local AI assistant powered by Ollama, featuring **Tool Calling**, **RAG long-term memory**, and a comprehensive slash command system. Specially optimized for reliable Hong Kong weather information.

---

## Features

- **RAG Memory System** – Persistent memory with export and management
- **Tool Calling** – `web_search`, `python_sandbox`, and easily extensible
- **Dynamic Tool Control** – Enable/disable tools at runtime
- **Hong Kong Weather Rules** – Strictly enforces fresh data fetching
- **Slash Commands** – `/export`, `/setting`, `/tools`, etc.
- **Docker Support** – Easy deployment
- **Modular Architecture** – Clean and maintainable code

---

## Quick Start

### Option 1: Ollama (Recommended)

#### Prerequisites
- [Ollama](https://ollama.com/download)
- Docker (required for `python_sandbox`)

```bash
# 1. Pull required models
ollama pull qwen2.5:7b
ollama pull nomic-embed-text

# 2. Setup project
git clone <your-repo-url>
cd <repo-dir>

# 3. Install dependencies
pip install -r requirements.txt
or 
uv sync

# 4. Build python sandbox for agent
docker build -t my-python-sandbox .

# 5. Run
python main.py
```

## Available Commands

| Command |Description |
| :--- | :--- |
| /help | Show all available commands|
| /tools | Show current tool status |
| /setting <tool> <?confirm> <on/off> | Enable or disable a tool (with confirm: set need_confirmation of a tool) |
| /export [day|week|month|all] [keyword] | Export memories to Markdown |
| /delete <mem_id> | Delete a specific memory |
### Examples
```bash
/export all
/export day weather
/setting python_sandbox off
/setting python_sandbox confirm off
/tools
```

## Important Notes
- `python_sandbox` is a high-risk tool and requires user confirmation by default. By allowing usage of sandbox, all consequences arising from the execution of the code shall be the sole responsibility of the user. allow usage of sandbox, all consequences 
- Exported files are saved in the exports/ directory.
- First run will automatically create necessary folders and database.

## Tech Stack
- LLM: Qwen2.5-7B
- Embedding Model: nomic-embed-text
- Vector Database: ChromaDB
- Tools: Web search + Secure Python sandbox

Contributions are welcome! Feel free to open Issues or Pull Requests.