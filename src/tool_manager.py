"""Tool Manager for handling dynamic tool execution."""
from .settings import settings
from .logger_utils import get_logger
import tools

logger = get_logger("ToolManager", subdir="main")

class ToolManager:
    def __init__(self):
        self.tool_registry = {
            "web_search": {
                "function": tools.web_search,
                "enabled": True,
                "needs_confirmation": False,
                "description": "Fetch web content from any URL (used for weather, search, etc.)"
            },
            "python_sandbox": {
                "function": tools.python_sandbox,
                "enabled": True,
                "needs_confirmation": True,
                "description": "Execute Python code in a secure sandbox"
            }
            # register more tools here as needed when expanding
        }

    def get_enabled_tools_info(self) -> str:
        """Return tool information for the AI"""
        enabled = []
        for name, info in self.tool_registry.items():
            if settings.is_enabled(name):
                enabled.append(f"- {name}: {info['description']}")
        return "\n".join(enabled) if enabled else "None"

    def execute(self, tool_name: str, arguments: dict):
        """execute tools"""
        if tool_name not in self.tool_registry:
            return f"Unknown tool: {tool_name}"

        if not settings.is_enabled(tool_name):
            return f"Tool '{tool_name}' is currently disabled."

        tool_info = self.tool_registry[tool_name]

        if tool_info.get("needs_confirmation", False):
            print(f"\n Your agent need confirmation to execute: **{tool_name}**")
            print(f"parameters: {arguments}")
            confirm = input("Allow execution? (y/n): ").strip().lower()
            if confirm != 'y':
                return f"User rejected execution of {tool_name}"

        try:
            func = tool_info["function"]
            return func(**arguments)
        except Exception as e:
            logger.error(f"Tool execution failed {tool_name}: {e}")
            return f"Tool execution error: {str(e)}"


# 全域實例
tool_manager = ToolManager()