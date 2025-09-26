import logging
from typing import Dict, Any

import httpx

from ..config import AGENTS_CONFIG
from ..types import AgentState

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a reusable async HTTP client
client = httpx.AsyncClient(timeout=10.0)


async def discover(state: AgentState) -> Dict[str, Any]:
    """
    Discovers the assistant_id for the selected agent by querying its endpoint.

    Args:
        state: The current state of the graph, containing `agent_key`.

    Returns:
        A dictionary with `assistant_id`, `host`, and `port` to be merged into the state.
    """
    agent_key = state.get("agent_key")
    if not agent_key:
        raise ValueError("`agent_key` not found in state. Cannot discover agent.")

    agent_config = AGENTS_CONFIG.get(agent_key)
    if not agent_config:
        raise ValueError(f"No configuration found for agent key: '{agent_key}'")

    host = agent_config.host
    port = agent_config.port
    expected_name = agent_config.name

    url = f"http://{host}:{port}/assistants/search"
    logger.info(f"Discovering assistant_id for '{expected_name}' at {url}")

    try:
        response = await client.post(url, json={})
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes

        assistants = response.json()
        if not isinstance(assistants, list):
            raise ValueError("Invalid response format: expected a list of assistants.")

        for assistant in assistants:
            if assistant.get("name") == expected_name:
                assistant_id = assistant.get("assistant_id")
                if not assistant_id:
                    raise ValueError(f"Assistant '{expected_name}' found but missing 'assistant_id'.")

                logger.info(f"Discovered assistant_id: {assistant_id}")
                return {
                    "assistant_id": assistant_id,
                    "host": host,
                    "port": port,
                }

        # If the loop completes without finding the assistant
        logger.error(f"Assistant with name '{expected_name}' not found at {url}.")
        raise RuntimeError(f"Discovery failed: Assistant '{expected_name}' not found.")

    except httpx.RequestError as e:
        logger.error(f"HTTP request failed during discovery for agent '{agent_key}': {e}")
        raise RuntimeError(f"Could not connect to agent '{agent_key}' at {url}.") from e
    except Exception as e:
        logger.error(f"An unexpected error occurred during discovery: {e}")
        # Re-raise to let LangGraph handle it
        raise