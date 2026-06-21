"""OCR port. Document AI is the concrete adapter; tests use a fake."""

from __future__ import annotations

from typing import Protocol

from app.domain.models import OcrResult


class OcrProvider(Protocol):
    def parse_receipt(self, content: bytes, mime_type: str) -> OcrResult:
        """Extract merchant/total/date/line-items from a receipt image or PDF."""
        ...
