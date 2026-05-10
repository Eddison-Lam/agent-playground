import ollama
import chromadb
# from ddgs import DDGS not used
import requests
import re
import logging
import docker
import json
import os
import uuid
from datetime import datetime

import rag_manager as rag
rag_manager = rag.RAGManager(
    db_path='./my_mem', 
    collection_name='chat_hist'
)

# --- Constants & Logging ---
MODEL_NAME = "qwen2.5:7b"
EMBED_MODEL = "nomic-embed-text"
log_dir = "log"
if not os.path.exists(log_dir):os.makedirs(log_dir)
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(log_dir, f"chat_debug_{current_time}.log")

logging.basicConfig(
    level=logging.INFO, 
    filename=log_filename, 
    encoding='utf-8',
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
SYSTEM_PROMPT = f'''
You are a helpful AI assistant...

RULES (follow strictly):
- For normal conversation, advice, drafting, etc. → ALWAYS output NORMAL TEXT ONLY. No JSON.
- Use tools when you genuinely need external information or computation (Hong Kong weather etc.)
- If you decide to use a tool, output **ONLY** the clean JSON, nothing else.

Hong Kong Weather Special Rules (MUST FOLLOW strictly):
- For ANY question related to current weather, today's weather, forecast, 9-day forecast, tomorrow, or future weather in Hong Kong, you MUST use the web_search tool to fetch the latest data.
- NEVER rely on RAG memories or previous conversation history for weather information, because they may be outdated.
- Weather forecasts change frequently. Always prioritize fresh tool results over any stored memories.
- The system provides the Current Time: {current_time}. Use this time as reference. 
  If the weather data in memory is from a significantly earlier date, ignore it and call the tool instead.
- NEVER guess, invent, or hallucinate any weather details (temperatures, rain probability, weather description, etc.).
- If you are unsure whether the data is fresh enough, call the web_search tool to be safe.
Correct URLs (always use the full URL with /textonly/v2/):

- Directory / Index page: https://www.hko.gov.hk/textonly/v2/

- Current Weather Report (即時天氣報告): 
  https://www.hko.gov.hk/textonly/v2/forecast/englishwx2.htm

- 9-Day Weather Forecast (九天天氣預報):
  https://www.hko.gov.hk/textonly/v2/forecast/nday_v2.htm

- Local Weather Forecast:
  https://www.hko.gov.hk/textonly/v2/forecast/localc.htm

Rules for sub-pages:
- If you fetch the directory page and it contains links like <a href="forecast/xxx.htm">, always convert it to the full URL: https://www.hko.gov.hk/textonly/v2/forecast/xxx.htm
Available tools:

1. web_search
   arguments:
     - url: (string, required)
     - params: (object, optional)
   description: Fetches content from any URL. If the page is a directory/index with links, summarize the important links and suggest or directly call the tool again on the most useful sub-page for current weather.

2. python_sandbox
   arguments:
     - code: (string, required)
   description: Execute Python code in a secure sandbox. Returns the stdout + stderr as string.

Tool calling format:
- Single tool:
{{
  "tool": "tool_name",
  "arguments": {{
    "arg_name": "value"
  }}
}}

- Multiple tools:
[
  {{"tool": "tool_name1", "arguments": {...}}},
  {{"tool": "tool_name2", "arguments": {...}}}
]

Important:
- After you receive the TOOL RESULTS, you MUST give the final answer in normal text.
- Do NOT output JSON/tool call again unless you need another tool call.
- The tool results will be given to you as normal text (string).
'''

# --- Docker Setup ---
docker_client = docker.from_env()

def python_sandbox(code: str) -> str:
    """直接在 Docker 容器內執行 Code，不產生本地檔案"""
    logger.info(f"Executing Python Sandbox...")
    try:
        # 使用 sh -c 來執行 python 並從 stdin 讀取代碼
        container = docker_client.containers.run(
            image="ai-sandbox",
            command=['python3', '-c', code], # 直接作為參數傳入，或透過 stdin
            network_mode="bridge",
            mem_limit="256m",
            cpu_quota=50000,
            remove=True,
            stdout=True, stderr=True,
            detach=False
        )
        logger.info(f"Code result: {container.decode('utf-8')}")
        return container.decode('utf-8')
    except Exception as e:
        logger.error(f"Sandbox Error: {e}")
        return f"Execution Error: {str(e)}"

def web_search(url: str, params=None) -> str:
    """通用網頁抓取：支援 JSON API 和純文字/HTML 頁面"""
    logger.info(f"Fetching: {url}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        }
        response = requests.get(url, params=params, timeout=15, headers=headers)
        
        logger.info(f"Status: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}")

        if not response.ok:
            return f"HTTP Error {response.status_code}: {response.text[:800]}"

        content_type = response.headers.get("Content-Type", "").lower()

        if "application/json" in content_type:
            # 是 JSON API
            data = response.json()
            return json.dumps({
                "success": True,
                "status": response.status_code,
                "data": data
            }, ensure_ascii=False, indent=2)
        else:
            # 是 HTML 或純文字頁面（例如 HKO textonly）
            text = response.text[:8000]   # 限制長度，避免 token 爆炸
            return f"""URL: {url}
Status: {response.status_code}
Content-Type: {content_type}

--- Page Content ---
{text}
"""
    except requests.exceptions.RequestException as e:
        return f"Network error fetching {url}: {str(e)}"
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return f"Failed to process {url}: {str(e)}"
    
def get_json_from_ai(text):
    # 先試著找最外層的完整 JSON（避免抓到嵌套或文字中的）
    match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', text, re.DOTALL)
    if not match:
        match = re.search(r'(\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\])', text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(1))
            # 額外檢查是否真的是 tool call
            if isinstance(parsed, dict) and "tool" in parsed:
                return parsed
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict) and "tool" in parsed[0]:
                return parsed
        except:
            pass
    return None
# --- Main Logic ---
db = chromadb.PersistentClient(path="./my_mem")
collection = db.get_or_create_collection("chat_hist")
short_hist = []

while True:
    user_input = input("\nUser >>> ")
    quit_variants = {'quit', 'exit', 'q', 'qq', 'quitt', 'quir', 'quti', 'exitt', 'exi'}
    if user_input.lower() in quit_variants:
        print("Goodbye! 👋")
        break

    logger.info(f'User input: {user_input}')

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # RAG 部分保持不變
    old_mem_text = rag_manager.get_relevant_memories(user_input, n_results=5)
    logger.info(f"RAG Retrieved: {old_mem_text}")

    full_system_prompt = f"""
{SYSTEM_PROMPT}
[Environment]
Current Time: {current_time}

- Related Past Memories: 
{old_mem_text if old_mem_text else "None"}
"""

    # 初始化這次對話的 messages
    messages = [
        {'role': 'system', 'content': full_system_prompt}
    ] + short_hist + [
        {'role': 'user', 'content': user_input}
    ]
    logger.info(f'Full message to AI: {messages}')
    max_steps = 10   # 防止無限循環
    step = 0

    while step < max_steps:
        step += 1
        response = ollama.chat(model=MODEL_NAME, messages=messages)
        ai_raw = response['message']['content']
        
        # 1. 儲存 AI 的這一次回覆（包含它呼叫工具的意圖）
        messages.append({'role': 'assistant', 'content': ai_raw})

        parsed = get_json_from_ai(ai_raw)
        
        if parsed:
            tool_calls = [parsed] if isinstance(parsed, dict) else parsed
            tool_results = []
            
            for call in tool_calls:
                tool_name = call["tool"]
                args = call.get("arguments", {})
                result = None

                if tool_name == "web_search":
                    url = args.get("url", "")
                    params = args.get("params")
                    if url:
                        result = web_search(url, params)
                        print(f"Searching using url: {url}...")
                        tool_results.append(f"=== web_search result ===\n{result}")

                elif tool_name == "python_sandbox":
                    code = args.get("code", "")
                    if code:
                        print(f"Running python sandbox...")
                        result = python_sandbox(code)
                        tool_results.append(f"=== python_sandbox result ===\n{result}")

            # 然後再塞回去
            if tool_results:
                combined = "\n\n".join(tool_results)
                messages.append({
                    'role': 'user', 
                    'content': f"TOOL RESULTS:\n{combined}\n\nNow, based on these results, give me the final answer in normal text."
                })
            
            # 繼續下一輪 loop 讓 LLM 讀取結果
            continue 
        else:
            # 沒有 JSON，代表是最終文字回答
            ai_final = ai_raw
            break

    else:
        ai_final = "達到最大步數限制，最後一輪回覆如下：\n" + ai_raw

    print(f"\nAI: {ai_final}")

    short_hist.append({'role': 'user', 'content': user_input})
    logger.info(f"User: {user_input}\n")
    logger.info(f"AI: {ai_final}\n")
    # 只把「最終乾淨回答」存進 RAG 和 short_hist
    # 如果 ai_final 看起來是 JSON tool call，就不要存（或只存最終版）
    if not get_json_from_ai(ai_final):  # 如果不是 tool call，才視為最終回答
        short_hist.append({'role': 'assistant', 'content': ai_final})
        
        # 存進 RAG 的內容要乾淨、有意義
        rag_manager.add_mem(
            text=f"User: {user_input}\nAI: {ai_final}",
            metadata={
                "type": "chat",
                "user_input": user_input[:100],
                "model": MODEL_NAME
            }
        )
    else:
        # 如果還是 tool call（異常情況），可以選擇不存，或只存 user 部分
        short_hist.append({'role': 'assistant', 'content': ai_final})  # 還是保留在 short-term
        logger.warning("AI 輸出了 tool call 作為最終回答，跳過 RAG 儲存")
        if len(short_hist) > 10:        # 5 輪 = 10 條訊息
            short_hist = short_hist[-10:]
