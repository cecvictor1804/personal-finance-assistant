"""Cloud KMS symmetric encrypt/decrypt for Plaid access tokens.

Access tokens are small (well under KMS's 64 KiB limit), so we encrypt them directly with a KMS
key rather than doing envelope encryption. Ciphertext is stored base64-encoded in the
client-inaccessible `plaid_secrets` collection. The KMS client is imported lazily.
"""

from __future__ import annotations

import base64


class KmsCipher:
    def __init__(self, key_name: str) -> None:
        if not key_name:
            raise ValueError("KMS_KEY_NAME is required to encrypt/decrypt Plaid tokens")
        from google.cloud import kms

        self._key_name = key_name
        self._client = kms.KeyManagementServiceClient()

    def encrypt(self, plaintext: str) -> str:
        resp = self._client.encrypt(
            request={"name": self._key_name, "plaintext": plaintext.encode("utf-8")}
        )
        return base64.b64encode(resp.ciphertext).decode("ascii")

    def decrypt(self, ciphertext_b64: str) -> str:
        ciphertext = base64.b64decode(ciphertext_b64)
        resp = self._client.decrypt(
            request={"name": self._key_name, "ciphertext": ciphertext}
        )
        return resp.plaintext.decode("utf-8")
