# main.py
import ollama
from datetime import datetime

# 自訂模組
from logger_utils import get_logger
import rag_manager as rag
import tools
import config


# ====================== 初始化 ======================
logger = get_logger("Main", subdir="main")

logger.info("=== AI Assistant Starting ===")

# 初始化 RAG Manager
rag_manager = rag.RAGManager(
    db_path='./my_mem', 
    collection_name='chat_hist',
    EMBED_MODEL=config.EMBED_MODEL
)

MODEL_NAME = config.MODEL_NAME

# ====================== 只建立一次 System Prompt ======================
# 這個只會在程式啟動時建立一次，之後不會重複傳送
BASE_SYSTEM_PROMPT = config.get_system_prompt(
    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
)

print("AI Assistant start! Enter 'quit' or 'exit' to end.\n")


# ====================== 主程式 ======================
def main():
    short_hist = []   # 只存 user + assistant 的對話紀錄
    quit_variants = {'quit', 'exit', 'q', 'qq', 'quitt', 'quir', 'quti', 'exitt', 'exi'}

    while True:
        try:
            user_input = input("\nUser >>> ").strip()
            
            if user_input.lower() in quit_variants:
                print("👋 Goodbye!")
                logger.info("User exited the program.")
                break

            logger.info(f"User input: {user_input}")

            # === 每次動態取得最新資訊 ===
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            old_mem_text = rag_manager.get_relevant_memories(user_input, n_results=6)

            dynamic_info = f"""
[Environment]
Current Time: {current_time}

Related Past Memories:
{old_mem_text if old_mem_text else "None"}
"""

            # === 組裝 messages（System 只放一次）===
            messages = [
                {'role': 'system', 'content': BASE_SYSTEM_PROMPT}
            ] + short_hist + [
                {'role': 'user', 'content': user_input + "\n\n" + dynamic_info}
            ]

            # === 處理本次對話 ===
            ai_final = process_conversation(messages, short_hist, user_input)

            print(f"\nAI: {ai_final}\n")

        except KeyboardInterrupt:
            print("\n\nProgram interrupted.")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print("An error occurred. Please try again.")

    logger.info("=== AI Assistant Shutdown ===")


def process_conversation(messages, short_hist, user_input):
    """處理單次對話（包含 tool calling）"""
    max_steps = 10
    step = 0

    while step < max_steps:
        step += 1
        response = ollama.chat(model=MODEL_NAME, messages=messages)
        ai_raw = response['message']['content']

        messages.append({'role': 'assistant', 'content': ai_raw})

        parsed = tools.get_json_from_ai(ai_raw)
        
        if parsed:
            tool_results = execute_tools(parsed)
            if tool_results:
                combined = "\n\n".join(tool_results)
                messages.append({
                    'role': 'user',
                    'content': f"TOOL RESULTS:\n{combined}\n\nNow, based on these results, give me the final answer in normal text."
                })
                continue
        else:
            ai_final = ai_raw
            break
    else:
        ai_final = "Reached maximum step limit, final response is as follows:\n" + ai_raw

    # 儲存對話
    _save_conversation(short_hist, user_input, ai_final)
    
    return ai_final


def execute_tools(tool_calls):
    """執行工具"""
    if not isinstance(tool_calls, list):
        tool_calls = [tool_calls]

    tool_results = []
    
    for call in tool_calls:
        tool_name = call.get("tool")
        args = call.get("arguments", {})

        if tool_name == "web_search":
            url = args.get("url", "")
            if url:
                print(f"🔍 Searching: {url} ...")
                result = tools.web_search(url, args.get("params"))
                tool_results.append(f"=== web_search result ===\n{result}")

        elif tool_name == "python_sandbox":
            code = args.get("code", "")
            if code:
                print(f"🐍 Running Python sandbox...")
                result = tools.python_sandbox(code)
                tool_results.append(f"=== python_sandbox result ===\n{result}")

    return tool_results


def _save_conversation(short_hist, user_input, ai_final):
    """儲存對話到 short_hist 和 RAG"""
    if not tools.get_json_from_ai(ai_final):
        short_hist.append({'role': 'user', 'content': user_input})
        short_hist.append({'role': 'assistant', 'content': ai_final})

        # 限制 short-term 記憶長度
        if len(short_hist) > 16:
            short_hist[:] = short_hist[-16:]

        # 存入長期 RAG 記憶
        rag_manager.add_mem(
            text=f"User: {user_input}\nAI: {ai_final}",
            metadata={
                "type": "conversation",
                "model": MODEL_NAME,
                "user_input_preview": user_input[:120]
            }
        )
    else:
        short_hist.append({'role': 'assistant', 'content': ai_final})
        logger.warning("AI output tool call as final answer")


if __name__ == "__main__":
    main()