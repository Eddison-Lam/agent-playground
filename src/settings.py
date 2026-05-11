"""Module for managing tool settings and configurations."""
from .logger_utils import get_logger

logger = get_logger("Settings", subdir="main")

class Settings:
    def __init__(self):
        self.enabled_tools = {
            "web_search": True,
            "python_sandbox": True,
        }
        
        self.require_confirmation = {
            "web_search": False,
            "python_sandbox": True,  
        }

    def set_tool(self, tool_name: str, enable: bool) -> bool:
        """Set tool enabled/disabled status"""
        if tool_name in self.enabled_tools:
            self.enabled_tools[tool_name] = enable
            status = "Enabled" if enable else "Disabled"
            logger.info(f"Tool {tool_name} set to {status}")
            return True
        return False
    
    def set_confirmation(self, tool_name: str, require: bool) -> bool:
        """Set whether a tool requires user confirmation before execution"""
        if tool_name in self.require_confirmation:
            self.require_confirmation[tool_name] = require
            logger.info(f"Confirmation for {tool_name} set to {require}")
            return True
        return False

    def is_enabled(self, tool_name: str) -> bool:
        return self.enabled_tools.get(tool_name, False)

    def needs_confirmation(self, tool_name: str) -> bool:
        return self.require_confirmation.get(tool_name, False)

    def get_all_status(self) -> dict:
        """return all tools status"""
        return self.enabled_tools.copy()

settings = Settings()