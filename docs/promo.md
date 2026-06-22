# Promotional copy

Messaging for promoting the app, leading with the **privacy / own-your-data** angle. Every claim
below maps to a shipped feature (see [../README.md](../README.md)).

> **Two notes before you publish**
> 1. **Name.** Copy uses the working name **Personal Finance Assistant**. Swap in your real brand
>    name everywhere if you have one.
> 2. **Self-host vs hosted.** Today the app is single-user and self-hosted (you run the backend and
>    bring your own Plaid + Firebase keys). The **landing-page** and **social** copy fit that as-is.
>    The **app-store listing** assumes an end user can install and connect a bank with no setup —
>    that requires you to offer a **hosted/managed** backend. If you stay self-host, use the listing
>    copy for a TestFlight / Play internal-testing build or an open-source release page instead.

---

## 1. Landing-page hero

**Headline**
> Your money. Your data. Your server.

**Subhead**
> A personal finance assistant that auto-syncs your bank, credit, investment, and loan accounts —
> while your bank credentials stay encrypted on infrastructure *you* control. No ads. No data
> resale. Ever.

**Calls to action**
- Primary: **Connect your accounts**
- Secondary: **See how your data stays yours →**

**Feature cards** (title + one line)

| Card | Copy |
|---|---|
| 🔒 Your data, full stop | Self-hosted. Bank access tokens are encrypted server-side and never touch your phone or browser. |
| 🏦 Every account, one view | Bank, credit, investment, and loan accounts sync automatically via Plaid — with live net worth. |
| 🏷️ Categorized for you | Transactions are auto-categorized from your own rules and Plaid's categories — and duplicate charges get flagged. |
| 🎯 Budgets that ping you | Set per-category caps and get alerts for overruns, large, foreign, or unusual charges. |
| 🔁 Subscriptions & forecast | Recurring charges are detected automatically, with a 30-day cash-flow forecast so there are no surprises. |
| 📸 Snap a receipt | Capture receipts on mobile; OCR reads them and matches them to the right transaction. |

**How it works** (3 steps)
1. **Connect** — link your accounts securely through Plaid.
2. **Track** — everything syncs and categorizes itself: spending, budgets, net worth.
3. **Stay ahead** — proactive alerts and a cash-flow forecast catch problems early.

**Trust line**
> Built privacy-first: your Plaid credentials are KMS-encrypted in a store your apps can't read,
> financial data is write-protected at the database layer, and the app locks behind your
> fingerprint or device passcode.

---

## 2. App-store listing

> Field limits noted per platform. Counts are approximate — re-check in App Store Connect / Play
> Console, which count emoji and some punctuation differently.

**App title** — *Apple & Google ≤ 30*
> `Personal Finance Assistant`  *(26)*

Keyword-leaning alternative:
> `Finance: Private & Automatic`  *(28)*

**Subtitle** — *Apple ≤ 30*
> `Your accounts. Your data.`  *(25)*

**Short description** — *Google Play ≤ 80*
> `Auto-sync every account, track budgets, and keep your financial data private.`  *(77)*

**Promotional text** — *Apple ≤ 170*
> `Connect your banks via Plaid and see every account, transaction, and your net worth in one place — with your data encrypted on a server you own. No ads. No selling.`  *(~164)*

**Full description** — *Google Play ≤ 4000; Apple has a large limit too*

```
Take control of your money — without handing your financial life to someone else's servers.

Personal Finance Assistant connects your bank, credit, investment, and loan accounts through
Plaid and turns them into one clear, automatic picture: spending, budgets, and your real net
worth across every account. And because it's built privacy-first, your bank credentials are
encrypted on infrastructure you control and never reach your phone or browser.

OWN YOUR DATA
• Your Plaid access tokens are encrypted and stored where the app itself can't read them.
• Financial data is write-protected at the database layer.
• Lock the app behind your fingerprint or device passcode.
• No ads. No selling your data. No third-party trackers feeding on your spending.

EVERYTHING IN ONE PLACE
• Auto-sync bank, credit, investment, and loan accounts via Plaid.
• See live balances and your true net worth as accounts update.
• Web dashboard and a mobile app stay in sync.

AUTOMATIC, ACCURATE CATEGORIES
• Transactions are categorized for you — using your own rules plus Plaid's categories.
• Duplicate charges are detected and flagged so you never pay twice unnoticed.

BUDGETS THAT ACTUALLY HELP
• Set monthly caps per category and watch progress in real time.
• Get alerts for budget overruns, large transactions, foreign charges, new merchants, and
  statistically unusual spending.

NEVER GET SURPRISED
• Recurring charges and subscriptions are detected automatically.
• A 30-day cash-flow forecast shows what's coming before it hits.

RECEIPTS, HANDLED
• Snap a photo of a receipt; OCR reads it and matches it to the right transaction.

Your money, your data, your rules.
```
*(~1,560 characters — well within both platforms' limits, leaving room to expand.)*

**Keywords** — *Apple ≤ 100 chars, comma-separated*
> `budget,finance,money,expenses,net worth,Plaid,privacy,spending,subscriptions,bank,tracker`  *(~89)*

**"What's new"**
> `Faster account sync, sharper duplicate detection, and a clearer net-worth view.`

**Listing prerequisite (do not publish without this):** a public app-store listing implies a hosted
backend a user can connect to immediately. Stand up a managed backend first, or repurpose this copy
for TestFlight / Play internal testing / an open-source release page.

---

## 3. Short taglines & social

**One-liners**
- Your money. Your data. Your server.
- All your accounts. One clear picture. Zero data resale.
- Personal finance that runs on infrastructure you own.
- Budgets, net worth, and alerts — without selling your spending to anyone.
- Auto-sync everything. Own everything.
- Finance that watches your back, not your data.
- The privacy-first way to see all your money in one place.
- Your bank credentials never touch your phone. Your insights always do.

**Blurb** — *≤ 280 chars (Twitter/X, bios)*
> `A privacy-first personal finance assistant: auto-syncs your bank, credit & investment accounts via Plaid, categorizes spending, tracks budgets & net worth, flags duplicates and unusual charges, and forecasts cash flow — with your data encrypted on a server you own.`  *(265)*

**Product Hunt / Show HN**

*Tagline (≤ 60):*
> `Self-hosted personal finance — own your accounts and data`  *(57)*

*First comment / intro:*
> I wanted the convenience of Mint/Monarch without handing my entire financial life to a company
> whose business is my data. So I built a self-hosted personal finance assistant.
>
> It connects your bank, credit, investment, and loan accounts through Plaid, then auto-categorizes
> transactions, tracks budgets and net worth, detects duplicate charges and subscriptions, forecasts
> 30 days of cash flow, and even OCRs receipts. There's a React web dashboard and a Flutter mobile
> app.
>
> The privacy model is the point: Plaid access tokens are KMS-encrypted in a store the apps can't
> read and never reach your device, financial data is write-protected at the database layer, and the
> app locks behind biometrics. No ads, no data resale.
>
> Happy to answer anything about the architecture (hexagonal FastAPI backend, Cloud Functions for
> Plaid/webhooks, Firestore) or the privacy design.
