"""Bank-data provider port. Plaid is the concrete adapter; tests use a fake.

Provider methods return raw, provider-shaped dicts (Plaid-like). The `normalize` service is the
single place that translates them into domain models, so swapping providers only touches the
adapter + normalize mapping, not the services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ProviderSyncResult:
    """Result of a cursor-based transactions sync (Plaid /transactions/sync semantics)."""

    added: list[dict[str, Any]] = field(default_factory=list)
    modified: list[dict[str, Any]] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)  # provider transaction ids
    accounts: list[dict[str, Any]] = field(default_factory=list)
    next_cursor: str = ""
    has_more: bool = False


class BankProvider(Protocol):
    def create_link_token(self, uid: str) -> str:
        """Create a Link token for the client to open Plaid Link."""
        ...

    def exchange_public_token(self, public_token: str) -> str:
        """Exchange a public token (from Link) for a long-lived access token."""

    def create_update_link_token(self, uid: str, access_token: str) -> str:
        """Create a Link token in *update mode* to re-authenticate a broken item."""

    def sync_transactions(self, access_token: str, cursor: str | None) -> ProviderSyncResult:
        """Pull added/modified/removed transactions since `cursor`. Caller loops on has_more."""

    def get_accounts(self, access_token: str) -> list[dict[str, Any]]:
        """Fetch current account balances/metadata."""

    def get_recurring(self, access_token: str) -> list[dict[str, Any]]:
        """Fetch recurring transaction streams (subscriptions/bills)."""
