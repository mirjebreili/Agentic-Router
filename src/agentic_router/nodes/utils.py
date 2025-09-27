"""Utility helpers shared between node implementations."""

from __future__ import annotations

import logging
from typing import Iterable
from urllib.parse import urljoin, urlparse, urlunparse

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

    parsed = urlparse(host)

    has_protocol = parsed.scheme and "://" in host

    if has_protocol:
        netloc = parsed.netloc
        path = parsed.path

        if not netloc:
            raise ValueError("Host must include a hostname when a protocol is provided.")

        if parsed.port is None:
            tail = netloc.split("]")[-1]
            if ":" not in tail:
                netloc = f"{netloc}:{port}"

        base = urlunparse((parsed.scheme, netloc, path.rstrip("/"), "", "", ""))
    else:
        pseudo = urlparse(f"//{host}")
        netloc = pseudo.netloc or pseudo.path or host

        if not netloc:
            raise ValueError("Host cannot be empty.")

        if pseudo.port is None and ":" not in netloc.split(']')[-1]:
            # Append the configured port only when the host value does not already provide
            # one. ``split(']')[-1]`` keeps IPv6 literals intact while examining any
            # trailing ``:port`` section outside of the closing bracket.
            netloc = f"{netloc}:{port}"

        base = urlunparse(("http", netloc, "", "", "", ""))

    return urljoin(base.rstrip("/") + "/", endpoint.lstrip("/"))

