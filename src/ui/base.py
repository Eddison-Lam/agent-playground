from abc import ABC, abstractmethod

class BaseSession(ABC):
    """Abstract base class for different types of UI sessions."""

    def __init__(self, agent, command_handler, rag_manager, timer_display):
        self.agent = agent
        self.command_handler = command_handler
        self.rag_manager = rag_manager
        self.timer = timer_display
        
        self.quit_variants = {'quit', 'exit', 'q', 'qq', 'quitt', 'quir', 'quti', 'exitt', 'exi'}
        self.short_hist = []

    @abstractmethod
    async def handle_message(self, user_input: str) -> dict:
        """Handle any UI input asynchronously."""
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start the session (e.g. event loop for prompt loop)."""
        pass
