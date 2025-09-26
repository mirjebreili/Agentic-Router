"""
Final formatting node for the graph's output.
"""
from router_app.types import RouterState
from router_app.services.logging import setup_logging

logger = setup_logging(__name__)


def format_output(state: RouterState) -> RouterState:
    """
    Prepares the final output of the graph.

    This node checks if an error occurred during the process. If so, it
    forwards the error. Otherwise, it presents the response text.

    Args:
        state: The final state of the graph.

    Returns:
        The cleaned-up state for the user.
    """
    if state.get("error"):
        logger.error(f"Graph execution finished with an error: {state['error']}")
        # Ensure response_text is None if there was an error
        return {**state, "response_text": None}

    logger.info("Graph execution completed successfully.")
    return state