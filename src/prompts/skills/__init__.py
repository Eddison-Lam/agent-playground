"""Skill registry."""
from .base import BaseSkill
from .hong_kong_weather import HongKongWeatherSkill
from .calculator import CalculatorSkill
from .web_search_general import WebSearchGeneralSkill


# Register all available skills
_SKILLS = [
    HongKongWeatherSkill(),
    CalculatorSkill(),
    WebSearchGeneralSkill(),
]


def get_all_skills() -> list[BaseSkill]:
    """Get all registered skills."""
    return _SKILLS


__all__ = [
    "BaseSkill",
    "get_all_skills",
]