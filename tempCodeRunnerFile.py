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
SYSTEM_PROMPT = """
You are a helpful AI assistant for casual conversation and advice.

RULES (follow strictly, no exceptions):
- For normal questions, advice, email drafting, gratitude messages, HR communication tips, etc. → ALWAYS output NORMAL TEXT ONLY. Do NOT use any JSON or tool.
- ONLY use tools when you genuinely need external information (web search) or computation (code execution, calculation, stock price, etc.).
- Never use python_sandbox just to "print" a suggestion. That's not what the tool is for.

If you decide to use a tool, output **ONLY** the clean JSON, nothing else before or after it.
If you are giving the final answer to the user, output normal text with no JSON at all.

For a single tool call:
{
  "tool": "tool_name",
  "arguments": {
    "arg_name": "value"
  }
}

For multiple tool calls in parallel:
[
  {
    "tool": "tool_name1",
    "arguments": { ... }
  },
  {
    "tool": "tool_name2",
    "arguments": { ... }
  }
]

After receiving tool results, you can either:
- output another JSON tool call(s), or
- output a normal text response (the final answer to the user)

Available tools:
1. web_search
   arguments:
     - url: (string, required) The specific target URL to fetch data from.
     - params: (object, optional) Query parameters to append to the URL (e.g., search filters, pagination).

2. python_sandbox
   - arguments: {"code": "the full python code here"}

Rules:
- For stock prices, financial data, calculations → ALWAYS prefer python_sandbox with yfinance
- Never use web_search for current stock prices (it's unreliable)
- The code in python_sandbox must be complete and runnable
- Use print() to output results
- Do NOT add extra ``` or quotes outside the JSON
"""

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

def web_search(url: str, params= None) -> str:
    """Existing web search function."""
    logger.info(f"Searching: {url}")
    try:
        url=url
        response = requests.get(url, params=params, timeout=10)
        return {
            "status": response.status_code,
            "success": response.ok,      # 若狀態碼為 200-299 則為 True
            "data": response.json() if response.ok else None,
            "error": response.text if not response.ok else None
        }
    except Exception as e:
        return {
            "status": "error",
            "success": False,
            "data": None,
            "error": str(e)
        }
    
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
    if user_input.lower() in ['exit', 'quit']:
        break

    logger.info(f'User input: {user_input}')

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # RAG 部分保持不變
    q_emb = ollama.embeddings(model=EMBED_MODEL, prompt=user_input)['embedding']
    results = collection.query(query_embeddings=[q_emb], n_results=5)
    retrieved_docs = results['documents'][0] if results['documents'] else []
    old_mem_text = "\n".join(retrieved_docs)
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
                if not isinstance(call, dict) or "tool" not in call:    continue
                tool_name = call["tool"]
                args = call.get("arguments", {})
                if tool_name == "web_search":
                    url = args.get("url", "")
                    params= args.get("params", "")
                    if url:
                        result = web_search(url, params)
                        tool_results.append(f"web_search result for '{url}':\n{result}")
                        tool_calls_made = True
                elif tool_name == "python_sandbox":
                    code = args.get("code", "")
                    if code:
                        print("🛠️  Running Python Sandbox...")
                        result = python_sandbox(code)
                        tool_results.append(f"python_sandbox result:\n{result}")
                        tool_calls_made = True
                tool_results.append(result)
            # 2. 將工具結果餵回
            if tool_calls_made:
                if tool_results:
                    combined = "\n\n".join(tool_results)
                    # 這裡建議標註這是 Tool Output，讓模型知道這是它剛才請求的結果
                    messages.append({'role': 'user', 'content': f"TOOL RESULTS:\n{combined}\n\nBased on these results, give me the final answer or next step."})
            
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

    # 只把「最終乾淨回答」存進 RAG 和 short_hist
    # 如果 ai_final 看起來是 JSON tool call，就不要存（或只存最終版）
    if not get_json_from_ai(ai_final):  # 如果不是 tool call，才視為最終回答
        short_hist.append({'role': 'assistant', 'content': ai_final})
        
        # 存進 RAG 的內容要乾淨、有意義
        combined_log = f"User: {user_input}\nAI: {ai_final}"
        
        c_emb = ollama.embeddings(model=EMBED_MODEL, prompt=combined_log)['embedding']
        collection.add(
            ids=[f"id_{collection.count()}_{uuid.uuid4().hex[:4]}"],
            embeddings=[c_emb],
            documents=[combined_log]
        )
    else:
        # 如果還是 tool call（異常情況），可以選擇不存，或只存 user 部分
        short_hist.append({'role': 'assistant', 'content': ai_final})  # 還是保留在 short-term
        logger.warning("AI 輸出了 tool call 作為最終回答，跳過 RAG 儲存")
