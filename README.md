# Personal Finance Assistant

A single-user personal finance assistant that automatically pulls in US bank, credit, investment,
and loan accounts via **Plaid**, categorizes spending, tracks monthly budgets, computes net worth,
detects large/suspicious/anomalous transactions, surfaces recurring subscriptions with a cash-flow
forecast, and lets you log transactions + receipts on the go.

- **Web dashboard** — React (Vite) + Tailwind/shadcn-style UI + Recharts
- **Mobile app** — Flutter (Android first)
- **Backend** — Python: FastAPI on Cloud Run + Firebase Cloud Functions
- **Data / auth** — Firebase (Firestore, Auth, Storage, FCM)
- **Bank data** — Plaid (Transactions, Investments, Liabilities, Recurring)
- **Receipts** — Google Document AI (Expense parser)

The Firestore data model is documented in [`docs/data-model.md`](docs/data-model.md).

## Architecture

The backend is built **hexagonally** (ports & adapters): a pure domain layer, `Protocol` ports, and
swappable adapters (real Plaid/Firestore/GCS/Document AI, plus in-memory/fake equivalents). Plaid and
the Firebase/GCP SDKs are **lazy-imported**, so the entire domain + service layer is unit-tested with
fakes and no cloud credentials.

Plaid secrets never reach a client: Cloud Functions hold the access token (KMS-encrypted in a
client-denied collection) and hand work to Cloud Run via Pub/Sub. Apps authenticate with Firebase
Auth and talk only to the REST API + Firestore.

```
 Plaid ──webhook──▶ Cloud Functions ──Pub/Sub──▶ Cloud Run (FastAPI) ───▶ Firestore
                    Link · token exchange         sync · normalize ·         (+ KMS,
                    KMS-encrypted secrets          categorize · dedup ·        Storage)
                                                   budgets · alerts ·
                                                   recurring · rollups
   React (web) / Flutter (mobile) ──Firebase Auth (ID token)──▶ REST API + Firestore reads
```

## Repository layout

| Path | What |
|---|---|
| [`backend/`](backend/) | FastAPI service (Cloud Run): Plaid sync, categorization, dedup, budgets, alerts, anomaly detection, recurring, forecast, rollups, receipts, REST API |
| [`functions/`](functions/) | Firebase Cloud Functions (Python): Plaid Link token, token exchange (KMS-encrypt), webhook → Pub/Sub, receipt OCR trigger |
| [`infra/`](infra/) | Firestore/Storage security rules + composite indexes |
| [`web/`](web/) | React (Vite) dashboard |
| [`mobile/`](mobile/) | Flutter app (Android-first) |
| [`docs/`](docs/) | Data model + taxonomy reference |
| [`.design-sync/`](.design-sync/) | Inputs for syncing the web UI components to claude.ai/design (see below) |

### Backend internals ([`backend/app/`](backend/app/))

| Layer | Contents |
|---|---|
| `domain/` | `money` (signed integer cents), `categories` (taxonomy + Plaid PFC mapping), `models` (pydantic) — pure, no I/O |
| `ports/` | `BankProvider`, `Repository`, `Notifier`, `Ocr`, `ObjectStore` protocols |
| `adapters/` | Plaid · Firestore · GCS · Document AI · FCM (real) and fake provider / in-memory repo / fakes (tests + local) |
| `services/` | `normalize`, `categorization`, `dedup`, `sync`, `budgets`, `alerts`, `anomaly`, `recurring`, `forecast`, `rollups`, `receipts` |
| `api/` | `deps` (DI + Firebase auth), `schemas`, route modules |

## Status

All seven planned phases are implemented:

| Phase | Scope | State |
|---|---|---|
| 1 | Bank sync + categorization foundation | ✅ backend, unit-tested |
| 2 | React web dashboard | ✅ builds clean |
| 3 | Budgets + alert engine (push + email) | ✅ tested |
| 4 | Recurring transactions + cash-flow forecast | ✅ tested |
| 5 | Flutter mobile app (Android-first) | ✅ authored (needs `flutter` toolchain to compile — see [mobile/README](mobile/README.md)) |
| 6 | Receipt OCR (Document AI) + transaction match | ✅ tested |
| 7 | Statistical anomaly detection | ✅ tested |

Integrations that need live cloud services (Plaid, Firestore, Document AI, Cloud Functions) are
behind ports with in-memory fakes, so the core logic is fully tested without credentials.

## Running it

Each surface has its own README with full detail; the essentials:

| Surface | Command | Notes |
|---|---|---|
| **Backend tests** | `cd backend && ./.venv/Scripts/python -m pytest` | **84 passing + 1 skipped** (the skip is a Firestore-emulator test). See [backend/README](backend/README.md) |
| **Backend (local)** | `uvicorn app.main:app --reload` with `APP_ENV=local AUTH_DISABLED=true` | In-memory repo, no GCP/Plaid needed |
| **Web** | `cd web && npm install && npm run build` (or `npm run dev`) | See [web/README](web/README.md) |
| **Functions** | `firebase deploy --only functions` | See [functions/README](functions/README.md) |
| **Mobile** | `cd mobile && flutter pub get && flutter run` | Android-first; needs the Flutter toolchain. See [mobile/README](mobile/README.md) |
| **Infra** | `firebase deploy --only firestore:indexes,firestore:rules,storage` | Rules + composite indexes in [`infra/`](infra/) |

**Before going live:** apply for Plaid Production access, run against Plaid Sandbox first, and deploy
the Firestore indexes in [`infra/firestore.indexes.json`](infra/firestore.indexes.json).

## Money convention

All monetary amounts are stored as **signed integer minor units (cents)**, never floats.
**Negative = money leaving the account (spending/outflow); positive = money entering (income/inflow).**
This is the inverse of Plaid's raw sign convention, normalized at ingestion.

## Design system → claude.ai/design

The web UI's presentational components (Button, Card, Badge, Input, Select, Progress, Spinner,
MoneyText, CategoryBadge, and the two charts) are synced to a **Claude Design** project so the design
agent can mock up on-brand finance screens with the real components. The sync inputs live in
[`.design-sync/`](.design-sync/) (config, authored previews, conventions header); re-run with the
driver command documented in [`.design-sync/NOTES.md`](.design-sync/NOTES.md). Generated build output
(`ds-bundle/`, `web/.ds-styles.css`) is git-ignored.
