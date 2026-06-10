"""Concrete VisionExtractionProvider adapters.

- GeminiFlashProvider  — primary (~150đ/doc target), Gemini 2.0 Flash
- ClaudeHaikuProvider  — fallback when accuracy <90% (~300đ/doc), Claude Haiku 4.5
- ClaudeSonnetProvider — complex / handwritten docs, Claude Sonnet 4.6

Each imports its SDK lazily so this package imports without keys/SDKs present.
"""

from .gemini_flash import GeminiFlashProvider
from .claude_haiku import ClaudeHaikuProvider
from .claude_sonnet import ClaudeSonnetProvider

__all__ = [
    "GeminiFlashProvider",
    "ClaudeHaikuProvider",
    "ClaudeSonnetProvider",
]
