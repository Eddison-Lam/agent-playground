"""Agent nodes for LangGraph workflow."""
import os
import sys
from datetime import datetime
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from .state import AgentState
from .router_agent import RouterAgent
from src.logger_utils import get_logger
from src.llm.llm_factory import get_langchain_llm
from src.tools.langchain_tools import get_langchain_tools
import src.config as config

logger = get_logger("AgentNodes", subdir="agent")


class AgentNodes:
    """Collection of agent processing nodes."""
    
    def __init__(self, rag_manager):
        """Initialize agent nodes."""
        self.llm = get_langchain_llm()
        self.rag_manager = rag_manager
        self.router = RouterAgent()  # ✅ 使用 RouterAgent
        logger.info("AgentNodes initialized")
    
    def router_node(self, state: AgentState) -> AgentState:
        """
        Router node: Use RouterAgent to select skills.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with selected_skills
        """
        logger.info("Running router node...")
        
        # Get last user message
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        if not user_messages:
            return {"selected_skills": []}
        
        user_input = user_messages[-1].content
        
        # Use RouterAgent to select skills
        selected_skills = self.router.select_skills(user_input)
        
        if selected_skills:
            sys.stdout.write(f"📚 Selected skills: {', '.join(selected_skills)}\n")
            sys.stdout.flush()
        
        return {"selected_skills": selected_skills}
    
    def prepare_node(self, state: AgentState) -> AgentState:
        """
        Prepare node: Build system prompt with selected skills and memories.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with system message
        """
        logger.info("Running prepare node...")
        
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        if not user_messages:
            return state
        
        last_user_input = user_messages[-1].content
        
        # Get memories
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        memories = self.rag_manager.get_relevant_memories(last_user_input, n_results=6)
        
        # Get skills instructions
        selected_skills = state.get("selected_skills", [])
        skills_instructions = self.router.get_skills_instructions(selected_skills)
        
        # Build system prompt
        system_prompt = config.build_full_prompt(
            current_time=current_time,
            memories=memories,
            skills_instructions=skills_instructions
        )
        
        # Update messages
        messages = list(state["messages"])
        if messages and isinstance(messages[0], SystemMessage):
            messages[0] = SystemMessage(content=system_prompt)
        else:
            messages.insert(0, SystemMessage(content=system_prompt))
        
        logger.info(f"Context prepared. Skills: {selected_skills}")
        
        return {"messages": messages}
    
    def agent_with_tools(self, state: AgentState) -> AgentState:
        """Agent node with dynamic tool binding."""
        tools = get_langchain_tools()
        
        logger.info(f"Agent step {state.get('step_count', 0) + 1}, tools: {[t.name for t in tools]}")
        
        llm_with_tools = self.llm.bind_tools(tools) if tools else self.llm
        
        if not tools:
            logger.warning("No tools enabled, LLM will respond without tool access")
        
        response = llm_with_tools.invoke(state["messages"])
        
        if hasattr(response, "tool_calls") and response.tool_calls:
            sys.stdout.write(f"\n🔧 Agent is calling {len(response.tool_calls)} tool(s):\n")
            for i, tc in enumerate(response.tool_calls, 1):
                tool_name = tc.get('name', 'unknown')
                tool_args = tc.get('args', {})
                
                args_preview = {}
                for key, value in tool_args.items():
                    if isinstance(value, str) and len(value) > 100:
                        args_preview[key] = value[:100] + "..."
                    else:
                        args_preview[key] = value
                
                sys.stdout.write(f"  [{i}] {tool_name}\n")
                for key, val in args_preview.items():
                    sys.stdout.write(f"      - {key}: {val}\n")
            sys.stdout.flush()
            
            logger.info(f"Agent requested {len(response.tool_calls)} tool(s):")
            for tc in response.tool_calls:
                logger.info(f"  - {tc.get('name', 'unknown')}")
        else:
            logger.info("Agent responded with text (no tool calls)")
        
        return {
            "messages": [response],
            "step_count": state.get("step_count", 0) + 1
        }
    
    def check_confirmation_node(self, state: AgentState) -> AgentState:
        """
        Check if tool calls need confirmation before execution.
        Ask user for confirmation if needed.
        """
        logger.info("Checking tool confirmation requirements...")
        
        last_message = state["messages"][-1]
        
        if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
            return state
        
        from src.tools.manager import tool_manager
        
        needs_confirm = False
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get("name")
            tool = tool_manager.registry.get(tool_name)
            
            if tool and tool.info.needs_confirmation:
                needs_confirm = True
                break
        
        if not needs_confirm:
            return state  # tool calls exist but none require confirmation, exec tool
        
        # need confirmation, ask user
        print(f"\nThe following tool(s) require confirmation: (y/n)")
        for i, tool_call in enumerate(last_message.tool_calls, 1):
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            print(f"  [{i}] {tool_name}")
            for key, val in tool_args.items():
                if isinstance(val, str) and len(val) > 100:
                    print(f"      - {key}: {str(val)[:100]}...")
                else:
                    print(f"      - {key}: {val}")
        
        confirm = input("\nAllow execution? (y/n): ").strip().lower()
        
        if confirm != 'y':
            logger.warning("User rejected tool execution")
            from langchain_core.messages import HumanMessage
            rejection_msg = HumanMessage(
                content="User rejected tool execution. Please provide answer based on available information."
            )
            return {"messages": [rejection_msg]}
        
        logger.info("User approved tool execution")
        return state

    def execute_tools(self, state: AgentState) -> AgentState:
        """Execute tools using LangGraph's ToolNode."""
        tools = get_langchain_tools()
        
        if not tools:
            logger.error("No tools available for execution!")
            return state
        
        sys.stdout.write("⚙️  Executing tools...\n")
        sys.stdout.flush()
        
        logger.info(f"Executing tools with {len(tools)} available tools")
        tool_node = ToolNode(tools)
        result = tool_node.invoke(state)
        
        sys.stdout.write("✅ Tools executed\n\n")
        sys.stdout.flush()
        
        return result