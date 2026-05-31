# src/prompts/skills/hong_kong_weather.py
from .base import BaseSkill, SkillInfo
from pathlib import Path


class HongKongWeatherSkill(BaseSkill):
    """Skill for Hong Kong weather."""
    
    def get_info(self) -> SkillInfo:
        return SkillInfo(
            name="hong_kong_weather",
            description="Fetch real-time Hong Kong weather from HKO",
            priority=10
        )
    
    def get_instructions(self) -> str:
        # ✅ 從 markdown 檔案讀取
        return super().get_instructions()