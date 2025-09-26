"""
Asynchronous A2A (Agent-to-Agent) client for sending JSON-RPC 2.0 messages.
"""
import httpx
import uuid
import asyncio
from typing import Optional, Dict, Any

from router_app.types import Config
from .logging import setup_logging

logger = setup_logging(__name__)


class A2AClient:
    """A client for making A2A calls to other LangGraph agents."""

    def __init__(self, config: Config):
        self._config = config
        self._http_client = httpx.AsyncClient(
            timeout=config.timeouts.http_seconds,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    async def send_message(
        self,
        host: str,
        port: int,
        assistant_id: uuid.UUID,
        text: str,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sends a 'message/send' request to a target agent.

        Args:
            host: The hostname or IP address of the target agent.
            port: The port number of the target agent.
            assistant_id: The UUID of the target assistant.
            text: The message text to send.
            thread_id: The optional thread ID for maintaining context.

        Returns:
            The JSON response from the agent as a dictionary.

        Raises:
            httpx.HTTPStatusError: If the request fails with a non-2xx status code.
            httpx.RequestError: For other network-related issues.
        """
        url = f"http://{host}:{port}/a2a/{assistant_id}"

        # Construct the JSON-RPC 2.0 payload
        params = {"message": {"role": "user", "parts": [{"kind": "text", "text": text}]}}
        if thread_id:
            params["thread"] = {"threadId": thread_id}

        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "message/send",
            "params": params,
        }

        logger.info(f"Sending A2A message to {url} with thread_id: {thread_id}")

        attempts = self._config.retries.attempts
        backoff_seconds = self._config.retries.backoff_seconds

        for attempt in range(attempts):
            try:
                response = await self._http_client.post(url, json=payload)
                response.raise_for_status()  # Raise an exception for 4xx/5xx responses
                return response.json()
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as e:
                if isinstance(e, httpx.HTTPStatusError) and e.response.status_code not in [502, 503, 504]:
                    logger.error(f"A2A request failed with non-retriable status: {e.response.status_code}")
                    raise

                logger.warning(f"A2A request failed (attempt {attempt + 1}/{attempts}): {e}")
                if attempt + 1 < attempts:
                    await asyncio.sleep(backoff_seconds)
                else:
                    logger.error("A2A request failed after all retry attempts.")
                    raise
        # This line should not be reachable, but is here for safety
        raise Exception("A2A client failed unexpectedly.")

    async def close(self):
        """Closes the underlying HTTP client."""
        await self._http_client.aclose()