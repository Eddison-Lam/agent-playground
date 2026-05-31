"""Main entry point for AI Assistant with LangGraph."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import os
from dotenv import load_dotenv
from src.agent.graph import create_agent_graph
from src.command_handler import CommandHandler
from src.logger_utils import get_logger
from src.timer import TimerDisplay
from src.cli_app import ConversationSession
import src.rag_manager as rag

load_dotenv()

# ====================== Initialization ======================
logger = get_logger("Main", subdir="main")
logger.info("=== AI Assistant Starting (LangGraph Mode) ===")

rag_manager = rag.RAGManager(
    db_path='./my_mem',
    collection_name='chat_hist',
    EMBED_MODEL=os.getenv("EMBED_MODEL", "nomic-embed-text")
)

command_handler = CommandHandler(rag_manager)
agent = create_agent_graph(rag_manager)
timer = TimerDisplay()
print("🤖 AI Assistant started! Enter 'quit' or 'exit' to end.\n")
print("Type /help for available commands.\n")


# ====================== Main Loop ======================
def main():
    """Main conversation loop (CMD UI Shell)."""
    # init session
    session = ConversationSession(
        agent=agent,
        command_handler=command_handler,
        rag_manager=rag_manager,
        timer_display=timer
    )

    while True:
        try:
            user_input = input("\nUser >>> ")

            res = session.handle_message(user_input)
            
            match res["status"]:
                case "quit":
                    print(res["output"])
                    break
                case "command_handled":
                    continue
                case "unknown_command":
                    print(res["output"])
                case "error":
                    print(res["output"])
                case "success":
                    print(f"\nAI >>> {res['output']}") 
                case _:
                    if res["output"]:
                        print(f"\nAI >>> {res['output']}")
                
        except KeyboardInterrupt:
            session.timer.stop()
            print("\n\nProgram interrupted.")
            break
        except Exception as e:
            session.timer.stop()
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print("An error occurred. Please try again.")

    logger.info("=== AI Assistant Shutdown ===")

if __name__ == "__main__":
    main()