# main.py
from command_handler import CommandHandler
import ollama
from datetime import datetime

# 自訂模組
from logger_utils import get_logger
import rag_manager as rag
import tools
import config
from settings import settings
from tool_manager import tool_manager

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
    command_handler = CommandHandler(rag_manager)
    while True:
        try:
            user_input = input("\nUser >>> ").strip()
            
            if user_input.lower() in quit_variants:
                print("👋 Goodbye!")
                logger.info("User exited the program.")
                break

            if user_input.startswith('/'):
                if command_handler.handle(user_input):
                    continue
                else:
                    print("Unknown command. Type /help for available commands.")
                    continue

            logger.info(f"User input: {user_input}")

            # === 每次動態取得最新資訊 ===
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            old_mem_text = rag_manager.get_relevant_memories(user_input, n_results=6)

            available_tools = tool_manager.get_enabled_tools_info()

            full_system_prompt = config.build_full_prompt(
                current_time=current_time,
                available_tools=available_tools,
                memories=old_mem_text
            )

            messages = [
                {'role': 'system', 'content': full_system_prompt}
            ] + short_hist + [
                {'role': 'user', 'content': user_input}
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
    """Process conversation (including tool calling)"""
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

    # save conversation to short_hist and RAG
    _save_conversation(short_hist, user_input, ai_final)
    
    return ai_final


def execute_tools(tool_calls):
    """Execute tools using ToolManager, return list of results"""
    if not isinstance(tool_calls, list):
        tool_calls = [tool_calls]

    tool_results = []
    
    for call in tool_calls:
        tool_name = call.get("tool")
        args = call.get("arguments", {})

        result = tool_manager.execute(tool_name, args)
        tool_results.append(f"=== {tool_name} result ===\n{result}")

    return tool_results


def _save_conversation(short_hist, user_input, ai_final):
    """Save conversation to short_hist and RAG"""
    if not tools.get_json_from_ai(ai_final):
        short_hist.append({'role': 'user', 'content': user_input})
        short_hist.append({'role': 'assistant', 'content': ai_final})

        # Restrict short_hist to last 10 messages (5 turns) to avoid token explosion
        if len(short_hist) > 10:
            short_hist[:] = short_hist[-10:]

        # store to RAG
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