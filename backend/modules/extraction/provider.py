"""The `VisionExtractionProvider` interface (DEC-002, ratified).

One method, one call: image bytes in → structured ExtractionResult out. No
separate OCR step. Implementations live in `providers/`.

Coordinate with KHE_Backend via PM BEFORE changing this Protocol (scope-lock).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .schemas import ExtractionResult


@runtime_checkable
class VisionExtractionProvider(Protocol):
    """A single-call vision extractor.

    Args (extract):
        image_bytes: raw image OR single-page PDF bytes of the document.
        doc_type: caller hint ("hd_thue_mat_bang" | "hd_nha_cung_cap" |
            "hd_lao_dong" | "auto"). "auto" lets the model classify (FR-EX-01).

    Returns:
        ExtractionResult — READ-ONLY extracted Terms + provenance/metrics.

    Implementations MUST NOT generate or alter legal content (D-06). They surface
    what is on the page, with per-field confidence + needs_review (FR-EX-05), and
    set value=None when a Term is absent (D-08 — never guess).
    """

    name: str

    async def extract(self, image_bytes: bytes, doc_type: str = "auto") -> ExtractionResult:
        ...
