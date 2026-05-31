"""Routing logic for LangGraph workflow."""
import os
from typing import Literal
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from src.logger_utils import get_logger
from .state import AgentState

load_dotenv()

logger = get_logger("AgentRouter", subdir="agent")


def route_after_agent(state: AgentState) -> Literal["tools", "end"]:
    """
    Route after agent call.

    If AI wants to use tools AND step limit not reached → go to tools node
    Otherwise → end

    Args:
        state: Current agent state

    Returns:
        Next node: "tools" or "end"
    """
    max_steps = int(os.getenv("AGENT_MAX_STEPS", "10"))
    current_steps = state.get("step_count", 0)

    # Check step limit
    if current_steps >= max_steps:
        logger.warning(f"Reached max steps ({current_steps}/{max_steps}), forcing end")
        return "end"

    # Check if last message has tool calls
    last_message = state["messages"][-1]

    if isinstance(last_message, AIMessage):
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            logger.info(f"Tool calls detected (step {current_steps}/{max_steps}), routing to tools")
            return "tools"

    logger.info(f"No tool calls (step {current_steps}/{max_steps}), routing to end")
    return "end"

def route_after_agent_with_confirmation(state: AgentState) -> Literal["confirm", "tools", "end"]:
    """
    Route after agent call, considering confirmation needs.
    """
    max_steps = int(os.getenv("AGENT_MAX_STEPS", "10"))
    current_steps = state.get("step_count", 0)

    # Check step limit
    if current_steps >= max_steps:
        logger.warning(f"Reached max steps ({current_steps}/{max_steps})")
        return "end"

    # Check if last message has tool calls
    last_message = state["messages"][-1]

    if isinstance(last_message, AIMessage):
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            from src.tools.manager import tool_manager
            
            needs_confirm = False
            for tool_call in last_message.tool_calls:
                tool_name = tool_call.get("name")
                tool = tool_manager.registry.get(tool_name)
                
                if tool and tool.info.needs_confirmation:
                    needs_confirm = True
                    logger.info(f"Tool '{tool_name}' needs confirmation")
                    break
            
            if needs_confirm:
                return "confirm"
            else:
                return "tools"
    
    logger.info("No tool calls")
    return "end"