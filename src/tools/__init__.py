"""Tools module initialization and default setup."""
from .manager import tool_manager
from .registry import ToolRegistry
from .base import BaseTool, ToolInfo
from .implementations.web_search import WebSearchTool
from .implementations.python_sandbox import PythonSandboxTool
from logger_utils import get_logger

logger = get_logger("ToolsInit", subdir="tools")

# Register default tools
def _init_default_tools():
    """Initialize and register default tools."""
    default_tools = [
        WebSearchTool(),
        PythonSandboxTool(),
    ]
    
    tool_manager.register_tools(default_tools)
    logger.info(f"Default tools initialized: {', '.join([t.info.name for t in default_tools])}")

# Auto-initialize on import
_init_default_tools()


__all__ = [
    "tool_manager",
    "ToolRegistry",
    "BaseTool",
    "ToolInfo",
    "WebSearchTool",
    "PythonSandboxTool",
]