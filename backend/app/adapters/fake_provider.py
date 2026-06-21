"""In-memory fake BankProvider for tests and local dev.

Returns Plaid-shaped dicts so the `normalize` service is exercised exactly as in production.
Scripted with a list of ``ProviderSyncResult`` "pages" returned in sequence per access token.
"""

from __future__ import annotations

from typing import Any

from app.ports.bank_provider import ProviderSyncResult


def plaid_txn(
    *,
    transaction_id: str,
    account_id: str = "acc_1",
    name: str = "",
    merchant_name: str | None = None,
    amount: float = 0.0,
    date: str = "2026-01-01",
    pending: bool = False,
    pfc_primary: str | None = None,
    pfc_detailed: str | None = None,
    iso_currency_code: str = "USD",
    location_country: str | None = "US",
) -> dict[str, Any]:
    """Build a Plaid-shaped transaction dict for tests/fixtures."""
    return {
        "transaction_id": transaction_id,
        "account_id": account_id,
        "name": name,
        "merchant_name": merchant_name,
        "amount": amount,
        "date": date,
        "pending": pending,
        "iso_currency_code": iso_currency_code,
        "personal_finance_category": (
            {"primary": pfc_primary, "detailed": pfc_detailed} if pfc_primary else None
        ),
        "location": {"country": location_country},
    }


def plaid_account(
    *,
    account_id: str = "acc_1",
    name: str = "Checking",
    mask: str = "0000",
    type: str = "depository",
    subtype: str = "checking",
    balance: float = 0.0,
    iso_currency_code: str = "USD",
) -> dict[str, Any]:
    return {
        "account_id": account_id,
        "name": name,
        "mask": mask,
        "type": type,
        "subtype": subtype,
        "balances": {"current": balance, "iso_currency_code": iso_currency_code},
    }


def plaid_recurring(
    *,
    stream_id: str,
    merchant_name: str = "",
    description: str = "",
    average_amount: float = 0.0,
    last_amount: float | None = None,
    frequency: str = "MONTHLY",
    flow: str = "outflow",
    last_date: str = "2026-05-01",
    is_active: bool = True,
    status: str = "MATURE",
    pfc_primary: str | None = None,
    pfc_detailed: str | None = None,
) -> dict[str, Any]:
    """Build a Plaid-shaped recurring stream dict (flow-tagged) for tests/fixtures."""
    return {
        "stream_id": stream_id,
        "merchant_name": merchant_name,
        "description": description,
        "average_amount": {"amount": average_amount, "iso_currency_code": "USD"},
        "last_amount": {"amount": average_amount if last_amount is None else last_amount,
                        "iso_currency_code": "USD"},
        "frequency": frequency,
        "flow": flow,
        "last_date": last_date,
        "is_active": is_active,
        "status": status,
        "personal_finance_category": (
            {"primary": pfc_primary, "detailed": pfc_detailed} if pfc_primary else None
        ),
    }


class FakeBankProvider:
    def __init__(
        self,
        pages: list[ProviderSyncResult] | None = None,
        accounts: list[dict[str, Any]] | None = None,
        recurring: list[dict[str, Any]] | None = None,
    ) -> None:
        self._pages = list(pages or [])
        self._accounts = accounts or []
        self._recurring = recurring or []
        self.link_tokens_created = 0
        self.update_link_tokens_created = 0

    def add_page(self, page: ProviderSyncResult) -> None:
        """Queue another sync page (used by tests that drive the API)."""
        self._pages.append(page)

    def create_link_token(self, uid: str) -> str:
        self.link_tokens_created += 1
        return f"link-sandbox-fake-{uid}"

    def exchange_public_token(self, public_token: str) -> str:
        return f"access-sandbox-fake-{public_token}"

    def create_update_link_token(self, uid: str, access_token: str) -> str:
        self.update_link_tokens_created += 1
        return f"link-sandbox-update-{uid}"

    def sync_transactions(self, access_token: str, cursor: str | None) -> ProviderSyncResult:
        if self._pages:
            return self._pages.pop(0)
        return ProviderSyncResult(next_cursor=cursor or "cursor-empty", has_more=False)

    def get_accounts(self, access_token: str) -> list[dict[str, Any]]:
        return self._accounts

    def get_recurring(self, access_token: str) -> list[dict[str, Any]]:
        return self._recurring
