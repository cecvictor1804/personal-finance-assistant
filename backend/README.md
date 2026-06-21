# Backend (FastAPI on Cloud Run)

The data/processing core: cursor-based Plaid sync, categorization (rules + PFC), suspected-duplicate
flagging, monthly budgets, the alert engine (large/new-merchant/foreign/rapid-repeat/budget) with
statistical anomaly detection, recurring-stream tracking + cash-flow forecast, Document AI receipt
OCR, precomputed rollups (spend-by-category, net worth), and the REST API the web/mobile apps call.
Plaid and Firebase SDKs are **lazy-imported**, so the whole domain + service layer is unit-tested with
in-memory fakes and no credentials.

## Layout

```
app/
  config.py            settings (env / .env)
  main.py              FastAPI app factory
  domain/              money, models, category taxonomy + PFC mapping   (pure, no I/O)
  ports/               BankProvider · Repository · Notifier · Ocr · ObjectStore interfaces
  adapters/            Plaid · Firestore · GCS · Document AI · FCM · KMS crypto (real)
                       | fake provider · in-memory repo · fakes (tests / local)
  services/            normalize · categorization · dedup · sync · budgets · alerts ·
                       anomaly · recurring · forecast · rollups · receipts
  api/                 deps (DI + auth), schemas, routers
tests/                 84 passing + 1 skipped (Firestore-emulator test) — fakes only
```

## Run the tests

```bash
cd backend
python -m venv .venv
./.venv/Scripts/python -m pip install fastapi pydantic pydantic-settings httpx pytest pytest-asyncio
./.venv/Scripts/python -m pytest
```

(Only these light deps are needed for tests; install `requirements.txt` for the full runtime.)

## Run locally (in-memory, no GCP/Plaid)

```bash
cd backend
cp .env.example .env          # set APP_ENV=local and AUTH_DISABLED=true for a no-auth in-memory run
./.venv/Scripts/python -m pip install -r requirements.txt
./.venv/Scripts/python -m uvicorn app.main:app --reload
# Docs at http://localhost:8000/docs
```

With `APP_ENV=local` the API uses the in-memory repository; with `AUTH_DISABLED=true` requests run
as `DEV_UID`. Set `APP_ENV=prod` to switch to Firestore + KMS, and unset `AUTH_DISABLED` to require
a Firebase ID token (`Authorization: Bearer <token>`).

## Key endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/transactions` | List (filter by date/category/account) |
| POST | `/transactions` | Manual entry (auto-categorized) |
| POST | `/transactions/{id}/recategorize` | Set category; optionally remember as a rule |
| GET/POST/DELETE | `/rules` | Manage categorization rules |
| GET | `/accounts` | Balances + asset/liability flags (net-worth inputs) |
| GET/PUT | `/budgets/{month}` | Read / set monthly category caps (with computed `spent`) |
| GET | `/alerts`, POST `/alerts/{id}/read` | Alert feed + mark-read |
| GET | `/recurring`, POST `/recurring/refresh` | Recurring streams + refresh |
| GET | `/forecast` | Cash-flow forecast (upcoming recurring vs. expected inflows) |
| GET | `/receipts`, POST `/receipts/{id}/attach` | Receipt list + confirm match to a transaction |
| GET/PUT | `/settings`, POST `/settings/fcm-token` | User settings + register FCM token |
| GET | `/items` | Connection status (drives the re-link UI) |
| POST | `/items/sync` | Refresh now / daily reconcile |
| POST | `/items/{id}/reauth-link-token` | Update-mode Link token for a broken connection |
| POST | `/internal/pubsub/sync` | Pub/Sub push target for the webhook pipeline |

## Sync flow

`webhook (Cloud Function) → Pub/Sub → POST /internal/pubsub/sync → SyncService.sync_item`:
pulls Plaid pages by cursor → `normalize` → `categorize` (rule → PFC → uncategorized) → flag
suspected duplicates of manual entries → upsert accounts/transactions → advance cursor. User edits
(manual category, notes, receipts) are preserved across re-syncs. Post-processing then recomputes
budgets + rollups, runs the alert engine + anomaly detector, refreshes recurring streams, and
snapshots net worth — alerts are suppressed on the initial backfill so importing history stays quiet.

## Deploy (Cloud Run)

```bash
gcloud run deploy pfa-backend --source backend --region <region> \
  --set-env-vars APP_ENV=prod,GCP_PROJECT_ID=<proj>,KMS_KEY_NAME=<key>,INTERNAL_SECRET=<secret>
```

Grant the Cloud Run service account: Firestore read/write, KMS encrypt/decrypt on the key, and
Firebase Auth token verification. Configure the `plaid-sync` Pub/Sub push subscription to target
`/internal/pubsub/sync?token=<INTERNAL_SECRET>` with OIDC auth.
