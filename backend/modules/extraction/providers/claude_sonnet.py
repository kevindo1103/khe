"""ClaudeSonnetProvider — complex / handwritten documents.

Claude Sonnet 4.6 (`claude-sonnet-4-6`): $3.00 in / $15.00 out per 1M tokens.
Highest extraction quality of the three; reserved for hard scans where Gemini
Flash and Haiku both fall short.
"""

from __future__ import annotations

from ._claude import _ClaudeVisionProvider


class ClaudeSonnetProvider(_ClaudeVisionProvider):
    name = "claude_sonnet"
    model = "claude-sonnet-4-6"
    in_usd_per_mtok = 3.0
    out_usd_per_mtok = 15.0
