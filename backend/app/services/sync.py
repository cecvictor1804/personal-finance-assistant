"""Transaction sync orchestrator (Plaid /transactions/sync semantics).

Pulls added/modified/removed pages by cursor, normalizes + categorizes each transaction, flags
suspected duplicates of manual entries, upserts accounts, and advances the cursor. Preserves
user-owned fields (manual category override, notes, receipt) across re-syncs so a Plaid "modified"
event never clobbers the user's edits.

Optional post-sync collaborators (alert engine, budget + rollup services) run after the data lands.
Alerts are intentionally suppressed on the initial backfill (cursor was empty) so importing 24
months of history doesn't fire hundreds of "new merchant"/"large transaction" notifications.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.domain.models import CategorySource, ItemStatus, Transaction
from app.ports.bank_provider import BankProvider
from app.ports.repository import Repository
from app.services.alerts import AlertEngine
from app.services.budgets import BudgetService
from app.services.categorization import apply_categorization
from app.services.dedup import DEFAULT_WINDOW_DAYS, find_duplicate
from app.services.normalize import normalize_account, normalize_transaction
from app.services.recurring import RecurringService
from app.services.rollups import RollupService

# Safety bound: Plaid guarantees cursor progress, but never loop forever on a misbehaving provider.
_MAX_PAGES = 100


@dataclass
class SyncReport:
    added: int = 0
    modified: int = 0
    removed: int = 0
    flagged_duplicates: int = 0
    alerts_created: int = 0
    pages: int = 0
    is_initial: bool = False
    cursor: str = ""
    new_transactions: list[Transaction] = field(default_factory=list)


class SyncService:
    def __init__(
        self,
        provider: BankProvider,
        repo: Repository,
        dedup_window_days: int = DEFAULT_WINDOW_DAYS,
        alert_engine: AlertEngine | None = None,
        budget_service: BudgetService | None = None,
        rollup_service: RollupService | None = None,
        recurring_service: RecurringService | None = None,
    ) -> None:
        self._provider = provider
        self._repo = repo
        self._window = dedup_window_days
        self._alert_engine = alert_engine
        self._budget_service = budget_service
        self._rollup_service = rollup_service
        self._recurring_service = recurring_service

    def sync_item(self, uid: str, item_id: str) -> SyncReport:
        secret = self._repo.get_item_secret(item_id)
        if secret is None:
            raise ValueError(f"No stored credentials for item {item_id}")

        rules = self._repo.get_rules(uid)
        cursor = secret.cursor
        is_initial = not bool(cursor)
        report = SyncReport(cursor=cursor or "", is_initial=is_initial)
        new_txns: list[Transaction] = []

        for _ in range(_MAX_PAGES):
            page = self._provider.sync_transactions(secret.access_token, cursor)

            for raw in page.added + page.modified:
                txn = apply_categorization(normalize_transaction(raw), rules)
                existing = self._repo.get_transaction(uid, txn.id)
                is_new = existing is None
                if is_new:
                    # Dedup only matters on incremental syncs: on the initial backfill there are
                    # no prior manual entries to collide with, and running the candidate query per
                    # backfilled transaction would be a wasted read.
                    if not is_initial and self._flag_duplicate(uid, txn):
                        report.flagged_duplicates += 1
                else:
                    txn = self._preserve_user_fields(existing, txn)
                self._repo.upsert_transaction(uid, txn)
                if is_new:
                    new_txns.append(txn)

            for plaid_txn_id in page.removed:
                self._repo.delete_transaction_by_plaid_id(uid, plaid_txn_id)

            for raw_acct in page.accounts:
                self._repo.upsert_account(uid, normalize_account(raw_acct))

            report.added += len(page.added)
            report.modified += len(page.modified)
            report.removed += len(page.removed)
            report.pages += 1

            cursor = page.next_cursor
            self._repo.update_cursor(item_id, cursor)
            report.cursor = cursor
            if not page.has_more:
                break

        report.new_transactions = new_txns
        self._post_process(uid, item_id, new_txns, is_initial, report)

        self._repo.touch_item_synced(uid, item_id)
        self._repo.set_item_status(uid, item_id, ItemStatus.ACTIVE)
        return report

    def sync_all_items(self, uid: str) -> dict[str, SyncReport]:
        """Daily-reconcile entry point: sync every active item for a user."""
        return {item.id: self.sync_item(uid, item.id) for item in self._repo.get_items(uid)}

    def mark_needs_reauth(self, uid: str, item_id: str) -> None:
        """Called on a Plaid ITEM_LOGIN_REQUIRED webhook; UI then offers guided re-link."""
        self._repo.set_item_status(uid, item_id, ItemStatus.NEEDS_REAUTH)

    # --- post-processing: budgets, rollups, alerts, recurring ---
    def _post_process(
        self,
        uid: str,
        item_id: str,
        new_txns: list[Transaction],
        is_initial: bool,
        report: SyncReport,
    ) -> None:
        if not (
            self._alert_engine
            or self._budget_service
            or self._rollup_service
            or self._recurring_service
        ):
            return

        months = sorted({t.date.isoformat()[:7] for t in new_txns})
        for month in months:
            budget = (
                self._budget_service.recompute_month(uid, month) if self._budget_service else None
            )
            if self._rollup_service:
                self._rollup_service.recompute_month_category(uid, month)
            if budget is not None and self._alert_engine and not is_initial:
                report.alerts_created += len(self._alert_engine.evaluate_budget(uid, budget))

        if self._alert_engine and not is_initial:
            for txn in new_txns:
                report.alerts_created += len(self._alert_engine.evaluate_transaction(uid, txn))

        if self._recurring_service:
            report.alerts_created += len(
                self._recurring_service.refresh_item(uid, item_id, is_initial=is_initial)
            )

        if self._rollup_service:
            self._rollup_service.snapshot_net_worth(uid, date.today())

    # --- helpers ---
    def _flag_duplicate(self, uid: str, txn: Transaction) -> bool:
        candidates = self._repo.find_candidate_duplicates(
            uid, amount_cents=txn.amount_cents, around=txn.date, window_days=self._window
        )
        dup_id = find_duplicate(txn, candidates)
        if dup_id:
            txn.possible_duplicate_of = dup_id
            return True
        return False

    @staticmethod
    def _preserve_user_fields(existing: Transaction, incoming: Transaction) -> Transaction:
        """Keep user-owned edits when Plaid re-sends a modified transaction."""
        update: dict[str, object] = {
            "notes": existing.notes,
            "receipt_id": existing.receipt_id,
            "possible_duplicate_of": existing.possible_duplicate_of,
            "created_at": existing.created_at,
        }
        if existing.category_source == CategorySource.MANUAL:
            update["category"] = existing.category
            update["category_source"] = CategorySource.MANUAL
        return incoming.model_copy(update=update)
