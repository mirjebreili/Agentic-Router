"""State definitions for the Agentic Router graph."""

from __future__ import annotations

from typing import Dict, Optional

from langgraph.graph import MessagesState


class AgentState(MessagesState, total=False):
    """State container passed between nodes in the LangGraph workflow."""

    agent_key: Optional[str]
    assistant_id: Optional[str]
    host: Optional[str]
    port: Optional[int]
    response: Optional[str]
    thread_map: Dict[str, str]
    active_thread_id: Optional[str]