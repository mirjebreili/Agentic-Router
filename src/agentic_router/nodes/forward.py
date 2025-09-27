"""Forward the request payload to the selected downstream agent."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, Optional, Tuple, List

import httpx

from ..types import AgentState
from .utils import build_service_url, extract_latest_user_message

logger = logging.getLogger(__name__)


def build_json_rpc_payload(input_text: str, thread_id: Optional[str]) -> Dict[str, Any]:
    """Build the JSON-RPC 2.0 payload for the A2A `message/send` method.

    Per LangGraph's A2A endpoint, the request must include:
      - jsonrpc: "2.0"
      - method: "message/send"
      - params.message with role + parts(kind="text", text=...)
      - optional params.thread.threadId
      - optional params.messageId
    """
    return {
        "jsonrpc": "2.0",
        "method": "message/send",
        "id": str(uuid.uuid4()),
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": input_text}],
            },
            "messageId": str(uuid.uuid4()),
            "thread": {"threadId": thread_id or ""},
        },
    }


def _first_str(*vals: Optional[str]) -> Optional[str]:
    for v in vals:
        if isinstance(v, str) and v.strip():
            return v
    return None


def _from_parts(parts: Any) -> Optional[str]:
    """Extract text from an A2A parts array."""
    if not isinstance(parts, list):
        return None
    for p in parts:
        if not isinstance(p, dict):
            continue
        # A2A canonical: {"kind": "text", "text": "..."}
        txt = p.get("text")
        if isinstance(txt, str) and txt.strip():
            return txt
        # Some variants may use {"type": "text", "text": "..."}
        if p.get("type") == "text" and isinstance(p.get("text"), str):
            return p["text"]
        # Fallback: a single "content" style key
        c = p.get("content")
        if isinstance(c, str) and c.strip():
            return c
    return None


def _extract_text_and_thread(result: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """
    Try multiple reply shapes to extract assistant text and a thread/context id.

    Known shapes:
      - result.artifacts[0].parts[0].text          (A2A example)  [docs]
      - result.artifacts[0].text
      - result.messages[-1] with role == "assistant", in .content or .parts
      - result.output_text  / result.content
      - result.choices[0].message.content          (OpenAI-style)
    Thread/context:
      - result.contextId / result.threadId
      - result.thread.threadId
      - result.context.threadId
    """
    thread_id = _first_str(
        result.get("contextId"),
        result.get("threadId"),
        (result.get("thread") or {}).get("threadId") if isinstance(result.get("thread"), dict) else None,
        (result.get("context") or {}).get("threadId") if isinstance(result.get("context"), dict) else None,
    )

    # 1) artifacts -> parts -> text
    artifacts = result.get("artifacts")
    if isinstance(artifacts, list) and artifacts:
        first = artifacts[0]
        if isinstance(first, dict):
            # parts path
            txt = _from_parts(first.get("parts"))
            if txt:
                return txt, thread_id
            # sometimes text lives directly on the artifact
            txt = first.get("text")
            if isinstance(txt, str) and txt.strip():
                return txt, thread_id

    # 2) messages array (assistant last)
    msgs = result.get("messages")
    if isinstance(msgs, list) and msgs:
        # prefer the last assistant role; otherwise last item
        candidates: List[Dict[str, Any]] = [m for m in msgs if isinstance(m, dict)]
        ass = next((m for m in reversed(candidates) if m.get("role") in ("assistant", "ai")), candidates[-1])
        if isinstance(ass, dict):
            # content could be str or list of parts
            content = ass.get("content")
            if isinstance(content, str) and content.strip():
                return content, thread_id
            txt = _from_parts(ass.get("parts"))
            if txt:
                return txt, thread_id

    # 3) flat string fields
    for key in ("output_text", "content", "text"):
        val = result.get(key)
        if isinstance(val, str) and val.strip():
            return val, thread_id

    # 4) OpenAI-style choices[]
    choices = result.get("choices")
    if isinstance(choices, list) and choices:
        choice0 = choices[0]
        if isinstance(choice0, dict):
            msg = choice0.get("message")
            if isinstance(msg, dict):
                c = msg.get("content")
                if isinstance(c, str) and c.strip():
                    return c, thread_id

    # If we reach here, we couldn't parse it.
    raise KeyError("Unrecognized result shape")


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

    # Get user's latest text; raises if messages missing/empty per your helper
    input_text = extract_latest_user_message(state["messages"])
    thread_id = state.get("active_thread_id")

    url = build_service_url(host, port, f"/a2a/{assistant_id}")
    payload = build_json_rpc_payload(input_text, thread_id)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    logger.info("Forwarding request to %s", url)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            # If server returns non-JSON, raise with body preview for easier debugging
            try:
                rpc_response = response.json()
            except json.JSONDecodeError:
                body = (await response.aread()).decode(errors="replace") if hasattr(response, "aread") else response.text
                logger.error("Non-JSON response (%s): %s", response.status_code, body[:500])
                response.raise_for_status()
                raise ValueError("Agent returned non-JSON response")

            # JSON parsed; now check HTTP status
            response.raise_for_status()

        # Handle JSON-RPC error shape
        if isinstance(rpc_response, dict) and "error" in rpc_response:
            error_info = rpc_response.get("error", {})
            logger.error("Agent returned an error: %s", error_info)
            message = error_info.get("message") or str(error_info)
            raise RuntimeError(f"Agent error: {message}")

        result = rpc_response.get("result", {}) if isinstance(rpc_response, dict) else {}
        try:
            response_text, new_thread_id = _extract_text_and_thread(result)
        except Exception as exc:
            # Log full shape once to aid debugging, then raise a clean error
            logger.error("Failed to extract response text. RPC response: %s", json.dumps(rpc_response)[:2000])
            raise ValueError("Invalid response structure from agent.") from exc

        if not new_thread_id:
            logger.warning("No thread/context id returned from the agent.")

        logger.info("Successfully received response from agent.")

        # Maintain per-agent thread map
        thread_map = dict(state.get("thread_map", {}) or {})
        if new_thread_id:
            thread_map[agent_key] = new_thread_id
        elif thread_id:
            thread_map.setdefault(agent_key, thread_id)

        out: Dict[str, Any] = {"response": response_text, "thread_map": thread_map}
        if new_thread_id:
            out["active_thread_id"] = new_thread_id

        return out

    except httpx.RequestError as exc:
        logger.error("HTTP request failed while forwarding to agent: %s", exc)
        raise RuntimeError(f"Could not connect to agent at {url}.") from exc
    except Exception as exc:  # defensive re-raise for visibility
        logger.error("An unexpected error occurred during forwarding: %s", exc)
        raise
