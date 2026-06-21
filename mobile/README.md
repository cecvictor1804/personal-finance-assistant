# Mobile app (Phase 5 — not yet built)

Planned stack (from the approved design):

- **Flutter**, **Android first** (iOS deferred; code kept cross-platform for a later TestFlight build)
- **Google Sign-In + biometric lock** (`local_auth`)
- **firebase_messaging** for push alerts; Firestore listeners for live data
- **plaid_flutter** for adding/re-authenticating bank connections (guided update mode)

Features: manual transaction entry, receipt capture/upload to Cloud Storage (OCR in Phase 6), live
balances/budgets/alerts. Writes go through the FastAPI [`backend`](../backend); reads via Firestore.

Scaffold to come:
```bash
flutter create mobile
```
