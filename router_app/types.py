"""
Core Pydantic models and TypedDicts for the Agentic Router.
"""
from typing import TypedDict, Optional, Dict, Literal
from pydantic import BaseModel, Field
import uuid


class AgentInfo(BaseModel):
    """Resolved information for a target agent."""
    host: str
    port: int
    assistant_id: uuid.UUID


class RouterState(TypedDict):
    """The state of the LangGraph for the Agentic Router."""
    input_text: str
    target_agent_key: Optional[str]
    agent_info: Optional[AgentInfo]
    thread_id: Optional[str]
    response_text: Optional[str]
    error: Optional[str]


# Pydantic models for agents_config.yaml validation

class AgentConfig(BaseModel):
    """Configuration for a single target agent."""
    host: str = "127.0.0.1"
    port: int
    name: str = "agent"
    registry_enabled: bool = False
    assistant_id: Optional[uuid.UUID] = None


class RegistryConfig(BaseModel):
    """Configuration for the optional registry agent."""
    host: str = "127.0.0.1"
    port: int = 2026
    assistant_id: uuid.UUID


class RoutingConfig(BaseModel):
    """Configuration for routing behavior."""
    mode: Literal["keywords", "llm", "semantic"] = "keywords"
    default_agent: Optional[str] = None


class TimeoutsConfig(BaseModel):
    """Configuration for HTTP client timeouts."""
    http_seconds: int = 20


class RetriesConfig(BaseModel):
    """Configuration for retry behavior."""
    attempts: int = 2
    backoff_seconds: float = 0.5


class Config(BaseModel):
    """Top-level configuration model, mapping to agents_config.yaml."""
    agents: Dict[str, AgentConfig]
    registry: Optional[RegistryConfig] = None
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    timeouts: TimeoutsConfig = Field(default_factory=TimeoutsConfig)
    retries: RetriesConfig = Field(default_factory=RetriesConfig)