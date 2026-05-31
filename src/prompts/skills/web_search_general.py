from .base import BaseSkill, SkillInfo
from pathlib import Path

class WebSearchGeneralSkill(BaseSkill):
    """Skill for general web searches and information fetching."""
    
    def get_info(self) -> SkillInfo:
        return SkillInfo(
            name="web_search_general",
            description="Search or fetch web content for general information",
            priority=3
        )
    
    def get_instructions(self) -> str:
        skill_dir = Path(__file__).parent
        with open(skill_dir / "web_search_general.md", "r") as f:
            return f.read()