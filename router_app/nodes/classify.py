"""
Node for classifying the input and routing to the appropriate agent.
"""
from router_app.types import RouterState
from router_app.services.config import get_config
from router_app.services.logging import setup_logging

logger = setup_logging(__name__)

# Simple keyword mapping for routing. This could be externalized or made more complex.
KEYWORD_MAP = {
    "gitlab": ["gitlab", "merge request", "pipeline", "mr"],
    "jira": ["jira", "issue", "ticket", "sprint"],
}


def classify_input(state: RouterState) -> RouterState:
    """
    Classifies the input text to determine the target agent.

    This node checks the `routing.mode` from the config and applies the
    corresponding classification logic. Currently, only "keywords" mode
    is implemented.

    Args:
        state: The current state of the graph.

    Returns:
        The updated state with `target_agent_key` set, or an `error`.
    """
    config = get_config()
    input_text = state["input_text"].lower()
    target_agent_key = None

    if config.routing.mode == "keywords":
        for agent_key, keywords in KEYWORD_MAP.items():
            if any(keyword in input_text for keyword in keywords):
                target_agent_key = agent_key
                logger.info(f"Classified input to agent: '{target_agent_key}' based on keywords.")
                break
    # Placeholder for other routing modes like "llm" or "semantic"
    # elif config.routing.mode == "llm":
    #     logger.warning("LLM routing mode is not yet implemented.")
    # elif config.routing.mode == "semantic":
    #     logger.warning("Semantic routing mode is not yet implemented.")

    if not target_agent_key:
        if config.routing.default_agent:
            target_agent_key = config.routing.default_agent
            logger.info(f"No specific agent matched. Using default agent: '{target_agent_key}'.")
        else:
            error_message = "Could not classify input to any known agent."
            logger.error(error_message)
            return {**state, "error": error_message}

    return {**state, "target_agent_key": target_agent_key}