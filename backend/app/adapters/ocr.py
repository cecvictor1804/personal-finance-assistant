"""OCR adapters.

- ``DocumentAiOcrProvider``: Google Document AI Expense parser (lazy-imported). Maps the parser's
  entities to an OcrResult. Entity field availability varies by document, so parsing is defensive.
- ``FakeOcrProvider``: returns a preset OcrResult for tests.
"""

from __future__ import annotations

from datetime import date

from app.domain.money import to_cents
from app.domain.models import LineItem, OcrResult


class FakeOcrProvider:
    def __init__(self, result: OcrResult) -> None:
        self._result = result

    def parse_receipt(self, content: bytes, mime_type: str) -> OcrResult:
        return self._result


class DocumentAiOcrProvider:
    def __init__(self, processor_name: str) -> None:
        if not processor_name:
            raise ValueError("DOCAI_PROCESSOR_NAME is required for Document AI OCR")
        from google.cloud import documentai

        self._processor_name = processor_name
        self._client = documentai.DocumentProcessorServiceClient()

    def parse_receipt(self, content: bytes, mime_type: str) -> OcrResult:
        from google.cloud import documentai

        request = documentai.ProcessRequest(
            name=self._processor_name,
            raw_document=documentai.RawDocument(content=content, mime_type=mime_type),
        )
        document = self._client.process_document(request=request).document

        result = OcrResult(raw_text=document.text or "")
        for entity in document.entities:
            etype = entity.type_
            if etype == "supplier_name":
                result.merchant = (entity.mention_text or "").strip()
            elif etype in ("total_amount", "net_amount") and result.total_cents == 0:
                result.total_cents = _money_cents(entity)
            elif etype == "currency":
                result.currency = (entity.mention_text or result.currency).strip()
            elif etype in ("receipt_date", "purchase_date", "invoice_date") and result.date is None:
                result.date = _date_value(entity)
            elif etype == "line_item":
                result.line_items.append(_line_item(entity))
        return result


def _money_cents(entity) -> int:
    """Prefer the normalized money value; fall back to parsing the mention text."""
    try:
        money = entity.normalized_value.money_value
        if money is not None and (money.units or money.nanos):
            return abs(int(money.units) * 100 + round(money.nanos / 10_000_000))
    except (AttributeError, ValueError):
        pass
    try:
        return abs(to_cents(_clean_amount(entity.mention_text)))
    except (ValueError, TypeError):
        return 0


def _date_value(entity) -> date | None:
    try:
        d = entity.normalized_value.date_value
        if d and d.year:
            return date(d.year, d.month or 1, d.day or 1)
    except (AttributeError, ValueError):
        pass
    return None


def _line_item(entity) -> LineItem:
    description = ""
    amount = 0
    for prop in getattr(entity, "properties", []):
        if prop.type_.endswith("description"):
            description = (prop.mention_text or "").strip()
        elif prop.type_.endswith("amount"):
            amount = _money_cents(prop)
    return LineItem(description=description, amount_cents=amount)


def _clean_amount(text: str) -> str:
    return "".join(ch for ch in (text or "") if ch.isdigit() or ch in ".-")
