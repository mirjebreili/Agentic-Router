"""Utilities for discovering a downstream assistant."""

from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from ..config import AGENTS_CONFIG
from ..types import AgentState

logger = logging.getLogger(__name__)


async def discover(state: AgentState) -> Dict[str, Any]:
    """Discover the assistant metadata for the selected agent."""
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
    logger.info("Discovering assistant_id for '%s' at %s", expected_name, url)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json={})
            response.raise_for_status()

        assistants = response.json()
        if not isinstance(assistants, list):
            raise ValueError("Invalid response format: expected a list of assistants.")

        for assistant in assistants:
            if assistant.get("name") == expected_name:
                assistant_id = assistant.get("assistant_id")
                if not assistant_id:
                    raise ValueError(
                        f"Assistant '{expected_name}' found but missing 'assistant_id'."
                    )

                logger.info("Discovered assistant_id: %s", assistant_id)
                return {
                    "assistant_id": assistant_id,
                    "host": host,
                    "port": port,
                }

        logger.error("Assistant with name '%s' not found at %s.", expected_name, url)
        raise RuntimeError(f"Discovery failed: Assistant '{expected_name}' not found.")

    except httpx.RequestError as exc:
        logger.error(
            "HTTP request failed during discovery for agent '%s': %s",
            agent_key,
            exc,
        )
        raise RuntimeError(f"Could not connect to agent '{agent_key}' at {url}.") from exc
    except Exception as exc:  # pragma: no cover - defensive re-raise for visibility
        logger.error("An unexpected error occurred during discovery: %s", exc)
        raise

