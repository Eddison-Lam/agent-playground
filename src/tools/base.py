"""Base class for all tools."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum
from logger_utils import get_logger


class ToolStatus(Enum):
    """Tool execution status."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class ToolInfo:
    """Tool metadata."""
    name: str
    description: str
    enabled: bool = True
    needs_confirmation: bool = False
    timeout: int = 30
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "needs_confirmation": self.needs_confirmation,
            "timeout": self.timeout,
        }


class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    def __init__(self, info: ToolInfo):
        self.info = info
        self.logger = get_logger(info.name, subdir="tools")
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """
        Execute the tool with given arguments.
        
        Args:
            **kwargs: Tool-specific arguments
            
        Returns:
            str: Execution result or error message
        """
        pass
    
    def validate_arguments(self, **kwargs) -> tuple[bool, str]:
        """
        Validate tool arguments before execution.
        Override this in subclasses for specific validation.
        
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        return True, ""
    
    def get_info(self) -> ToolInfo:
        """Return tool metadata."""
        return self.info