"""Node that classifies input into one of the configured agents."""

from __future__ import annotations

import logging
from typing import Any, Dict

from ..types import AgentState

logger = logging.getLogger(__name__)


async def classify(state: AgentState) -> Dict[str, Any]:
    """Classify the incoming request by applying simple keyword matching."""
    input_text = state.get("input_text")
    if not input_text:
        raise ValueError("`input_text` not found in state. Cannot classify request.")

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

    logger.info("Classified request for agent: '%s'", agent_key)
    return {"agent_key": agent_key}
