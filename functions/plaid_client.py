"""Thin Plaid client + KMS + webhook-verification helpers shared by the Cloud Functions.

Kept deliberately small: the heavy sync/categorization logic lives in the Cloud Run backend.
These functions only mint Link tokens, exchange public tokens, and receive webhooks.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

import plaid
from plaid.api import plaid_api
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.webhook_verification_key_get_request import WebhookVerificationKeyGetRequest

_PRODUCTS = [p.strip() for p in os.environ.get("PLAID_PRODUCTS", "transactions").split(",") if p]
_COUNTRIES = [c.strip() for c in os.environ.get("PLAID_COUNTRY_CODES", "US").split(",") if c]


def _client() -> plaid_api.PlaidApi:
    host = {
        "sandbox": plaid.Environment.Sandbox,
        "production": plaid.Environment.Production,
    }.get(os.environ.get("PLAID_ENV", "sandbox").lower(), plaid.Environment.Sandbox)
    cfg = plaid.Configuration(
        host=host,
        api_key={
            "clientId": os.environ["PLAID_CLIENT_ID"],
            "secret": os.environ["PLAID_SECRET"],
        },
    )
    return plaid_api.PlaidApi(plaid.ApiClient(cfg))


def create_link_token(uid: str) -> str:
    req = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id=uid),
        client_name="Personal Finance Assistant",
        products=[Products(p) for p in _PRODUCTS],
        country_codes=[CountryCode(c) for c in _COUNTRIES],
        language="en",
        webhook=os.environ.get("PLAID_WEBHOOK_URL", ""),
    )
    return _client().link_token_create(req).link_token


def exchange_public_token(public_token: str) -> tuple[str, str]:
    """Return (access_token, item_id)."""
    resp = _client().item_public_token_exchange(
        ItemPublicTokenExchangeRequest(public_token=public_token)
    )
    return resp.access_token, resp.item_id


# --- KMS ---
def kms_encrypt(plaintext: str) -> str:
    from google.cloud import kms

    client = kms.KeyManagementServiceClient()
    resp = client.encrypt(
        request={"name": os.environ["KMS_KEY_NAME"], "plaintext": plaintext.encode("utf-8")}
    )
    return base64.b64encode(resp.ciphertext).decode("ascii")


# --- Webhook verification (Plaid JWT, ES256) ---
def verify_webhook(body: bytes, jwt_header: str) -> bool:
    """Verify a Plaid webhook's `Plaid-Verification` JWT and that it matches the request body."""
    import jwt
    from jwt.algorithms import ECAlgorithm

    try:
        header = jwt.get_unverified_header(jwt_header)
    except Exception:
        return False
    if header.get("alg") != "ES256":
        return False

    key_dict = (
        _client()
        .webhook_verification_key_get(WebhookVerificationKeyGetRequest(key_id=header["kid"]))
        .to_dict()["key"]
    )
    public_key = ECAlgorithm.from_jwk(json.dumps(key_dict))
    try:
        claims = jwt.decode(jwt_header, public_key, algorithms=["ES256"])
    except Exception:
        return False

    # Reject stale tokens (replay protection): issued within the last 5 minutes.
    if claims.get("iat", 0) < time.time() - 5 * 60:
        return False
    expected = hashlib.sha256(body).hexdigest()
    return hmac.compare_digest(expected, claims.get("request_body_sha256", ""))
