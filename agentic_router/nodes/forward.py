import logging
import uuid
from typing import Dict, Any, Optional

import httpx

from ..types import AgentState

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a reusable async HTTP client
client = httpx.AsyncClient(timeout=10.0)


def build_json_rpc_payload(input_text: str, thread_id: Optional[str]) -> Dict[str, Any]:
    """Builds the JSON-RPC 2.0 payload for the A2A message/send method."""
    params = {"content": [{"type": "text", "text": input_text}]}
    if thread_id:
        params["contextId"] = thread_id

    return {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": params,
        "id": str(uuid.uuid4()),
    }


async def forward(state: AgentState) -> Dict[str, Any]:
    """
    Forwards the user's request to the discovered agent via JSON-RPC.

    Args:
        state: The current state of the graph. Must contain `input_text`,
               `assistant_id`, `host`, `port`, and optionally `thread_id`.

    Returns:
        A dictionary with the `response` and `thread_id` from the agent.
    """
    required_keys = ["input_text", "assistant_id", "host", "port"]
    if not all(key in state for key in required_keys):
        missing_keys = [key for key in required_keys if key not in state]
        raise ValueError(f"Missing required keys in state: {missing_keys}")

    host = state["host"]
    port = state["port"]
    assistant_id = state["assistant_id"]
    input_text = state["input_text"]
    thread_id = state.get("thread_id")  # thread_id is optional

    url = f"http://{host}:{port}/a2a/{assistant_id}"
    payload = build_json_rpc_payload(input_text, thread_id)
    headers = {"Accept": "application/json"}

    logger.info(f"Forwarding request to {url}")

    try:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()

        rpc_response = response.json()

        if "error" in rpc_response:
            error_info = rpc_response["error"]
            logger.error(f"Agent returned an error: {error_info}")
            raise RuntimeError(f"Agent error: {error_info.get('message', 'Unknown error')}")

        result = rpc_response.get("result", {})

        # Extract the response text
        try:
            response_text = result["artifacts"][0]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract response text from agent reply: {result}")
            raise ValueError("Invalid response structure from agent.") from e

        # Extract the new thread_id for conversation continuity
        new_thread_id = result.get("contextId")
        if not new_thread_id:
            logger.warning("No `contextId` (thread_id) returned from the agent.")

        logger.info(f"Successfully received response from agent.")

        return {
            "response": response_text,
            "thread_id": new_thread_id,
        }

    except httpx.RequestError as e:
        logger.error(f"HTTP request failed while forwarding to agent: {e}")
        raise RuntimeError(f"Could not connect to agent at {url}.") from e
    except Exception as e:
        logger.error(f"An unexpected error occurred during forwarding: {e}")
        raise