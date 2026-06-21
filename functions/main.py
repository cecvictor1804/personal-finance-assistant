"""Firebase Cloud Functions (Python) — the thin Plaid edge.

- create_link_token / create_update_link_token: callable, mint Link tokens for the client.
- exchange_public_token: callable, swaps the public token, KMS-encrypts the access token into the
  client-inaccessible `plaid_secrets` collection, writes item metadata, and kicks off the first sync.
- plaid_webhook: HTTP, verifies Plaid's JWT, then either enqueues a sync (Pub/Sub) or flags the
  item as needing re-auth.

Heavy lifting (sync/categorization/dedup) lives in the Cloud Run backend, triggered via Pub/Sub.
"""

from __future__ import annotations

import json
import os

from firebase_admin import firestore, initialize_app
from firebase_functions import https_fn, storage_fn

import plaid_client

initialize_app()

_SYNC_TOPIC = os.environ.get("PLAID_SYNC_TOPIC", "plaid-sync")
_RECEIPT_TOPIC = os.environ.get("RECEIPT_TOPIC", "receipt-process")
_PROJECT = os.environ.get("GCP_PROJECT") or os.environ.get("GCLOUD_PROJECT", "")

# Plaid webhook codes that mean "this item needs the user to re-authenticate".
_REAUTH_CODES = {"PENDING_EXPIRATION", "USER_PERMISSION_REVOKED"}


def _publish(topic_name: str, payload: dict) -> None:
    from google.cloud import pubsub_v1

    publisher = pubsub_v1.PublisherClient()
    topic = publisher.topic_path(_PROJECT, topic_name)
    publisher.publish(topic, json.dumps(payload).encode("utf-8"))


def _publish_sync(uid: str, item_id: str) -> None:
    _publish(_SYNC_TOPIC, {"uid": uid, "item_id": item_id})


def _uid_for_item(db, item_id: str) -> str | None:
    snap = db.collection("plaid_secrets").document(item_id).get()
    return snap.to_dict().get("uid") if snap.exists else None


@https_fn.on_call()
def create_link_token(req: https_fn.CallableRequest) -> dict[str, str]:
    if req.auth is None:
        raise https_fn.HttpsError(https_fn.FunctionsErrorCode.UNAUTHENTICATED, "Sign in required")
    return {"link_token": plaid_client.create_link_token(req.auth.uid)}


@https_fn.on_call()
def exchange_public_token(req: https_fn.CallableRequest) -> dict[str, str]:
    if req.auth is None:
        raise https_fn.HttpsError(https_fn.FunctionsErrorCode.UNAUTHENTICATED, "Sign in required")
    uid = req.auth.uid
    public_token = req.data.get("public_token")
    if not public_token:
        raise https_fn.HttpsError(
            https_fn.FunctionsErrorCode.INVALID_ARGUMENT, "public_token is required"
        )
    institution = req.data.get("institution") or {}

    access_token, item_id = plaid_client.exchange_public_token(public_token)
    db = firestore.client()

    # Secret store — never exposed to clients (locked by security rules).
    db.collection("plaid_secrets").document(item_id).set(
        {"uid": uid, "accessTokenEnc": plaid_client.kms_encrypt(access_token), "cursor": None}
    )
    # Client-readable item metadata.
    db.collection("users").document(uid).collection("items").document(item_id).set(
        {
            "id": item_id,
            "institution_id": institution.get("institution_id"),
            "institution_name": institution.get("name", ""),
            "status": "active",
            "products": [p.strip() for p in os.environ.get("PLAID_PRODUCTS", "").split(",") if p],
            "last_sync_at": None,
        }
    )
    _publish_sync(uid, item_id)  # initial backfill
    return {"item_id": item_id}


@https_fn.on_request()
def plaid_webhook(req: https_fn.Request) -> https_fn.Response:
    jwt_header = req.headers.get("Plaid-Verification", "")
    if not jwt_client_ok(req.data, jwt_header):
        return https_fn.Response("invalid signature", status=401)

    payload = req.get_json(silent=True) or {}
    wh_type = payload.get("webhook_type")
    wh_code = payload.get("webhook_code")
    item_id = payload.get("item_id")
    if not item_id:
        return https_fn.Response("ok", status=200)

    db = firestore.client()
    uid = _uid_for_item(db, item_id)
    if uid is None:
        return https_fn.Response("ok", status=200)  # unknown item; ack to stop retries

    # New transaction data available -> enqueue a sync on the backend.
    if wh_type == "TRANSACTIONS" and wh_code in {"SYNC_UPDATES_AVAILABLE", "DEFAULT_UPDATE"}:
        _publish_sync(uid, item_id)

    # Connection broke -> flag for guided re-link.
    needs_reauth = (
        wh_type == "ITEM"
        and (
            wh_code in _REAUTH_CODES
            or (wh_code == "ERROR" and (payload.get("error") or {}).get("error_code")
                == "ITEM_LOGIN_REQUIRED")
        )
    )
    if needs_reauth:
        db.collection("users").document(uid).collection("items").document(item_id).update(
            {"status": "needsReauth"}
        )

    return https_fn.Response("ok", status=200)


def jwt_client_ok(body: bytes, jwt_header: str) -> bool:
    """Wrapper around plaid_client.verify_webhook so it can be monkeypatched in tests."""
    if not jwt_header:
        return False
    return plaid_client.verify_webhook(body, jwt_header)


@storage_fn.on_object_finalized()
def process_receipt(event: storage_fn.CloudEvent) -> None:
    """When a receipt image lands in Storage at receipts/{uid}/{receiptId}.ext, enqueue OCR.

    The Cloud Run backend (Pub/Sub push -> /internal/pubsub/receipt) runs Document AI + matching.
    """
    data = event.data
    name = getattr(data, "name", None)
    bucket = getattr(data, "bucket", None)
    if not name or not name.startswith("receipts/"):
        return
    parts = name.split("/")
    if len(parts) < 3:
        return
    uid = parts[1]
    receipt_id = parts[-1].rsplit(".", 1)[0]
    _publish(
        _RECEIPT_TOPIC,
        {"uid": uid, "receipt_id": receipt_id, "bucket": bucket, "path": name},
    )
