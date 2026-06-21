"""Suspected-duplicate detection between a synced Plaid txn and prior manual entries.

Policy (per design): **flag, never auto-merge.** When an incoming Plaid transaction looks like a
manual entry the user already logged (same amount, near date, similar merchant), we set
``possible_duplicate_of`` so the UI can offer a confirm/merge action. Candidates are pre-filtered
by the repository on amount + date window + source==manual; this module adds the merchant check.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.domain.models import Transaction

DEFAULT_WINDOW_DAYS = 3
MIN_MERCHANT_SIMILARITY = 0.55


def _normalize_merchant(s: str) -> str:
    # Drop apostrophes first so possessives don't split into separate tokens
    # ("Joe's" -> "joes", not "joe s"), then collapse other punctuation to spaces.
    lowered = (s or "").lower().replace("'", "").replace("’", "")
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", lowered).split())


def merchant_similarity(a: str, b: str) -> float:
    na, nb = _normalize_merchant(a), _normalize_merchant(b)
    if not na or not nb:
        return 0.0
    if na == nb or na in nb or nb in na:
        return 1.0
    return SequenceMatcher(None, na, nb).ratio()


def find_duplicate(
    txn: Transaction,
    candidates: list[Transaction],
    *,
    min_similarity: float = MIN_MERCHANT_SIMILARITY,
) -> str | None:
    """Return the id of the best-matching manual duplicate, or None.

    Candidates are assumed already matched on amount and date window. If either merchant string is
    empty, the amount+date match alone is treated as enough to flag (conservatively, for review).
    """
    best_id: str | None = None
    best_score = 0.0
    for c in candidates:
        if c.id == txn.id:
            continue
        score = merchant_similarity(txn.merchant, c.merchant)
        if not txn.merchant or not c.merchant:
            score = max(score, min_similarity)
        if score >= min_similarity and score > best_score:
            best_id, best_score = c.id, score
    return best_id
