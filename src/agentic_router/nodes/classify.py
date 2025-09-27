"""Node that classifies input into one of the configured agents."""

from __future__ import annotations

import logging
from typing import Any, Dict

from ..types import AgentState
from .utils import extract_latest_user_message

logger = logging.getLogger(__name__)


async def classify(state: AgentState) -> Dict[str, Any]:
    """Classify the incoming request by applying simple keyword matching."""

    input_text = extract_latest_user_message(state["messages"])
    logger.info("Classifying input using keywords: '%s'", input_text)

    lower_input = input_text.lower()
    agent_key = None

    if "gitlab" in lower_input:
        agent_key = "gitlab"
    elif "jira" in lower_input:
        agent_key = "jira"

    if not agent_key:
        logger.error("No matching agent found for the input.")
        raise ValueError("No matching agent found.")

    thread_map = state.get("thread_map", {}) or {}
    active_thread_id = thread_map.get(agent_key)

    logger.info("Classified request for agent: '%s'", agent_key)
    return {"agent_key": agent_key, "active_thread_id": active_thread_id}
