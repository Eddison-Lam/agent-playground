import os
import logging
from langchain_core.messages import HumanMessage, AIMessage
from src.ui.base import BaseSession

logger = logging.getLogger(__name__)

class ConversationSession(BaseSession):
    def __init__(self, agent, command_handler, rag_manager, timer_display):
        super().__init__(agent, command_handler, rag_manager, timer_display)

    async def handle_message(self, user_input: str) -> dict:
        """
        handle single message for any ui, return dict with status and output
        """
        user_input = user_input.strip()

        if user_input.lower() in self.quit_variants:
            logger.info("User exited the program.")
            return {"status": "quit", "output": "👋 Goodbye!"}

        if user_input.startswith('/'):
            if self.command_handler.handle(user_input):
                return {"status": "command_handled", "output": None}
            else:
                return {"status": "unknown_command", "output": "Unknown command. Type /help for available commands."}

        logger.info(f"User input: {user_input}")

        self.timer.start()
        result = await self.agent.ainvoke({
            "messages": [HumanMessage(content=user_input)] + self.short_hist,
            "selected_skills": [],
            "step_count": 0
        })
        elapsed = self.timer.stop()

        ai_messages = [
            msg for msg in result["messages"]
            if isinstance(msg, AIMessage)
            and not (hasattr(msg, "tool_calls") and msg.tool_calls)
        ]

        if not ai_messages:
            return {"status": "error", "output": "❌ No response from AI"}

        ai_response = ai_messages[-1].content

        self.short_hist.append(HumanMessage(content=user_input))
        self.short_hist.append(AIMessage(content=ai_response))

        max_hist = int(os.getenv("AGENT_MAX_HISTORY", "10"))
        if len(self.short_hist) > max_hist:
            self.short_hist = self.short_hist[-max_hist:]


        model_name = os.getenv("LLM_MODEL", "qwen2.5:7b") 
        self.rag_manager.add_mem(
            text=f"User: {user_input}\nAI: {ai_response}",
            metadata={
                "type": "conversation",
                "model": model_name,
                "user_input_preview": user_input[:120]
            }
        )

        return {
            "status": "success",
            "ai_response": ai_response,
            "elapsed": elapsed,
            "output": f"🤖 AI: {ai_response}\n⏱️  Response time: {elapsed:.2f}s\n"
        }
