"""Async V9 gateway bridge for the Computer-Use skill.

Mirrors browser/client.py exactly — same two methods (vision / chat),
same GatewayResult dataclass, same /v1/vision and /v1/chat endpoints.
All calls are tagged agent="computer" so the cost ledger attributes them
separately from the browser skill.

vision() is used by Layer 3 (screenshot → multimodal model → click coords).
chat()   is used by Layer 2b (AX tree markdown → cheap text model → action).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx


@dataclass
class GatewayResult:
    """Normalised reply from /v1/vision or /v1/chat."""
    parsed: dict | None
    text: str
    provider: str
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int


class V9Client:
    """One client, two async methods: vision() and chat()."""

    def __init__(
        self,
        base_url: str = "http://localhost:8109",
        agent: str = "computer",
        timeout: float = 120.0,
        session: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.agent = agent
        self.timeout = timeout
        self.session = session

    @staticmethod
    def _normalise(d: dict) -> GatewayResult:
        return GatewayResult(
            parsed=d.get("parsed"),
            text=d.get("text") or "",
            provider=d.get("provider", ""),
            model=d.get("model", ""),
            latency_ms=int(d.get("latency_ms") or 0),
            input_tokens=int(d.get("input_tokens") or 0),
            output_tokens=int(d.get("output_tokens") or 0),
        )

    async def vision(
        self,
        image_data_url: str,
        prompt: str,
        *,
        schema: Optional[dict] = None,
        schema_name: str = "out",
        system: Optional[str] = None,
        max_tokens: int = 512,
        session: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> GatewayResult:
        """Send a screenshot as a base64 data URL with a prompt to /v1/vision.

        The image must be a data URL: "data:image/png;base64,<b64>".
        """
        body: dict[str, Any] = {
            "image": image_data_url,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "agent": self.agent,
        }
        if schema:
            body["schema"] = schema
            body["schema_name"] = schema_name
        if system:
            body["system"] = system
        s = session or self.session
        if s:
            body["session"] = s
        if model:
            body["model"] = model
        if provider:
            body["provider"] = provider

        import asyncio as _asyncio
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            for attempt in range(4):
                r = await c.post(f"{self.base_url}/v1/vision", json=body)
                if r.is_success:
                    return self._normalise(r.json())
                if r.status_code == 503:
                    # Provider cooldown — wait a bit and retry.
                    import re as _re
                    m = _re.search(r"cooldown \((\d+\.?\d*)s\)", r.text)
                    wait = float(m.group(1)) + 0.1 if m else 2.0
                    await _asyncio.sleep(min(wait, 5.0))
                    continue
                r.raise_for_status()  # non-503 errors are fatal
            r.raise_for_status()

    async def chat(
        self,
        prompt: str,
        *,
        schema: Optional[dict] = None,
        schema_name: str = "out",
        system: Optional[str] = None,
        max_tokens: int = 512,
        session: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> GatewayResult:
        """Send a text-only prompt to /v1/chat (no image, cheaper than vision)."""
        body: dict[str, Any] = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "agent": self.agent,
        }
        if schema:
            body["response_format"] = {
                "type": "json_schema",
                "schema": schema,
                "name": schema_name,
                "strict": True,
            }
        if system:
            body["system"] = system
        s = session or self.session
        if s:
            body["session"] = s
        if model:
            body["model"] = model
        if provider:
            body["provider"] = provider

        async with httpx.AsyncClient(timeout=self.timeout) as c:
            r = await c.post(f"{self.base_url}/v1/chat", json=body)
            r.raise_for_status()
            return self._normalise(r.json())

    async def cost_by_agent(
        self,
        agent: Optional[str] = None,
        session: Optional[str] = None,
    ) -> dict:
        """Query the V9 ledger for this agent/session."""
        params: dict[str, Any] = {}
        if agent:
            params["agent"] = agent
        if session:
            params["session"] = session
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            r = await c.get(f"{self.base_url}/v1/cost/by_agent", params=params)
            r.raise_for_status()
            return r.json()
