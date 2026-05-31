"""Base class for skills."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SkillInfo:
    """Metadata for a skill."""
    name: str
    description: str
    priority: int = 0


class BaseSkill(ABC):
    """Abstract base class for skills."""
    
    @abstractmethod
    def get_info(self) -> SkillInfo:
        """Return skill metadata."""
        pass
    
    @abstractmethod
    def get_instructions(self) -> str:
        """
        Return skill-specific instructions for the LLM.
        This will be injected into the system prompt.
        """
        pass