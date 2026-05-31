"""Routing logic for LangGraph workflow."""
import os
from typing import Literal
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from src.logger_utils import get_logger
from .state import AgentState

load_dotenv()

logger = get_logger("AgentRouter", subdir="agent")

def route_after_agent_with_confirmation(state):
    """Determine if user confirmation is needed"""
    last_message = state["messages"][-1]
    
    if not (isinstance(last_message, AIMessage) and last_message.tool_calls):
        return "end"
    
    # check if any tool call requires confirmation
    from src.tools.manager import tool_manager
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call.get("name")
        tool = tool_manager.registry.get(tool_name)
        
        if tool and tool.info.needs_confirmation:
            return "confirm"
    
    # there are tool calls but none require confirmation → execute directly
    return "tools"


def route_after_agent(state):
    """normally called after user confirmation, determine if there are tool calls to execute"""
    last_message = state["messages"][-1]
    
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    
    logger.info("No tool calls")
    return "end"