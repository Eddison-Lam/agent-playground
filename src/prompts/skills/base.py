"""Base class for skills."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import inspect


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
    
    def _load_instructions_from_md(self) -> str:
        """
        Internal method: Load instructions from corresponding .md file.
        """
        try:
            # Get the file path of the subclass
            skill_file = Path(inspect.getfile(self.__class__))
            md_file = skill_file.with_suffix('.md')
            
            with open(md_file, "r", encoding="utf-8") as f:
                return f.read().strip()
                
        except FileNotFoundError:
            return f"[{self.__class__.__name__}] Instructions file not found: {md_file.name}"
        except UnicodeDecodeError:
            with open(md_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()
                print(f"⚠️  Warning: Encoding issue in {md_file.name}")
                return content
        except Exception as e:
            return f"Error loading skill instructions: {str(e)}"
    
    def get_instructions(self) -> str:
        """
        Default implementation. Subclasses should call super() 
        if they want to extend the behavior.
        """
        return self._load_instructions_from_md()