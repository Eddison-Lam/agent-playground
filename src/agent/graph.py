"""LangGraph workflow definition."""
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import AgentNodes
from .router import (
    route_after_agent_with_confirmation,
    route_after_agent
)
from src.logger_utils import get_logger

logger = get_logger("AgentGraph", subdir="agent")


def create_agent_graph(rag_manager, timer_display):
    """
    Flow:
    router → prepare → agent 
           → confirmation (if needed) → tools → agent → ...
           → end (if no tool call)
    """
    logger.info("Building agent graph...")
    
    nodes = AgentNodes(rag_manager, timer_display)
    
    workflow = StateGraph(AgentState)
    
    # Nodes
    workflow.add_node("router", nodes.router_node)
    workflow.add_node("prepare", nodes.prepare_node)
    workflow.add_node("agent", nodes.agent_with_tools)
    workflow.add_node("confirmation", nodes.check_confirmation_node)
    workflow.add_node("tools", nodes.execute_tools)
    
    # Edges
    workflow.set_entry_point("router")
    workflow.add_edge("router", "prepare")
    workflow.add_edge("prepare", "agent")
    
    
    # 1. Agent decision after execution
    workflow.add_conditional_edges(
        "agent",
        route_after_agent_with_confirmation,
        {
            "confirm": "confirmation",   
            "tools": "tools",           
            "end": END                 
        }
    )
    
    # 2. After Confirmation
    workflow.add_conditional_edges(
        "confirmation",
        route_after_agent,                  
        {
            "tools": "tools",               
            "end": END                      
        }
    )
    
    # After executing tools, back to agent for next step
    workflow.add_edge("tools", "agent")
    
    app = workflow.compile()
    logger.info("Agent graph compiled successfully")
    return app