"""Main entry point for AI Assistant with LangGraph."""
import sys
from pathlib import Path
import asyncio
import threading
import tts.tts_model as tts


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import os
from src.agent.graph import create_agent_graph
from src.command_handler import CommandHandler
from src.logger_utils import get_logger
from src.timer import TimerDisplay
from src.ui.cli_app import ConversationSession
import src.rag_manager as rag

# ====================== Initialization ======================
logger = get_logger("Main", subdir="main")
logger.info("=== AI Assistant Starting (LangGraph Mode) ===")

rag_manager = rag.RAGManager(
    db_path='./rag_mem',
    collection_name='chat_hist',
    EMBED_MODEL=os.getenv("EMBED_MODEL", "nomic-embed-text")
)

command_handler = CommandHandler(rag_manager)
timer = TimerDisplay()
agent = create_agent_graph(rag_manager, timer)
print("🤖 AI Assistant started! Enter 'quit' or 'exit' to end.\n")
print("Type /help for available commands.\n")


# ====================== Main Loop ======================
async def async_main():
    """Main conversation loop (CMD UI Shell)."""
    # init session
    session = ConversationSession(
        agent=agent,
        command_handler=command_handler,
        rag_manager=rag_manager,
        timer_display=timer
    )
    await session.start()

if __name__ == "__main__":
    tts_thread = threading.Thread(target=tts.tts_worker)
    audio_player_thread = threading.Thread(target= tts.audio_player_worker)
    tts_thread.start()
    audio_player_thread.start()
    asyncio.run(async_main())
    tts_thread.join()
    audio_player_thread.join()