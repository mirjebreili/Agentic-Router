"""
Node for resolving the agent's connection details, including assistant_id.
"""
from router_app.types import RouterState, AgentInfo
from router_app.services.config import get_config
from router_app.services.discovery import resolve_assistant_id
from router_app.services.a2a_client import A2AClient
from router_app.services.logging import setup_logging

logger = setup_logging(__name__)


async def resolve_agent(state: RouterState) -> RouterState:
    """
    Resolves the agent's host, port, and assistant_id.

    This node uses the `target_agent_key` from the state to look up the
    agent's configuration and then uses the discovery service to find the
    assistant_id if it's not already specified.

    Args:
        state: The current state of the graph.

    Returns:
        The updated state with `agent_info` populated, or an `error`.
    """
    if state.get("error"):
        return state

    config = get_config()
    agent_key = state.get("target_agent_key")

    if not agent_key or agent_key not in config.agents:
        error_message = f"Agent key '{agent_key}' not found in configuration."
        logger.error(error_message)
        return {**state, "error": error_message}

    agent_config = config.agents[agent_key]
    a2a_client = A2AClient(config)

    try:
        assistant_id = await resolve_assistant_id(
            agent_key=agent_key,
            agent_config=agent_config,
            registry_config=config.registry,
            a2a_client=a2a_client,
        )

        agent_info = AgentInfo(
            host=agent_config.host,
            port=agent_config.port,
            assistant_id=assistant_id,
        )
        logger.info(f"Successfully resolved agent info for '{agent_key}'.")
        return {**state, "agent_info": agent_info}

    except (ValueError, Exception) as e:
        error_message = f"Failed to resolve agent '{agent_key}': {e}"
        logger.error(error_message)
        return {**state, "error": error_message}
    finally:
        await a2a_client.close()