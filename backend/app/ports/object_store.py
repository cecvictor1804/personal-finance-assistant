"""Object-storage port (Cloud Storage). Reads a stored receipt's bytes. Faked in tests."""

from __future__ import annotations

from typing import Protocol


class ObjectStore(Protocol):
    def read(self, bucket: str, path: str) -> bytes:
        """Return the bytes of an object, or raise if missing."""
        ...
