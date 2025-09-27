"""Utility helpers shared between node implementations."""

from __future__ import annotations

import logging
from typing import Iterable
from urllib.parse import urlparse, urlunparse

from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)


def extract_latest_user_message(messages: Iterable[BaseMessage]) -> str:
    """Return the most recent human message content.

    The LangGraph dev UI sends conversation history as a list of LangChain
    ``BaseMessage`` objects. This helper walks the list in reverse order to
    locate the most recent human message and normalises the content to a
    single string.

    Raises:
        ValueError: If there is no human message or the content cannot be
        normalised.
    """

    for message in reversed(list(messages)):
        if message.type != "human":
            continue

        content = message.content
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts = []
            for part in content:
                if not isinstance(part, dict):
                    continue

                if part.get("type") == "text" and "text" in part:
                    text_parts.append(part["text"])

            if text_parts:
                return "\n".join(text_parts)

        logger.debug("Skipping unsupported human message content: %s", content)

    raise ValueError("No human message found in state; cannot continue workflow.")


def build_service_url(host: str, port: int, endpoint: str) -> str:
    """Return a fully qualified URL for the downstream service endpoint.

    ``host`` may be specified either as a bare hostname/IP (``example.com``) or with an
    explicit protocol prefix (``https://example.com``). When no protocol is provided the
    service defaults to HTTP. A port from the configuration is appended unless the host
    already includes one.
    """

    if not host:
        raise ValueError("Host cannot be empty.")

    host = host.strip()

    lower = host.lower()
    if lower.startswith("http:") and not lower.startswith("http://"):
        remainder = host.split(":", 1)[1].lstrip("/")
        host = f"http://{remainder}"
    elif lower.startswith("https:") and not lower.startswith("https://"):
        remainder = host.split(":", 1)[1].lstrip("/")
        host = f"https://{remainder}"
    elif lower.startswith("http//"):
        host = f"http://{host[6:].lstrip('/')}"
    elif lower.startswith("https//"):
        host = f"https://{host[7:].lstrip('/')}"
    elif lower.startswith("http://") or lower.startswith("https://"):
        scheme, remainder = host.split("://", 1)
        host = f"{scheme.lower()}://{remainder}"

    if "://" in host:
        parsed = urlparse(host)
        if not parsed.netloc:
            raise ValueError("Host must include a hostname when a protocol is provided.")
    else:
        parsed = urlparse(f"http://{host}")
        if not parsed.netloc:
            raise ValueError("Host cannot be empty.")

    scheme = parsed.scheme or "http"
    netloc = parsed.netloc
    base_path = parsed.path or ""

    tail = netloc.split(']')[-1]
    if parsed.port is None and ":" not in tail:
        netloc = f"{netloc}:{port}"

    base_segments = [segment for segment in base_path.strip("/").split("/") if segment]
    endpoint_clean = endpoint.strip()
    endpoint_segments = [segment for segment in endpoint_clean.strip("/").split("/") if segment]
    segments = base_segments + endpoint_segments

    if segments:
        path = "/" + "/".join(segments)
    else:
        path = "/" if endpoint_clean.startswith("/") or base_path.endswith("/") else ""

    return urlunparse((scheme, netloc, path, "", "", ""))

