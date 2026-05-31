# src/prompts/skills/calculator.py
from .base import BaseSkill, SkillInfo
from pathlib import Path

class CalculatorSkill(BaseSkill):
    """Skill for performing calculations."""
    
    def get_info(self) -> SkillInfo:
        return SkillInfo(
            name="calculator",
            description="Perform calculations using Python sandbox",
            priority=5
        )
    
    def get_instructions(self) -> str:
        skill_dir = Path(__file__).parent
        with open(skill_dir / "calculator.md", "r") as f:
            return f.read()