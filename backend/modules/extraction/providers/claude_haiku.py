"""ClaudeHaikuProvider — fallback when Gemini accuracy <90% (~300đ/doc target).

Claude Haiku 4.5 (`claude-haiku-4-5`): $1.00 in / $5.00 out per 1M tokens.
"""

from __future__ import annotations

from ._claude import _ClaudeVisionProvider


class ClaudeHaikuProvider(_ClaudeVisionProvider):
    name = "claude_haiku"
    model = "claude-haiku-4-5"
    in_usd_per_mtok = 1.0
    out_usd_per_mtok = 5.0
