"""Forward the request payload to the selected downstream agent."""
from __future__ import annotations
import json
import logging
import uuid
from typing import Any, Dict, Optional
import httpx
from ..types import AgentState
from .utils import build_service_url, extract_latest_user_message

logger = logging.getLogger(__name__)


def build_json_rpc_payload(input_text: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """Build the JSON-RPC 2.0 payload for the A2A message/send method.
    
    This matches the exact format from your curl example:
    {
        "jsonrpc": "2.0",
        "id": "req_1",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "what is the last log"}]
            },
            "messageId": "msg_1",
            "thread": {"threadId": "thread_1"}
        }
    }
    """
    return {
        "jsonrpc": "2.0",
        "id": f"req_{uuid.uuid4().hex[:8]}",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user", 
                "parts": [{"kind": "text", "text": input_text}]
            },
            "messageId": f"msg_{uuid.uuid4().hex[:8]}",
            "thread": {"threadId": thread_id or f"thread_{uuid.uuid4().hex[:8]}"}
        }
    }


def extract_response_text(rpc_response: Dict[str, Any]) -> tuple[str, Optional[str]]:
    """Extract the response text and context ID from the JSON-RPC response.
    
    Based on your response example, the structure is:
    {
        "jsonrpc": "2.0",
        "id": "req_1", 
        "result": {
            "id": "019993de-8dc6-7010-b839-687b2cff00c2",
            "contextId": "811bb44e-12d1-42e5-bd81-a9a420f5a7b6",
            "history": [...],
            "artifacts": [
                {
                    "artifactId": "3b87b0d1-a84b-4796-9cac-166030b87f25",
                    "name": "Assistant Response", 
                    "description": "Response from assistant 2079500c-239a-542d-bd16-796a31a400c2",
                    "parts": [{"kind": "text", "text": "The actual response text..."}]
                }
            ]
        }
    }
    """
    # Handle JSON-RPC error response
    if "error" in rpc_response:
        error_info = rpc_response["error"]
        error_message = error_info.get("message", str(error_info))
        raise RuntimeError(f"Agent returned error: {error_message}")
    
    # Extract result
    result = rpc_response.get("result", {})
    if not result:
        raise ValueError("No result found in JSON-RPC response")
    
    # Get context ID for thread tracking
    context_id = result.get("contextId")
    
    # Extract response text from artifacts
    artifacts = result.get("artifacts", [])
    if artifacts and len(artifacts) > 0:
        # Get the first artifact (should be the assistant response)
        artifact = artifacts[0]
        parts = artifact.get("parts", [])
        if parts and len(parts) > 0:
            # Get the text from the first part
            text_part = parts[0]
            if text_part.get("kind") == "text":
                response_text = text_part.get("text", "")
                return response_text, context_id
    
    # Fallback: try to get from history (last assistant message)
    history = result.get("history", [])
    for message in reversed(history):
        if message.get("role") == "agent":  # assistant messages have role "agent"
            parts = message.get("parts", [])
            if parts and len(parts) > 0:
                text_part = parts[0] 
                if text_part.get("kind") == "text":
                    response_text = text_part.get("text", "")
                    return response_text, context_id
    
    raise ValueError("Could not extract response text from agent response")


async def forward(state: AgentState) -> Dict[str, Any]:
    """Forward the user's request to the discovered agent via JSON-RPC."""
    
    # Validate required state
    required_keys = ["assistant_id", "host", "port", "agent_key"]
    missing_keys = [key for key in required_keys if key not in state]
    if missing_keys:
        raise ValueError(f"Missing required keys in state: {missing_keys}")
    
    host = state["host"]
    port = state["port"] 
    assistant_id = state["assistant_id"]
    agent_key = state["agent_key"]
    
    # Get user input text
    input_text = extract_latest_user_message(state["messages"])
    
    # Get existing thread ID for this agent if available
    thread_map = state.get("thread_map", {}) or {}
    thread_id = thread_map.get(agent_key)
    
    # Build URL and payload
    url = build_service_url(host, port, f"/a2a/{assistant_id}")
    payload = build_json_rpc_payload(input_text, thread_id)
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    logger.info(f"Forwarding request to {url} with payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            # Check HTTP status
            response.raise_for_status()
            
            # Parse JSON response
            try:
                rpc_response = response.json()
            except json.JSONDecodeError as exc:
                logger.error(f"Agent returned non-JSON response: {response.text[:500]}")
                raise ValueError("Agent returned invalid JSON response") from exc
            
            logger.info(f"Received JSON-RPC response: {json.dumps(rpc_response, indent=2)}")
            
            # Extract response text and context
            response_text, new_context_id = extract_response_text(rpc_response)
            
            logger.info(f"Successfully extracted response: {response_text[:100]}...")
            
            # Update thread map with new context ID
            updated_thread_map = dict(thread_map)
            if new_context_id:
                updated_thread_map[agent_key] = new_context_id
                logger.info(f"Updated thread ID for agent '{agent_key}': {new_context_id}")
            
            return {
                "response": response_text,
                "thread_map": updated_thread_map,
                "active_thread_id": new_context_id
            }
            
    except httpx.RequestError as exc:
        logger.error(f"HTTP request failed: {exc}")
        raise RuntimeError(f"Could not connect to agent at {url}") from exc
    except Exception as exc:
        logger.error(f"Unexpected error during forwarding: {exc}")
        raise