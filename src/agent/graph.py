"""LangGraph workflow definition."""
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import AgentNodes
from .router import route_after_agent_with_confirmation, route_after_agent
from src.logger_utils import get_logger

logger = get_logger("AgentGraph", subdir="agent")


def create_agent_graph(rag_manager):
    """
    Create the agent workflow graph.
    
    Flow: router → prepare → agent → [tools → agent] → end
    
    Args:
        rag_manager: RAGManager instance
        
    Returns:
        Compiled LangGraph application
    """
    logger.info("Building agent graph...")
    
    # Initialize nodes with rag_manager
    nodes = AgentNodes(rag_manager)
    
    # Build graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("router", nodes.router_node)
    workflow.add_node("prepare", nodes.prepare_node)
    workflow.add_node("agent", nodes.agent_with_tools)
    workflow.add_node("confirmation", nodes.check_confirmation_node)
    workflow.add_node("tools", nodes.execute_tools)
    
    # Define edges
    workflow.set_entry_point("router")
    workflow.add_edge("router", "prepare")
    workflow.add_edge("prepare", "agent")
    workflow.add_conditional_edges(
        "agent",
        route_after_agent_with_confirmation,
        {
            "confirm": "confirmation",
            "tools": "tools",
            "end": END
        }
    )
    
    # Conditional routing after agent
    workflow.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # After tools, go back to agent
    workflow.add_edge("tools", "agent")
    
    # Compile
    app = workflow.compile()
    
    logger.info("Agent graph compiled successfully")
    return app