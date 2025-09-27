"""Utility helpers shared between node implementations."""

from __future__ import annotations

import logging
from typing import Iterable

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

