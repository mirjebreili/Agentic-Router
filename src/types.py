"""Type definitions used throughout the Agentic Router graph."""

from __future__ import annotations
from typing import Dict, Optional
from pydantic import BaseModel, Field


class ToolConfig(BaseModel):
    """Pydantic model for a single agent's configuration."""

    name: str = Field(..., description="The name of the agent.")
    description: str = Field(
        ...,
        description="A brief description of the agent's purpose.",
    )
    host: str = Field(
        ...,
        description=(
            "The hostname, IP address, or fully qualified base URL for the agent's service."
        ),
    )
    port: int = Field(..., description="The port number for the agent's service.")
    keywords: list[str] = Field(
        default_factory=list,
        description="List of keywords that should route requests to this agent.",
    )


class AgentsConfig(BaseModel):
    """Pydantic model for the entire agent configuration file."""

    agents: Dict[str, ToolConfig]
