"""
Node for sending the A2A request and handling the response.
"""
from typing import Dict, Tuple
from router_app.types import RouterState
from router_app.services.config import get_config
from router_app.services.a2a_client import A2AClient
from router_app.services.logging import setup_logging

logger = setup_logging(__name__)

# In-memory store for thread IDs. Key: (host, port, assistant_id)
_thread_context: Dict[Tuple[str, int, str], str] = {}


async def a2a_send(state: RouterState) -> RouterState:
    """
    Sends the request to the resolved target agent via A2A.

    This node constructs and sends a JSON-RPC 2.0 message/send request,
    manages thread context, and processes the response.

    Args:
        state: The current state of the graph.

    Returns:
        The updated state with `response_text` and `thread_id`, or an `error`.
    """
    if state.get("error") or not state.get("agent_info"):
        return state

    config = get_config()
    agent_info = state["agent_info"]
    input_text = state["input_text"]

    # Create a key for the thread context store
    thread_key = (agent_info.host, agent_info.port, str(agent_info.assistant_id))
    thread_id = _thread_context.get(thread_key)

    a2a_client = A2AClient(config)
    try:
        response = await a2a_client.send_message(
            host=agent_info.host,
            port=agent_info.port,
            assistant_id=agent_info.assistant_id,
            text=input_text,
            thread_id=thread_id,
        )

        # Extract the response text and new thread/context ID
        result = response.get("result", {})
        response_text = result.get("artifacts", [{}])[0].get("parts", [{}])[0].get("text")
        new_thread_id = result.get("contextId")

        if not response_text:
            raise ValueError("Response from agent is missing expected text content.")

        if new_thread_id:
            _thread_context[thread_key] = new_thread_id
            logger.info(f"Updated thread_id for agent '{state['target_agent_key']}' to {new_thread_id}.")

        return {**state, "response_text": response_text, "thread_id": new_thread_id}

    except Exception as e:
        error_message = f"A2A call failed for agent '{state['target_agent_key']}': {e}"
        logger.error(error_message)
        return {**state, "error": error_message}
    finally:
        await a2a_client.close()


def reset_thread(agent_key: str):
    """
    Resets the thread for a specific agent.
    """
    config = get_config()
    if agent_key not in config.agents:
        logger.warning(f"Cannot reset thread for unknown agent: {agent_key}")
        return

    agent_config = config.agents[agent_key]
    # Note: This only works if assistant_id is statically known or has been discovered.
    if agent_config.assistant_id:
        thread_key_tuple = (agent_config.host, agent_config.port, str(agent_config.assistant_id))
        if thread_key_tuple in _thread_context:
            del _thread_context[thread_key_tuple]
            logger.info(f"Reset thread context for agent: {agent_key}")
        else:
            logger.info(f"No active thread context to reset for agent: {agent_key}")
    else:
        logger.warning(f"Cannot reset thread for agent '{agent_key}' without a known assistant_id.")