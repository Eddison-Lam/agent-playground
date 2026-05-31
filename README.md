# AI Assistant with RAG Memory

A local AI Agent Playground built with **LangGraph**, featuring robust tool calling, persistent RAG memory, and stateful multi-step reasoning.
---

## Features

- **LangGraph Architecture** — Powered by LangGraph StateGraph for clear, controllable, and debuggable agent workflows
- **Persistent RAG Memory** — Long-term vector memory with export and management capabilities
- **Advanced Tool Calling** — `web_search`, `python_sandbox`, and easily extensible tools
- **Dynamic Tool Control** — Enable/disable tools at runtime
- **Hong Kong Weather Rules** — Strictly enforces fresh weather data fetching for accuracy
- **Slash Commands** — `/help`, `/tools`, `/export`, `/settings`, etc.
- **Docker Support** — Easy deployment with sandbox environment
- **Modular & Clean Codebase** — Well-structured for further development
---

## Quick Start

### Option 1: Ollama (Recommended)

#### Prerequisites
- [Ollama](https://ollama.com/download)
- Docker (required for `python_sandbox`)

```bash
# 1. Pull required models
ollama pull qwen2.5:7b      # ollama model as you want to use
ollama pull nomic-embed-text    # ollama embedding model as you want to use

# 2. Setup project
git clone https://github.com/Eddison-Lam/agent-playground.git
cd cd agent-playground

# 3. Install dependencies
pip install -r requirements.txt
or 
uv sync

# 4. Build python sandbox for agent
docker build -t ai-sandbox .

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
- LangGraph (LangChain) — Agent orchestration
- LLM: Qwen2.5-7B
- Embedding Model: nomic-embed-text
- Vector Database: ChromaDB
- Tools: Web search + Secure Python sandbox

## Project Structure
```
.
├── Dockerfile
├── README.md
├── scripts/                  # Windows start & install scripts
├── src/
│   ├── main.py
│   ├── config.py
│   ├── settings.py
│   ├── rag_manager.py
│   ├── command_handler.py
│   ├── agent/                # LangGraph core
│   │   ├── state.py
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   ├── router.py
│   │   └── router_agent.py
│   ├── tools/                # Tool system
│   │   ├── manager.py
│   │   ├── registry.py
│   │   ├── base.py
│   │   └── implementations/
│   ├── prompts/skills/       # Skill-specific prompts
│   ├── llm/                  # LLM providers
│   ├── ui/                   # CLI & UI layer
│   └── ...
├── rag_mem/                  # Persistent RAG database (Chroma)
├── tests/
├── log/                      # Log files
└── ...
```

Contributions are welcome! Feel free to open Issues or Pull Requests.