"""
Service for discovering agent assistant_ids.
"""
import httpx
import json
import uuid
from typing import Optional, Dict, Any, Tuple

from router_app.types import AgentConfig, RegistryConfig
from .a2a_client import A2AClient
from .logging import setup_logging

logger = setup_logging(__name__)

# A simple in-memory cache for discovered assistant_ids
# Key: (agent_key, host, port), Value: assistant_id
_assistant_id_cache: Dict[Tuple[str, str, int], uuid.UUID] = {}


async def resolve_assistant_id(
    agent_key: str,
    agent_config: AgentConfig,
    registry_config: Optional[RegistryConfig],
    a2a_client: A2AClient,
) -> uuid.UUID:
    """
    Resolves the assistant_id for a given agent, using cache, static config,
    or discovery mechanisms.

    Args:
        agent_key: The key of the agent from the config (e.g., "gitlab").
        agent_config: The configuration object for the target agent.
        registry_config: The configuration for the registry agent, if available.
        a2a_client: An instance of the A2A client for communication.

    Returns:
        The resolved assistant_id as a UUID.

    Raises:
        ValueError: If the assistant_id cannot be resolved.
    """
    cache_key = (agent_key, agent_config.host, agent_config.port)
    if cache_key in _assistant_id_cache:
        logger.info(f"Found cached assistant_id for agent '{agent_key}'.")
        return _assistant_id_cache[cache_key]

    if agent_config.assistant_id:
        logger.info(f"Using static assistant_id for agent '{agent_key}'.")
        _assistant_id_cache[cache_key] = agent_config.assistant_id
        return agent_config.assistant_id

    logger.info(f"No static assistant_id for '{agent_key}'. Starting discovery.")

    # First, try direct search on the agent itself
    try:
        assistant_id = await _search_on_target(agent_config)
        if assistant_id:
            logger.info(f"Discovered assistant_id for '{agent_key}' via target search.")
            _assistant_id_cache[cache_key] = assistant_id
            return assistant_id
    except Exception as e:
        logger.warning(f"Failed to discover assistant_id for '{agent_key}' via target search: {e}")

    # If that fails and registry is enabled, try the registry
    if agent_config.registry_enabled:
        if not registry_config:
            raise ValueError("Registry is enabled for agent but not configured globally.")

        logger.info(f"Attempting discovery for '{agent_key}' via registry.")
        try:
            assistant_id = await _query_registry(agent_key, registry_config, a2a_client)
            if assistant_id:
                logger.info(f"Discovered assistant_id for '{agent_key}' via registry.")
                _assistant_id_cache[cache_key] = assistant_id
                return assistant_id
        except Exception as e:
            logger.error(f"Failed to discover assistant_id for '{agent_key}' via registry: {e}")

    raise ValueError(f"Could not resolve assistant_id for agent: {agent_key}")


async def _search_on_target(agent_config: AgentConfig) -> Optional[uuid.UUID]:
    """
    Performs a POST /assistants/search on the target agent.
    """
    url = f"http://{agent_config.host}:{agent_config.port}/assistants/search"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json={}, headers={"Accept": "application/json"})
            response.raise_for_status()
            assistants = response.json()

        matches = [
            a for a in assistants
            if a.get("name") == agent_config.name and a.get("assistant_id")
        ]

        if len(matches) == 1:
            assistant_id_str = matches[0]["assistant_id"]
            return uuid.UUID(assistant_id_str)
        elif len(matches) > 1:
            logger.warning(f"Found multiple assistants named '{agent_config.name}' on {agent_config.host}. Cannot uniquely identify.")
        else:
            logger.warning(f"No assistant named '{agent_config.name}' found on {agent_config.host}.")

    except httpx.RequestError as e:
        logger.error(f"HTTP error while searching for assistant on {url}: {e}")
    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing response from {url}: {e}")

    return None


async def _query_registry(
    agent_key: str, registry_config: RegistryConfig, a2a_client: A2AClient
) -> Optional[uuid.UUID]:
    """
    Queries the registry agent to find the assistant_id for the target agent.
    """
    prompt = f"Find assistant for project: {agent_key}"
    try:
        response = await a2a_client.send_message(
            host=registry_config.host,
            port=registry_config.port,
            assistant_id=registry_config.assistant_id,
            text=prompt,
        )

        result_text = response.get("result", {}).get("artifacts", [{}])[0].get("parts", [{}])[0].get("text")
        if not result_text:
            logger.warning("Registry response did not contain expected text artifact.")
            return None

        # The response text is expected to be a JSON string
        data = json.loads(result_text)
        assistant_id_str = data.get("assistant_id")

        if not assistant_id_str:
            logger.warning("Registry JSON response missing 'assistant_id'.")
            return None

        return uuid.UUID(assistant_id_str)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from registry response: {e}")
    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing registry response or invalid UUID: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while querying the registry: {e}")

    return None


def clear_cache():
    """Clears the in-memory assistant_id cache."""
    global _assistant_id_cache
    _assistant_id_cache.clear()
    logger.info("Cleared assistant_id cache.")