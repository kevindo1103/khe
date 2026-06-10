"""GeminiFlashProvider — primary extractor (~150đ/doc target).

Gemini 2.0 Flash via google-genai. Single `generate_content` call with the image
inline + structured output (response_schema=ContractExtractionLLM) → response.parsed.

Pricing (Gemini 2.0 Flash, image/text): ~$0.10 in / $0.40 out per 1M tokens.
Update the constants if Google revises pricing.
"""

from __future__ import annotations

import os
import time

from ..prompts import SYSTEM_GUARDRAIL, build_instruction
from ..schemas import ContractExtractionLLM, ExtractionResult, TokenUsage
from .base import cost_vnd, empty_result, sniff_mime, to_result


class GeminiFlashProvider:
    name = "gemini_flash"
    model = "gemini-2.0-flash"
    in_usd_per_mtok = 0.10
    out_usd_per_mtok = 0.40

    def __init__(self, api_key: str | None = None) -> None:
        # Lazy import — keep package importable without the SDK installed.
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover - surfaced at call sites
            raise RuntimeError(
                "google-genai SDK not installed — `pip install google-genai` to use Gemini."
            ) from exc
        self._genai = genai
        self._client = genai.Client(
            api_key=api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        )

    async def extract(self, image_bytes: bytes, doc_type: str = "auto") -> ExtractionResult:
        from google.genai import types

        mime = sniff_mime(image_bytes)
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_GUARDRAIL,
            response_mime_type="application/json",
            response_schema=ContractExtractionLLM,
            temperature=0.0,  # deterministic extraction (Gemini still accepts this)
        )
        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type=mime),
            types.Part.from_text(text=build_instruction(doc_type)),
        ]

        started = time.perf_counter()
        try:
            response = await self._client.aio.models.generate_content(
                model=self.model, contents=contents, config=config
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

        parsed = getattr(response, "parsed", None)
        if not isinstance(parsed, ContractExtractionLLM):
            return empty_result(
                provider=self.name,
                model=self.model,
                latency_ms=latency_ms,
                warning=f"{self.name} returned no structured output.",
            )

        meta = getattr(response, "usage_metadata", None)
        usage = TokenUsage(
            input_tokens=getattr(meta, "prompt_token_count", 0) or 0,
            output_tokens=getattr(meta, "candidates_token_count", 0) or 0,
        )
        return to_result(
            parsed,
            provider=self.name,
            model=self.model,
            latency_ms=latency_ms,
            usage=usage,
            cost=cost_vnd(usage, self.in_usd_per_mtok, self.out_usd_per_mtok),
        )
