"""Utilities for discovering a downstream assistant."""

from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from ..config import AGENTS_CONFIG
from ..types import AgentState
from .utils import build_service_url, fetch_assistant_id

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
    api_key = getattr(agent_config, "api_key", None)  # optional; use if your server requires it

    url = build_service_url(host, port, "/assistants/search")
    logger.info("Discovering assistant_id for '%s' at %s", expected_name, url)

    try:
        assistant_id = await fetch_assistant_id(url, expected_name, api_key=api_key, timeout=10.0)
        logger.info("Discovered assistant_id: %s", assistant_id)
        return {"assistant_id": assistant_id, "host": host, "port": port}

    except httpx.HTTPError as exc:
        logger.error("HTTP error during discovery for agent '%s': %s", agent_key, exc)
        raise RuntimeError(f"Could not reach '{agent_key}' at {url}: {exc}") from exc
    except Exception as exc:  # defensive re-raise
        logger.error("Unexpected error during discovery: %s", exc)
        raise
