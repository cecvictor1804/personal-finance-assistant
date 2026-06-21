"""Receipt processing: OCR an uploaded receipt and suggest (not auto-apply) a transaction match.

Pipeline (triggered by a Cloud Storage upload): read bytes -> Document AI -> parse merchant/total/
date -> suggest a matching transaction by amount + date window + merchant similarity. Following the
project's flag-don't-merge policy, ``process`` only records a *suggested* match on the receipt;
linking the receipt to the transaction happens when the user confirms via ``attach``.
"""

from __future__ import annotations

from app.domain.models import OcrResult, Receipt, ReceiptStatus, Transaction
from app.ports.ocr import OcrProvider
from app.ports.object_store import ObjectStore
from app.ports.repository import Repository
from app.services.dedup import merchant_similarity

RECEIPT_MATCH_WINDOW_DAYS = 5
MIN_MATCH_SIMILARITY = 0.5  # looser than dedup: amount + date are already strong signals


def _mime_for(path: str) -> str:
    p = path.lower()
    if p.endswith(".pdf"):
        return "application/pdf"
    if p.endswith(".png"):
        return "image/png"
    return "image/jpeg"


class ReceiptService:
    def __init__(
        self,
        ocr: OcrProvider,
        object_store: ObjectStore,
        repo: Repository,
        window_days: int = RECEIPT_MATCH_WINDOW_DAYS,
    ) -> None:
        self._ocr = ocr
        self._store = object_store
        self._repo = repo
        self._window = window_days

    def process(self, uid: str, receipt_id: str, bucket: str, storage_path: str) -> Receipt:
        try:
            content = self._store.read(bucket, storage_path)
            ocr = self._ocr.parse_receipt(content, _mime_for(storage_path))
        except Exception:  # noqa: BLE001 - record the failure rather than crash the pipeline
            receipt = Receipt(
                id=receipt_id, storage_path=storage_path, status=ReceiptStatus.ERROR
            )
            self._repo.upsert_receipt(uid, receipt)
            return receipt

        receipt = Receipt(
            id=receipt_id,
            storage_path=storage_path,
            status=ReceiptStatus.PARSED,
            merchant=ocr.merchant,
            total_cents=ocr.total_cents,
            date=ocr.date,
            line_items=ocr.line_items,
        )
        match = self._suggest_match(uid, ocr)
        if match is not None:
            # Suggestion only — status stays PARSED until the user confirms via attach().
            receipt.matched_txn_id = match.id
        self._repo.upsert_receipt(uid, receipt)
        return receipt

    def attach(self, uid: str, receipt_id: str, txn_id: str) -> Receipt:
        receipt = self._repo.get_receipt(uid, receipt_id)
        if receipt is None:
            raise ValueError(f"Receipt {receipt_id} not found")
        txn = self._repo.get_transaction(uid, txn_id)
        if txn is None:
            raise ValueError(f"Transaction {txn_id} not found")

        txn.receipt_id = receipt_id
        self._repo.upsert_transaction(uid, txn)
        receipt.matched_txn_id = txn_id
        receipt.status = ReceiptStatus.MATCHED
        self._repo.upsert_receipt(uid, receipt)
        return receipt

    def _suggest_match(self, uid: str, ocr: OcrResult) -> Transaction | None:
        if ocr.total_cents <= 0 or ocr.date is None:
            return None
        candidates = self._repo.find_transactions_by_amount(
            uid, amount_cents=-ocr.total_cents, around=ocr.date, window_days=self._window
        )
        best: Transaction | None = None
        best_score = 0.0
        for t in candidates:
            score = merchant_similarity(ocr.merchant, t.merchant)
            if not ocr.merchant or not t.merchant:
                score = max(score, MIN_MATCH_SIMILARITY)
            if score >= MIN_MATCH_SIMILARITY and score > best_score:
                best, best_score = t, score
        return best
