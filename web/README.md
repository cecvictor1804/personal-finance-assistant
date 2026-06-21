# Web dashboard (Phase 2)

React + Vite SPA for the finance dashboard. Auth via Firebase (Google Sign-In); data via the
FastAPI [`backend`](../backend) using React Query. Deployable to Firebase Hosting.

- **Vite + React + TypeScript**
- **Tailwind CSS** with shadcn-style hand-rolled UI primitives ([`src/components/ui`](src/components/ui))
- **Recharts** for spending trend + category breakdown
- **@tanstack/react-query** for data fetching/mutations; **firebase/auth** for Google Sign-In

## Pages

| Route | What |
|---|---|
| `/` | Dashboard: net worth, assets, this-month spend/income, 6-month spend-vs-income chart, category pie, account balances, recent transactions, budget progress |
| `/transactions` | Filter by category, inline recategorize (creates a remembered rule), manual entry, pending + possible-duplicate flags |
| `/budgets` | Set monthly category caps; per-category progress bars (green/amber/red) |
| `/recurring` | Detected subscriptions/bills + recurring income, and a 30/60-day cash-flow forecast |
| `/rules` | Create/list/delete categorization rules |
| `/alerts` | Alert feed (large/new-merchant/foreign/rapid-repeat/budget/recurring) with mark-read; header bell shows unread count |
| `/connections` | Plaid item status + guided re-link for broken connections |
| `/login` | Google Sign-In (or "local mode" when Firebase is unconfigured) |

## Run

```bash
cd web
cp .env.example .env.local        # set VITE_FIREBASE_* and VITE_API_BASE_URL
npm install
npm run dev                       # http://localhost:5173
```

For a no-Firebase local loop, run the backend with `APP_ENV=local AUTH_DISABLED=true` and leave the
`VITE_FIREBASE_*` vars blank — the app runs unauthenticated in "local mode" and talks to the backend
at `VITE_API_BASE_URL` (default `http://localhost:8000`).

## Verify

```bash
npm run build      # runs tsc -b (typecheck) then vite build
```

## Notes / next

- Reads currently use REST + light polling so the app works against both the in-memory local
  backend and Firestore in prod. **Phase 3** swaps reads to **Firestore real-time listeners** and
  adds the precomputed `rollups`/`alerts` collections the dashboard will prefer.
- Adding a *new* bank uses Plaid Link (via the Cloud Function `create_link_token` + the mobile app
  in Phase 5); the web "Reconnect" flow already mints an update-mode link token via the backend.
- Push notifications (FCM) for alerts are delivered by the backend; registering a web push token
  from the browser is wired on the backend (`POST /settings/fcm-token`) and will be hooked into the
  UI alongside the mobile app in Phase 5.
