# App workflow

How data moves through the system, as Mermaid diagrams (they render on GitHub). Grounded in the
real code — Cloud Functions in [`functions/main.py`](../functions/main.py), the sync pipeline in
[`backend/app/services/sync.py`](../backend/app/services/sync.py), and the architecture in
[`../README.md`](../README.md).

---

## 1. System overview

The clients never hold bank secrets. Cloud Functions are the thin Plaid edge; the Cloud Run
FastAPI backend does the heavy lifting; Plaid access tokens live KMS-encrypted in a
client-denied store.

```mermaid
flowchart LR
  W["Web dashboard<br/>React"]
  M["Mobile app<br/>Flutter"]

  subgraph fb["Firebase"]
    AUTH["Auth"]
    FS[("Firestore")]
    STg[("Cloud Storage")]
    FCM["FCM push"]
  end

  subgraph cf["Cloud Functions — Plaid edge"]
    EXCH["exchange_public_token<br/>(KMS-encrypt)"]
    WH["plaid_webhook"]
    RCPT["process_receipt"]
  end

  PS(["Pub/Sub<br/>plaid-sync · receipt-process"])

  subgraph cr["Cloud Run — FastAPI"]
    API["REST API"]
    SYNC["Sync + post-process<br/>normalize·categorize·dedup<br/>budgets·alerts·recurring·rollups"]
    OCR["Receipt OCR + match"]
  end

  PLAID["Plaid"]
  DOCAI["Document AI"]
  SEC[("plaid_secrets<br/>KMS-encrypted · client-denied")]

  W -->|ID token| API
  M -->|ID token| API
  W -.->|reads| FS
  M -.->|reads| FS
  W -->|Plaid Link| PLAID
  M -->|Plaid Link| PLAID
  M -->|upload receipt| STg

  PLAID -->|webhook| WH
  WH -->|enqueue| PS
  EXCH --> SEC
  EXCH -->|initial sync| PS
  PS -->|push| API
  API --> SYNC
  SYNC --> FS
  SYNC -->|read token| SEC
  SYNC <-->|/transactions/sync| PLAID
  STg -->|finalize| RCPT
  RCPT --> PS
  API --> OCR
  OCR --> DOCAI
  OCR --> FS
  SYNC -->|alerts| FCM
  FCM --> M
```

---

## 2. Connect a bank (Plaid Link → first sync)

```mermaid
sequenceDiagram
  actor U as User
  participant App as App (web/mobile)
  participant CF as Cloud Functions
  participant Plaid
  participant FS as Firestore
  participant PS as Pub/Sub
  participant API as Cloud Run

  U->>App: Tap "Add bank"
  App->>CF: create_link_token()
  CF->>Plaid: /link/token/create
  Plaid-->>App: link_token
  U->>Plaid: Complete Plaid Link
  Plaid-->>App: public_token
  App->>CF: exchange_public_token(public_token)
  CF->>Plaid: /item/public_token/exchange
  Plaid-->>CF: access_token, item_id
  CF->>FS: store KMS-encrypted token in plaid_secrets
  CF->>FS: write item metadata (users/{uid}/items)
  CF->>PS: publish plaid-sync (initial backfill)
  PS->>API: push → sync_item
  API->>Plaid: /transactions/sync
  API->>FS: upsert accounts + transactions
  Note over API: Alerts suppressed on the<br/>initial backfill
```

---

## 3. Transaction sync pipeline

Triggered by a Plaid webhook (via Pub/Sub) or a manual **Sync now**. Each `/transactions/sync`
page is normalized, categorized, deduped, and upserted; user edits survive Plaid "modified" events.

```mermaid
flowchart TD
  T["Trigger:<br/>Plaid webhook → Pub/Sub<br/>or manual Sync now"] --> P["Pull page by cursor<br/>/transactions/sync"]
  P --> N["normalize_transaction"]
  N --> C["apply_categorization<br/>user rules + Plaid PFC"]
  C --> E{"Already stored?"}
  E -->|new| D{"Initial backfill?"}
  D -->|no| DUP["Flag possible duplicate<br/>of a manual entry"]
  D -->|yes| UP["upsert transaction"]
  DUP --> UP
  E -->|modified| PRE["Preserve user fields<br/>manual category · notes · receipt"]
  PRE --> UP
  UP --> MORE{"has_more?"}
  MORE -->|yes| P
  MORE -->|no| POST["Post-process"]

  subgraph pp["Post-process — alert steps skipped on initial backfill"]
    B["Recompute budgets<br/>+ category rollups"]
    AL["Alert engine:<br/>large · foreign · new-merchant<br/>· budget · anomaly"]
    R["Detect recurring<br/>+ refresh forecast"]
    NW["Snapshot net worth"]
  end

  POST --> B --> AL --> R --> NW --> SAVE[("Firestore")]
  AL -->|notify| NOTIF["FCM push + email"]
```

---

## 4. Receipt capture → OCR → match

```mermaid
sequenceDiagram
  actor U as User
  participant M as Mobile app
  participant ST as Cloud Storage
  participant CF as process_receipt
  participant PS as Pub/Sub
  participant API as Cloud Run
  participant DAI as Document AI
  participant FS as Firestore

  U->>M: Capture receipt photo
  M->>ST: upload receipts/{uid}/{id}
  ST->>CF: object finalized (Storage trigger)
  CF->>PS: publish receipt-process
  PS->>API: push → /internal/pubsub/receipt
  API->>DAI: OCR (Expense parser)
  DAI-->>API: merchant, total, date, line items
  API->>FS: save receipt + match to a transaction
  FS-->>M: matched receipt appears
```

---

## 5. Everyday use (reads & manual actions)

Once data has landed, the apps work against the REST API (with a Firebase ID token) and read
Firestore directly:

- **Dashboard** — net worth, spending trend, category breakdown, recent activity.
- **Recategorize a transaction** → optionally saves a **rule** so future syncs auto-apply it.
- **Add a manual transaction** → runs the same dedup check against synced data.
- **Set budget caps** → spend is recomputed from the month's transactions on read.
- **Re-auth a broken bank** → guided Plaid Link in update mode (`create_update_link_token`).

```mermaid
flowchart LR
  U["User"] --> APP["App (web/mobile)"]
  APP -->|"recategorize / add txn / set caps"| API["REST API (Cloud Run)"]
  API --> FS[("Firestore")]
  APP -.->|"live reads"| FS
  API -->|"ID token verify"| AUTH["Firebase Auth"]
```

> **Security note.** Plaid access tokens are KMS-encrypted in the `plaid_secrets` collection, which
> security rules make completely inaccessible to clients; financial data is write-protected at the
> database layer; the mobile app locks behind biometrics. See [`../README.md`](../README.md).
