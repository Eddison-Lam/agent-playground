"""Tool Manager for dynamic tool execution."""
from typing import Any, Dict
from .registry import ToolRegistry
from .base import BaseTool
from logger_utils import get_logger

logger = get_logger("ToolManager", subdir="main")


class ToolManager:
    """
    Manages tool registration and execution.
    
    Features:
    - Dynamic tool registration
    - User confirmation for sensitive tools
    - Comprehensive error handling
    - Tool information retrieval
    """
    
    def __init__(self):
        """Initialize ToolManager with empty registry."""
        self.registry = ToolRegistry
        logger.info("ToolManager initialized")
    
    def register_tools(self, tools: list[BaseTool]) -> None:
        """
        Register multiple tools.
        
        Args:
            tools: List of BaseTool instances to register
        """
        self.registry.register_multiple(tools)
        logger.info(f"Registered {len(tools)} tools")
    
    def get_enabled_tools_info(self) -> str:
        """
        Get formatted information about enabled tools.
        
        Returns:
            str: Formatted tool information for AI prompts
        """
        enabled_tools = self.registry.get_enabled_tools()
        
        if not enabled_tools:
            return "No tools are currently enabled"
        
        tools_info = []
        for name, tool in enabled_tools.items():
            info = tool.get_info()
            confirm_text = " (requires confirmation)" if info.needs_confirmation else ""
            tools_info.append(f"  ✓ {name}: {info.description}{confirm_text}")
        
        # Also show disabled tools
        all_tools = self.registry.get_all()
        disabled_tools = {name: tool for name, tool in all_tools.items() if not tool.info.enabled}
        
        result = "Enabled:\n" + "\n".join(tools_info)
        
        if disabled_tools:
            disabled_info = [f"  ✗ {name}" for name in disabled_tools.keys()]
            result += "\n\nDisabled:\n" + "\n".join(disabled_info)
        
        return result
    
    def get_all_tools_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed information about all registered tools.
        
        Returns:
            Dictionary containing tool metadata
        """
        result = {}
        for name, tool in self.registry.get_all().items():
            result[name] = tool.get_info().to_dict()
        return result
    
    def list_tools(self) -> list[str]:
        """
        Get list of all registered tool names.
        
        Returns:
            List of tool names
        """
        return self.registry.list_tools()
    
    def execute(self, tool_name: str, **arguments) -> str:
        """
        Execute a tool with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            **arguments: Tool-specific arguments
            
        Returns:
            str: Execution result or error message
        """
        # Check if tool exists
        tool = self.registry.get(tool_name)
        if not tool:
            error_msg = f"Unknown tool: {tool_name}"
            logger.error(error_msg)
            return error_msg
        
        # Check if tool is enabled
        if not tool.info.enabled:
            error_msg = f"Tool '{tool_name}' is currently disabled"
            logger.warning(error_msg)
            return error_msg
        
        # Request confirmation if needed
        if tool.info.needs_confirmation:
            print(f"\nAgent requires confirmation to execute: **{tool_name}**")
            print(f"Arguments: {arguments}")
            confirm = input("Allow execution? (y/n): ").strip().lower()
            if confirm != 'y':
                rejection_msg = f"User rejected execution of {tool_name}"
                logger.info(rejection_msg)
                return rejection_msg
        
        # Execute tool
        try:
            logger.info(f"Executing tool: {tool_name}")
            logger.debug(f"Arguments: {arguments}")
            result = tool.execute(**arguments)
            logger.info(f"Tool '{tool_name}' executed successfully")
            return result
        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            logger.error(f"Tool '{tool_name}' execution failed: {e}")
            return error_msg


# Global instance
tool_manager = ToolManager()