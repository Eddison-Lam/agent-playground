import os
from src.ui.base import BaseSession
from logger_utils import get_logger
logger = get_logger("UIFactory", subdir="ui")

class UIFactory:
    """Factory class to create UI sessions based on configuration."""
    
    @staticmethod
    def create_session(agent, command_handler, rag_manager, timer_display) -> BaseSession:
        ui_type = os.getenv("AGENT_UI_MODE", "cli").lower().strip()
        
        logger.info(f"UIFactory is creating session for mode: {ui_type}")
        match ui_type:
            case "cli":
                from src.ui.cli_app import ConversationSession
                return ConversationSession(agent, command_handler, rag_manager, timer_display)
            
            # extensible for other UI types, e.g. discord, web, etc.
            
            case _:
                logger.warning(f"Unknown UI mode '{ui_type}', automatic fallback to default CLI mode.")
                from src.ui.cli_app import ConversationSession
                return ConversationSession(agent, command_handler, rag_manager, timer_display)
