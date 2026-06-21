"""Object-store adapters: Google Cloud Storage (lazy) and an in-memory fake for tests."""

from __future__ import annotations


class GcsObjectStore:
    def __init__(self) -> None:
        from google.cloud import storage

        self._client = storage.Client()

    def read(self, bucket: str, path: str) -> bytes:
        return self._client.bucket(bucket).blob(path).download_as_bytes()


class FakeObjectStore:
    def __init__(self, data: bytes = b"fake-image-bytes") -> None:
        self._data = data

    def read(self, bucket: str, path: str) -> bytes:
        return self._data
