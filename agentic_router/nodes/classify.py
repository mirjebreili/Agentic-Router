import logging
from typing import Dict, Any

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def classify(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classifies the user input using keyword matching to determine the agent.

    Args:
        state: The current state of the graph, containing `input_text`.

    Returns:
        A dictionary with the `agent_key` to be merged into the state.

    Raises:
        ValueError: If no matching agent is found based on keywords.
    """
    input_text = state.get("input_text")
    if not input_text:
        raise ValueError("`input_text` not found in state. Cannot classify request.")

    logger.info(f"Classifying input using keywords: '{input_text}'")

    lower_input = input_text.lower()
    agent_key = None

    if "gitlab" in lower_input:
        agent_key = "gitlab"
    elif "jira" in lower_input:
        agent_key = "jira"

    if not agent_key:
        logger.error("No matching agent found for the input.")
        # Raising an exception is the standard way for a node to signal an
        # unrecoverable failure. LangGraph will halt execution and surface this error.
        raise ValueError("No matching agent found.")

    logger.info(f"Classified request for agent: '{agent_key}'")

    return {"agent_key": agent_key}