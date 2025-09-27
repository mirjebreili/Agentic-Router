"""Type definitions used throughout the Agentic Router graph."""

from __future__ import annotations
from typing import Dict, Optional
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field


class ToolConfig(BaseModel):
    """Pydantic model for a single agent's configuration."""

    name: str = Field(..., description="The name of the agent.")
    description: str = Field(..., description="A brief description of the agent's purpose.")
    host: str = Field(..., description="The hostname or IP address of the agent's service.")
    port: int = Field(..., description="The port number for the agent's service.")


class AgentsConfig(BaseModel):
    """Pydantic model for the entire agent configuration file."""

    agents: Dict[str, ToolConfig]


class AgentState(MessagesState, total=False):
    """State container passed between nodes in the LangGraph workflow."""


    agent_key: Optional[str]
    assistant_id: Optional[str]
    host: Optional[str]
    port: Optional[int]
    response: Optional[str]
    thread_map: Dict[str, str]
    active_thread_id: Optional[str]
