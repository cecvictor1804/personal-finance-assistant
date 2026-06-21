"""Composition root + FastAPI dependencies.

Adapters are built lazily as singletons so unit tests can override them via
``app.dependency_overrides`` without importing Plaid/Firebase SDKs. Auth verifies a Firebase ID
token unless ``AUTH_DISABLED`` is set (local dev only).
"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from app.config import Settings, get_settings
from app.ports.bank_provider import BankProvider
from app.ports.notifier import Notifier
from app.ports.repository import Repository
from app.services.alerts import AlertEngine
from app.services.budgets import BudgetService
from app.services.forecast import CashFlowService
from app.services.recurring import RecurringService
from app.services.rollups import RollupService
from app.services.sync import SyncService

_repo: Repository | None = None
_provider: BankProvider | None = None
_firebase_ready = False


def get_repository(settings: Settings = Depends(get_settings)) -> Repository:
    global _repo
    if _repo is None:
        if settings.app_env == "local":
            from app.adapters.memory_repo import MemoryRepository

            _repo = MemoryRepository()
        else:
            from app.adapters.firestore_repo import FirestoreRepository

            _repo = FirestoreRepository(settings.gcp_project_id, settings.kms_key_name)
    return _repo


def get_provider(settings: Settings = Depends(get_settings)) -> BankProvider:
    global _provider
    if _provider is None:
        from app.adapters.plaid_provider import PlaidProvider

        _provider = PlaidProvider(settings)
    return _provider


def get_notifier(settings: Settings = Depends(get_settings)) -> Notifier:
    if settings.app_env == "local":
        from app.adapters.notifier import FakeNotifier

        return FakeNotifier()
    from app.adapters.notifier import FirestoreFcmNotifier

    return FirestoreFcmNotifier()


def get_budget_service(repo: Repository = Depends(get_repository)) -> BudgetService:
    return BudgetService(repo)


def get_alert_engine(
    repo: Repository = Depends(get_repository),
    notifier: Notifier = Depends(get_notifier),
) -> AlertEngine:
    return AlertEngine(repo, notifier)


def get_recurring_service(
    provider: BankProvider = Depends(get_provider),
    repo: Repository = Depends(get_repository),
    notifier: Notifier = Depends(get_notifier),
) -> RecurringService:
    return RecurringService(provider, repo, alert_engine=AlertEngine(repo, notifier))


def get_forecast_service(repo: Repository = Depends(get_repository)) -> CashFlowService:
    return CashFlowService(repo)


def get_sync_service(
    provider: BankProvider = Depends(get_provider),
    repo: Repository = Depends(get_repository),
    notifier: Notifier = Depends(get_notifier),
) -> SyncService:
    engine = AlertEngine(repo, notifier)
    return SyncService(
        provider,
        repo,
        alert_engine=engine,
        budget_service=BudgetService(repo),
        rollup_service=RollupService(repo),
        recurring_service=RecurringService(provider, repo, alert_engine=engine),
    )


def _ensure_firebase() -> None:
    global _firebase_ready
    if _firebase_ready:
        return
    import firebase_admin

    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    _firebase_ready = True


def get_current_uid(
    authorization: str = Header(default=""),
    settings: Settings = Depends(get_settings),
) -> str:
    if settings.auth_disabled:
        return settings.dev_uid

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    _ensure_firebase()
    from firebase_admin import auth as fb_auth

    try:
        decoded = fb_auth.verify_id_token(token)
    except Exception as exc:  # noqa: BLE001 - any verification failure is a 401
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid ID token") from exc
    return decoded["uid"]


def require_internal_secret(
    x_internal_secret: str = Header(default=""),
    settings: Settings = Depends(get_settings),
) -> None:
    """Guard the internal sync endpoint called by the webhook -> Pub/Sub pipeline."""
    if not settings.internal_secret or x_internal_secret != settings.internal_secret:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")
