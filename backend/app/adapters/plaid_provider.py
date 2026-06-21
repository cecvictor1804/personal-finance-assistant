"""Plaid adapter implementing the BankProvider port.

`plaid-python` is imported lazily inside ``__init__`` so unit tests (which use FakeBankProvider)
don't need the SDK installed. Responses are converted to plain dicts via ``.to_dict()`` so they
match the shape the `normalize` service expects.
"""

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.ports.bank_provider import ProviderSyncResult


class PlaidProvider:
    def __init__(self, settings: Settings) -> None:
        import plaid
        from plaid.api import plaid_api

        host = {
            "sandbox": plaid.Environment.Sandbox,
            "production": plaid.Environment.Production,
        }.get(settings.plaid_env.lower(), plaid.Environment.Sandbox)

        configuration = plaid.Configuration(
            host=host,
            api_key={"clientId": settings.plaid_client_id, "secret": settings.plaid_secret},
        )
        self._client = plaid_api.PlaidApi(plaid.ApiClient(configuration))
        self._settings = settings

    def create_link_token(self, uid: str) -> str:
        from plaid.model.country_code import CountryCode
        from plaid.model.link_token_create_request import LinkTokenCreateRequest
        from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
        from plaid.model.products import Products

        req = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id=uid),
            client_name="Personal Finance Assistant",
            products=[Products(p) for p in self._settings.plaid_product_list],
            country_codes=[CountryCode(c) for c in self._settings.plaid_country_code_list],
            language="en",
        )
        return self._client.link_token_create(req).link_token

    def create_update_link_token(self, uid: str, access_token: str) -> str:
        from plaid.model.country_code import CountryCode
        from plaid.model.link_token_create_request import LinkTokenCreateRequest
        from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser

        # Update mode: pass access_token and omit products to re-authenticate a broken item.
        req = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id=uid),
            client_name="Personal Finance Assistant",
            country_codes=[CountryCode(c) for c in self._settings.plaid_country_code_list],
            language="en",
            access_token=access_token,
        )
        return self._client.link_token_create(req).link_token

    def exchange_public_token(self, public_token: str) -> str:
        from plaid.model.item_public_token_exchange_request import (
            ItemPublicTokenExchangeRequest,
        )

        req = ItemPublicTokenExchangeRequest(public_token=public_token)
        return self._client.item_public_token_exchange(req).access_token

    def sync_transactions(self, access_token: str, cursor: str | None) -> ProviderSyncResult:
        from plaid.model.transactions_sync_request import TransactionsSyncRequest

        kwargs: dict[str, Any] = {"access_token": access_token}
        if cursor:
            kwargs["cursor"] = cursor
        resp = self._client.transactions_sync(TransactionsSyncRequest(**kwargs)).to_dict()
        return ProviderSyncResult(
            added=resp.get("added", []),
            modified=resp.get("modified", []),
            removed=[r["transaction_id"] for r in resp.get("removed", [])],
            accounts=resp.get("accounts", []),
            next_cursor=resp.get("next_cursor", ""),
            has_more=resp.get("has_more", False),
        )

    def get_accounts(self, access_token: str) -> list[dict[str, Any]]:
        from plaid.model.accounts_get_request import AccountsGetRequest

        resp = self._client.accounts_get(AccountsGetRequest(access_token=access_token)).to_dict()
        return resp.get("accounts", [])

    def get_recurring(self, access_token: str) -> list[dict[str, Any]]:
        from plaid.model.transactions_recurring_get_request import (
            TransactionsRecurringGetRequest,
        )

        resp = self._client.transactions_recurring_get(
            TransactionsRecurringGetRequest(access_token=access_token)
        ).to_dict()
        # Tag each stream with its flow direction (lost once the lists are concatenated).
        outflow = resp.get("outflow_streams", [])
        inflow = resp.get("inflow_streams", [])
        for s in outflow:
            s["flow"] = "outflow"
        for s in inflow:
            s["flow"] = "inflow"
        return outflow + inflow
