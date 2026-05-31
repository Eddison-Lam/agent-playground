"""Tool registry for dynamic tool management."""
from typing import Dict
from .base import BaseTool
from logger_utils import get_logger

logger = get_logger("ToolRegistry", subdir="tools")


class ToolRegistry:
    """Centralized tool registry."""
    
    _tools: Dict[str, BaseTool] = {}
    
    @classmethod
    def register(cls, tool: BaseTool) -> None:
        """
        Register a new tool.
        
        Args:
            tool: Tool instance to register
        """
        tool_name = tool.info.name
        if tool_name in cls._tools:
            logger.warning(f"Tool '{tool_name}' already registered, overwriting...")
        
        cls._tools[tool_name] = tool
        logger.info(f"Tool registered: {tool_name}")
    
    @classmethod
    def register_multiple(cls, tools: list[BaseTool]) -> None:
        """
        Register multiple tools at once.
        
        Args:
            tools: List of tool instances
        """
        for tool in tools:
            cls.register(tool)
    
    @classmethod
    def get(cls, tool_name: str) -> BaseTool | None:
        """
        Get tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool instance or None if not found
        """
        return cls._tools.get(tool_name)
    
    @classmethod
    def get_all(cls) -> Dict[str, BaseTool]:
        """
        Get all registered tools.
        
        Returns:
            Dictionary of all registered tools
        """
        return cls._tools.copy()
    
    @classmethod
    def get_enabled_tools(cls) -> Dict[str, BaseTool]:
        """
        Get only enabled tools.
        
        Returns:
            Dictionary of enabled tools
        """
        return {
            name: tool 
            for name, tool in cls._tools.items() 
            if tool.info.enabled
        }
    
    @classmethod
    def remove(cls, tool_name: str) -> bool:
        """
        Remove a tool from registry.
        
        Args:
            tool_name: Name of the tool to remove
            
        Returns:
            True if removed, False if not found
        """
        if tool_name in cls._tools:
            del cls._tools[tool_name]
            logger.info(f"Tool removed: {tool_name}")
            return True
        return False
    
    @classmethod
    def unregister_all(cls) -> None:
        """Clear all tools (useful for testing)."""
        cls._tools.clear()
        logger.info("All tools unregistered")
    
    @classmethod
    def list_tools(cls) -> list[str]:
        """
        Get list of all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(cls._tools.keys())