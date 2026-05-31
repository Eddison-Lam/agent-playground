"""Agent state definition for LangGraph."""
from typing import Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """Agent state."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    selected_skills: list[str]  # ✅ 存儲選中的 skills
    step_count: int