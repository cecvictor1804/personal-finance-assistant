"""Application settings, loaded from environment / .env.

Integrations (Plaid, Firebase, KMS) are configured here but only instantiated lazily by their
adapters, so unit tests that exercise pure domain logic never need real credentials.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: str = Field(default="local")
    cors_origins: str = Field(default="http://localhost:5173")
    auth_disabled: bool = Field(default=False)
    dev_uid: str = Field(default="dev-user")
    # When true (local only), seed the in-memory repo with demo data at startup. See app.seed.
    seed_demo_data: bool = Field(default=False)
    # Shared secret guarding the internal sync endpoint hit by the webhook->Pub/Sub pipeline.
    # In production prefer OIDC service-account auth on the Pub/Sub push subscription.
    internal_secret: str = Field(default="")

    # Plaid
    plaid_client_id: str = Field(default="")
    plaid_secret: str = Field(default="")
    plaid_env: str = Field(default="sandbox")
    plaid_products: str = Field(default="transactions,investments,liabilities")
    plaid_country_codes: str = Field(default="US")

    # GCP / Firebase
    gcp_project_id: str = Field(default="")
    kms_key_name: str = Field(default="")
    # Document AI Expense parser processor (projects/{p}/locations/{loc}/processors/{id}).
    docai_processor_name: str = Field(default="")

    # Alerts (Phase 3)
    large_txn_threshold_cents: int = Field(default=50_000)
    budget_warn_percent: int = Field(default=80)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def plaid_product_list(self) -> list[str]:
        return [p.strip() for p in self.plaid_products.split(",") if p.strip()]

    @property
    def plaid_country_code_list(self) -> list[str]:
        return [c.strip() for c in self.plaid_country_codes.split(",") if c.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
