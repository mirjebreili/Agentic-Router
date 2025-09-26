from typing import TypedDict, Optional, Dict

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


class AgentState(TypedDict):
    """
    Represents the state of the agentic router graph.

    Attributes:
        input_text: The initial user query.
        agent_key: The key of the agent selected by the classification node (e.g., "gitlab").
        assistant_id: The unique ID of the assistant, discovered from its service.
        host: The hostname of the target agent service.
        port: The port number of the target agent service.
        thread_id: The conversation thread ID, for maintaining context.
        response: The final text response from the agent.
    """

    input_text: str
    agent_key: Optional[str]
    assistant_id: Optional[str]
    host: Optional[str]
    port: Optional[int]
    thread_id: Optional[str]
    response: Optional[str]