"""Telegram reminder delivery service (#26 PR-B / #62).

- Lazy Bot initialization: no import-time or start-time failure if no token.
- 3x exponential backoff retry on Telegram/HTTP 5xx (CLAUDE.md bug pattern).
- Never propagates exceptions: a failed reminder is logged, not crashed.
"""
from __future__ import annotations

import asyncio
import logging
from typing import cast

from app.core.config import settings

logger = logging.getLogger(__name__)


class TelegramNotConfigured(RuntimeError):
    """Raised when Telegram token/chat id are not configured."""


class _LazyBot:
    """Wraps python-telegram-bot Bot lazily so missing env vars don't break import."""

    def __init__(self) -> None:
        self._bot: object | None = None

    def _get_bot(self):
        if self._bot is not None:
            return self._bot

        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            raise TelegramNotConfigured("TELEGRAM_BOT_TOKEN not set")

        try:
            from telegram import Bot
        except ImportError as exc:
            raise TelegramNotConfigured(f"python-telegram-bot not installed: {exc}") from exc

        self._bot = Bot(token)
        return self._bot

    async def send_message(self, chat_id: str, text: str) -> None:
        bot = self._get_bot()
        await bot.send_message(chat_id=chat_id, text=text)


_lazy_bot = _LazyBot()


def _should_retry(exc: Exception) -> tuple[bool, int]:
    """Return (retryable, sleep_seconds) for Telegram/HTTP errors.

    python-telegram-bot wraps transport errors in telegram.error.* classes.
    RetryAfter carries the server's suggested retry interval.
    """
    try:
        from telegram.error import NetworkError, RetryAfter, TimedOut
    except ImportError:
        return False, 0

    if isinstance(exc, RetryAfter):
        return True, getattr(exc, "retry_after", 1)
    if isinstance(exc, (NetworkError, TimedOut)):
        return True, 2
    return False, 0


async def send_obligation_reminder(
    tenant_id: str,
    obligation_id: int,
    description: str,
    due_date: str | None,
    chat_id: str | None,
) -> bool:
    """Send a single obligation reminder via Telegram.

    Returns True if sent, False if delivery failed after retries.
    Returns True when chat_id is None so the caller can count it as skipped.
    Exceptions are never raised.
    """
    if not chat_id:
        logger.info("No chat_id for tenant %s; skipping reminder %s", tenant_id, obligation_id)
        return True

    text = f"📅 *Nhắc nhở hợp đồng*\n\n{description}"
    if due_date:
        text += f"\n📆 Hạn: {due_date}"

    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            await _lazy_bot.send_message(chat_id, text)
            logger.info("Sent reminder for obligation %s to tenant %s", obligation_id, tenant_id)
            return True
        except TelegramNotConfigured:
            logger.warning("Telegram not configured; skipping reminder %s", obligation_id)
            return False
        except Exception as exc:
            last_exc = exc
            retryable, sleep_seconds = _should_retry(exc)
            if retryable and attempt < 2:
                logger.warning(
                    "Telegram send failed (attempt %s) for obligation %s: %s. Retrying in %ss",
                    attempt + 1,
                    obligation_id,
                    exc,
                    sleep_seconds,
                )
                await asyncio.sleep(sleep_seconds)
            else:
                break

    logger.error(
        "Failed to send Telegram reminder for obligation %s after retries: %s",
        obligation_id,
        last_exc,
    )
    return False
