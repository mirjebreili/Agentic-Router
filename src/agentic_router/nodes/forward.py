"""Forward the request payload to the selected downstream agent."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

import httpx

from ..types import AgentState
from .utils import extract_latest_user_message


logger = logging.getLogger(__name__)


def build_json_rpc_payload(input_text: str, thread_id: Optional[str]) -> Dict[str, Any]:
    """Build the JSON-RPC 2.0 payload for the A2A ``message/send`` method."""
    params: Dict[str, Any] = {"content": [{"type": "text", "text": input_text}]}
    if thread_id:
        params["contextId"] = thread_id

    return {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": params,
        "id": str(uuid.uuid4()),
    }


async def forward(state: AgentState) -> Dict[str, Any]:
    """Forward the user's request to the discovered agent via JSON-RPC."""


    required_keys = ["assistant_id", "host", "port", "agent_key"]

    if not all(key in state for key in required_keys):
        missing_keys = [key for key in required_keys if key not in state]
        raise ValueError(f"Missing required keys in state: {missing_keys}")

    host = state["host"]
    port = state["port"]
    assistant_id = state["assistant_id"]
    agent_key = state["agent_key"]
    input_text = extract_latest_user_message(state["messages"])
    thread_id = state.get("active_thread_id")


    url = f"http://{host}:{port}/a2a/{assistant_id}"
    payload = build_json_rpc_payload(input_text, thread_id)
    headers = {"Accept": "application/json"}

    logger.info("Forwarding request to %s", url)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

        rpc_response = response.json()

        if "error" in rpc_response:
            error_info = rpc_response["error"]
            logger.error("Agent returned an error: %s", error_info)
            message = error_info.get("message", "Unknown error")
            raise RuntimeError(f"Agent error: {message}")

        result = rpc_response.get("result", {})

        try:
            response_text = result["artifacts"][0]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            logger.error("Failed to extract response text from agent reply: %s", result)
            raise ValueError("Invalid response structure from agent.") from exc

        new_thread_id = result.get("contextId")
        if not new_thread_id:
            logger.warning("No `contextId` (thread_id) returned from the agent.")

        logger.info("Successfully received response from agent.")

        thread_map = dict(state.get("thread_map", {}) or {})
        if new_thread_id:
            thread_map[agent_key] = new_thread_id
        elif thread_id:
            thread_map.setdefault(agent_key, thread_id)

        payload: Dict[str, Any] = {"response": response_text, "thread_map": thread_map}
        if new_thread_id:
            payload["active_thread_id"] = new_thread_id

        return payload


    except httpx.RequestError as exc:
        logger.error("HTTP request failed while forwarding to agent: %s", exc)
        raise RuntimeError(f"Could not connect to agent at {url}.") from exc
    except Exception as exc:  # pragma: no cover - defensive re-raise for visibility
        logger.error("An unexpected error occurred during forwarding: %s", exc)
        raise

