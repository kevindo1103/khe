"""Shared Claude (Anthropic) vision-extraction implementation.

Used by ClaudeHaikuProvider and ClaudeSonnetProvider — same call shape, different
model id + pricing. Single `messages.parse()` call with a base64 image block and
structured output (output_format=ContractExtractionLLM) → response.parsed_output.

No `temperature` / `budget_tokens` / `effort`: those 400 or are unnecessary on
these models for deterministic-ish structured extraction. Output is small so a
non-streaming call (max_tokens=4096) stays well under SDK HTTP timeouts.
"""

from __future__ import annotations

import base64
import os
import time

from ..prompts import SYSTEM_GUARDRAIL, build_instruction
from ..schemas import ContractExtractionLLM, ExtractionResult, TokenUsage
from .base import cost_vnd, empty_result, sniff_mime, to_result


class _ClaudeVisionProvider:
    """Base for Claude vision extractors. Subclasses set name/model/pricing."""

    name: str = "claude"
    model: str = "claude-haiku-4-5"
    in_usd_per_mtok: float = 1.0
    out_usd_per_mtok: float = 5.0
    max_tokens: int = 4096

    def __init__(self, api_key: str | None = None) -> None:
        # Lazy import — keep package importable without the SDK installed.
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:  # pragma: no cover - surfaced at call sites
            raise RuntimeError(
                "anthropic SDK not installed — `pip install anthropic` to use Claude providers."
            ) from exc
        self._client = AsyncAnthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    async def extract(self, image_bytes: bytes, doc_type: str = "auto") -> ExtractionResult:
        mime = sniff_mime(image_bytes)
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        content_block = (
            {"type": "document", "source": {"type": "base64", "media_type": mime, "data": b64}}
            if mime == "application/pdf"
            else {"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}}
        )

        started = time.perf_counter()
        try:
            response = await self._client.messages.parse(
                model=self.model,
                max_tokens=self.max_tokens,
                system=SYSTEM_GUARDRAIL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            content_block,
                            {"type": "text", "text": build_instruction(doc_type)},
                        ],
                    }
                ],
                output_format=ContractExtractionLLM,
            )
        except Exception as exc:  # noqa: BLE001 - report, never fabricate
            latency_ms = (time.perf_counter() - started) * 1000
            return empty_result(
                provider=self.name,
                model=self.model,
                latency_ms=latency_ms,
                warning=f"{self.name} extract failed: {type(exc).__name__}: {exc}",
            )
        latency_ms = (time.perf_counter() - started) * 1000

        parsed = response.parsed_output
        if parsed is None:
            return empty_result(
                provider=self.name,
                model=self.model,
                latency_ms=latency_ms,
                warning=f"{self.name} returned no structured output "
                f"(stop_reason={getattr(response, 'stop_reason', '?')}).",
            )

        usage = TokenUsage(
            input_tokens=getattr(response.usage, "input_tokens", 0) or 0,
            output_tokens=getattr(response.usage, "output_tokens", 0) or 0,
        )
        return to_result(
            parsed,
            provider=self.name,
            model=self.model,
            latency_ms=latency_ms,
            usage=usage,
            cost=cost_vnd(usage, self.in_usd_per_mtok, self.out_usd_per_mtok),
        )
