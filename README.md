# Personal Finance Assistant

A single-user personal finance assistant that automatically pulls in US bank, credit,
investment, and loan data via **Plaid**, categorizes spending, tracks monthly budgets,
detects suspicious/large transactions, and lets you log transactions + receipts on the go.

- **Web dashboard** — React (Vite) + Tailwind/shadcn + Recharts
- **Mobile app** — Flutter (Android first)
- **Backend** — Python: FastAPI on Cloud Run + Firebase Cloud Functions
- **Data/auth** — Firebase (Firestore, Auth, Storage, FCM)
- **Bank data** — Plaid (Transactions, Investments, Liabilities, Recurring)

See the full design in [`docs/plan.md`](docs/plan.md) and the data model in
[`docs/data-model.md`](docs/data-model.md).

## Repository layout

| Path | What |
|---|---|
| [`backend/`](backend/) | FastAPI service: sync worker, categorization, dedup, REST API (Cloud Run) |
| [`functions/`](functions/) | Firebase Cloud Functions (Python): Plaid Link, token exchange, webhook |
| [`infra/`](infra/) | Firestore/Storage security rules + indexes |
| [`web/`](web/) | React dashboard |
| [`mobile/`](mobile/) | Flutter app (Android-first) |
| [`docs/`](docs/) | Plan + data model + taxonomy docs |

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

Backend test suite: `cd backend && ./.venv/Scripts/python -m pytest` (84 passing + 1 emulator test
that skips without the Firestore emulator). Web: `cd web && npm run build`. Integrations that need
live cloud services (Plaid, Firestore, Document AI, Cloud Functions) are behind ports with in-memory
fakes, so the core logic is fully tested without credentials.

**Before going live:** apply for Plaid Production access, run against Plaid Sandbox first, and deploy
the Firestore indexes in [`infra/firestore.indexes.json`](infra/firestore.indexes.json).

## Money convention

All monetary amounts are stored as **signed integer minor units (cents)**, never floats.
**Negative = money leaving the account (spending/outflow); positive = money entering (income/inflow).**
This is the inverse of Plaid's raw sign convention, normalized at ingestion.
