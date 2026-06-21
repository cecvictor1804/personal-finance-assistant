# Cloud Functions (Plaid edge)

Thin Python Firebase Functions that hold the Plaid secret and handle the Link/webhook surface.
All heavy processing happens in the [Cloud Run backend](../backend); these functions enqueue work
via Pub/Sub.

| Function | Trigger | Purpose |
|---|---|---|
| `create_link_token` | callable | Mint a Plaid Link token for the signed-in user |
| `exchange_public_token` | callable | Swap the public token, KMS-encrypt + store the access token, write item metadata, enqueue initial sync |
| `plaid_webhook` | HTTPS | Verify Plaid's JWT, then enqueue a sync (Pub/Sub) or flag the item `needsReauth` |

## Flow

```
Client (Flutter/Web)
   │  create_link_token (callable)
   ▼
Plaid Link UI ──public_token──▶ exchange_public_token (callable)
                                   │ store KMS-encrypted token in plaid_secrets/{itemId}
                                   │ publish {uid,itemId} ─▶ Pub/Sub topic "plaid-sync"
                                   ▼
Plaid ──webhook──▶ plaid_webhook ──verify JWT──▶ publish {uid,itemId} ─▶ Pub/Sub
                                                  └─ ITEM_LOGIN_REQUIRED ─▶ items/{id}.status=needsReauth

Pub/Sub push ─▶ Cloud Run  POST /internal/pubsub/sync  (runs SyncService)
```

## Deploy

```bash
cd functions
firebase deploy --only functions
```

Required env / secrets (see `.env.example`): `PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ENV`,
`PLAID_PRODUCTS`, `PLAID_COUNTRY_CODES`, `PLAID_WEBHOOK_URL`, `KMS_KEY_NAME`, `PLAID_SYNC_TOPIC`,
`GCP_PROJECT`. Put `PLAID_SECRET` in Secret Manager, not plain config.

## Notes

- Webhook authenticity is verified via Plaid's `Plaid-Verification` JWT (ES256) and a body-hash
  comparison with 5-minute replay protection — see [`plaid_client.py`](plaid_client.py).
- The Pub/Sub push subscription should use OIDC service-account auth; the backend additionally
  checks a shared-secret `?token=` query param.
