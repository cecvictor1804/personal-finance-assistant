from datetime import date

from app.adapters.memory_repo import MemoryRepository
from app.adapters.object_store import FakeObjectStore
from app.adapters.ocr import FakeOcrProvider
from app.domain.models import OcrResult, ReceiptStatus, Transaction, TransactionSource
from app.services.receipts import ReceiptService

UID = "u1"


def _svc(repo, ocr_result):
    return ReceiptService(FakeOcrProvider(ocr_result), FakeObjectStore(), repo)


def _txn(repo, *, id_, cents, d, merchant):
    repo.upsert_transaction(
        UID,
        Transaction(id=id_, account_id="a", amount_cents=cents, date=d, merchant=merchant,
                    source=TransactionSource.PLAID),
    )


def test_process_parses_and_suggests_match():
    repo = MemoryRepository()
    _txn(repo, id_="plaid_1", cents=-4599, d=date(2026, 6, 10), merchant="Blue Bottle Coffee")
    ocr = OcrResult(merchant="Blue Bottle", total_cents=4599, date=date(2026, 6, 11))

    receipt = _svc(repo, ocr).process(UID, "r1", "bucket", "receipts/u1/r1.jpg")

    assert receipt.status == ReceiptStatus.PARSED
    assert receipt.matched_txn_id == "plaid_1"      # suggested
    assert receipt.merchant == "Blue Bottle"
    assert receipt.total_cents == 4599
    # Flag, don't merge: the transaction is NOT modified by processing.
    assert repo.get_transaction(UID, "plaid_1").receipt_id is None


def test_process_no_match_outside_date_window():
    repo = MemoryRepository()
    _txn(repo, id_="plaid_1", cents=-4599, d=date(2026, 5, 1), merchant="Cafe")
    ocr = OcrResult(merchant="Cafe", total_cents=4599, date=date(2026, 6, 11))

    receipt = _svc(repo, ocr).process(UID, "r2", "b", "receipts/u1/r2.jpg")

    assert receipt.matched_txn_id is None
    assert receipt.status == ReceiptStatus.PARSED


def test_process_no_match_on_different_amount():
    repo = MemoryRepository()
    _txn(repo, id_="plaid_1", cents=-9999, d=date(2026, 6, 10), merchant="Cafe")
    ocr = OcrResult(merchant="Cafe", total_cents=4599, date=date(2026, 6, 11))

    receipt = _svc(repo, ocr).process(UID, "r3", "b", "receipts/u1/r3.jpg")
    assert receipt.matched_txn_id is None


def test_process_records_error_when_ocr_fails():
    repo = MemoryRepository()

    class _BoomOcr:
        def parse_receipt(self, content, mime_type):
            raise RuntimeError("doc ai unavailable")

    receipt = ReceiptService(_BoomOcr(), FakeObjectStore(), repo).process(
        UID, "r4", "b", "receipts/u1/r4.jpg"
    )
    assert receipt.status == ReceiptStatus.ERROR


def test_attach_links_receipt_and_transaction():
    repo = MemoryRepository()
    _txn(repo, id_="plaid_1", cents=-4599, d=date(2026, 6, 10), merchant="Cafe")
    svc = _svc(repo, OcrResult(merchant="Cafe", total_cents=4599, date=date(2026, 6, 11)))
    svc.process(UID, "r1", "b", "receipts/u1/r1.jpg")

    receipt = svc.attach(UID, "r1", "plaid_1")

    assert receipt.status == ReceiptStatus.MATCHED
    assert receipt.matched_txn_id == "plaid_1"
    assert repo.get_transaction(UID, "plaid_1").receipt_id == "r1"


def test_attach_unknown_ids_raise():
    repo = MemoryRepository()
    svc = _svc(repo, OcrResult())
    import pytest

    with pytest.raises(ValueError):
        svc.attach(UID, "missing", "missing")
