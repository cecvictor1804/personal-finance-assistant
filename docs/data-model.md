# Firestore data model

Single-user app, but every document is scoped under `users/{uid}` and owner-locked by security
rules so the design is multi-user-ready. The backend uses the Admin SDK (bypasses rules); clients
read via Firestore listeners and write via the FastAPI REST API.

## Collections

```
users/{uid}
  profile, settings, alertThresholds, notifPrefs, fcmTokens[]

users/{uid}/items/{itemId}                 # client-readable Plaid item metadata
  institutionName, institutionId, status (active|needsReauth|error),
  lastSyncAt, products[], cursorPresent (bool — not the cursor itself)

plaid_secrets/{itemId}                      # DENIED to all clients (Admin SDK only)
  uid, accessTokenEnc (KMS-encrypted), cursor, dek (wrapped data-encryption-key)

users/{uid}/accounts/{accountId}
  plaidAccountId, name, mask, type, subtype, institutionId,
  balanceCents, currency, isAsset (bool), isLiability (bool), updatedAt

users/{uid}/transactions/{txnId}
  accountId, amountCents (signed: -=outflow), currency, date (YYYY-MM-DD),
  merchant, rawName, category, pfcPrimary, pfcDetailed, categorySource (rule|pfc|default|manual),
  source (plaid|manual), pending (bool), plaidTxnId, receiptId,
  possibleDuplicateOf (txnId|null), isTransfer (bool), notes, createdAt, updatedAt

users/{uid}/rules/{ruleId}
  matchType (contains|equals|regex), pattern, category, priority (int), createdAt

users/{uid}/budgets/{YYYY-MM}
  month, perCategory: { <category>: { capCents, spentCents } }, updatedAt

users/{uid}/recurring/{streamId}            # Plaid Recurring Transactions
  merchant, cadence, avgAmountCents, lastDate, status (mature|early|tombstoned), flow (in|out)

users/{uid}/holdings/{holdingId}            # Plaid Investments
  securityId, name, ticker, quantity, valueCents, costBasisCents

users/{uid}/liabilities/{liabilityId}       # Plaid Liabilities
  accountId, kind (credit|student|mortgage), balanceCents, aprPercent, nextPaymentDue, minPaymentCents

users/{uid}/receipts/{receiptId}            # Phase 6
  storagePath, ocrResult, matchedTxnId, status (pending|parsed|matched|error)

users/{uid}/alerts/{alertId}                # Phase 3
  type, severity, txnRef, message, read (bool), createdAt

users/{uid}/rollups/{period}                # precomputed aggregates for cheap dashboard reads
  kind (monthlyByCategory|netWorthSnapshot|trend), period, data{}, computedAt

mail/{mailId}                               # Firebase "Trigger Email" extension outbox
  to, message: { subject, html }
```

## Money convention

`amountCents` is a **signed integer**. **Negative = money leaving the account (spending);
positive = money entering (income).** Plaid's raw `amount` is positive for outflow, so ingestion
flips the sign. Floats are never persisted.

## Category taxonomy

The internal taxonomy and the Plaid Personal Finance Category (PFC) → internal mapping live in
[`backend/app/domain/categories.py`](../backend/app/domain/categories.py). Categorization order:
**user rule → PFC mapping → `UNCATEGORIZED`**, recorded in `categorySource`.

## Security rules

- `users/{uid}/**`: read/write only if `request.auth.uid == uid`.
- `plaid_secrets/**`: no client access at all (Admin SDK only).
- Storage `receipts/{uid}/**`: read/write only by the owner.

See [`infra/firestore.rules`](../infra/firestore.rules) and [`infra/storage.rules`](../infra/storage.rules).
