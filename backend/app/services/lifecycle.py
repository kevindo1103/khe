"""Derive lifecycle_status from document dates (#371, R8).

Auto-derived statuses: active | expiring | expired
Manual-only statuses:  settled | suspended  (sticky — not overwritten by derivation)
"""
from datetime import date

from app.services.date_parse import _OPEN_ENDED_RE, parse_date

EXPIRING_WINDOW_DAYS = 90

_MANUAL_STATUSES = frozenset({"settled", "suspended"})
_VALID_STATUSES = frozenset({"active", "expiring", "expired", "settled", "suspended"})


def is_open_ended(value: str | None) -> bool:
    """Return True if the contract_term string signals an indefinite duration."""
    if not value:
        return False
    return bool(_OPEN_ENDED_RE.search(value))


def derive_lifecycle_status(
    signing_date: str | None,
    commencement_date: str | None,
    expiry_date_str: str | None,
    contract_term: str | None,
    current_override: str | None,
) -> str | None:
    """Derive lifecycle_status from date columns + current manual override.

    Manual overrides (settled/suspended) are sticky — derivation never clears them.
    Returns None when there is insufficient date information to classify.
    """
    if current_override in _MANUAL_STATUSES:
        return current_override

    if not expiry_date_str:
        if is_open_ended(contract_term):
            return "active"
        return None

    expiry_dt = parse_date(expiry_date_str)
    if expiry_dt is None:
        return None

    expiry = expiry_dt.date()
    today = date.today()

    if today > expiry:
        return "expired"
    if (expiry - today).days <= EXPIRING_WINDOW_DAYS:
        return "expiring"
    return "active"
