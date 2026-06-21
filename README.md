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
| [`web/`](web/) | React dashboard (Phase 2 — scaffolded) |
| [`mobile/`](mobile/) | Flutter app (Phase 5 — scaffolded) |
| [`docs/`](docs/) | Plan + data model + taxonomy docs |

## Status

Phase 1 (bank sync + categorization foundation) is the current focus — see
[`backend/README.md`](backend/README.md) to run it and the tests locally against Plaid Sandbox.

## Money convention

All monetary amounts are stored as **signed integer minor units (cents)**, never floats.
**Negative = money leaving the account (spending/outflow); positive = money entering (income/inflow).**
This is the inverse of Plaid's raw sign convention, normalized at ingestion.
