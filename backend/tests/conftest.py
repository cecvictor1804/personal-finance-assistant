"""Shared pytest fixtures: in-memory repo, fake provider, and a wired-up TestClient."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.adapters.fake_provider import FakeBankProvider
from app.adapters.memory_repo import MemoryRepository
from app.adapters.notifier import FakeNotifier
from app.api.deps import (
    get_current_uid,
    get_notifier,
    get_provider,
    get_repository,
    get_sync_service,
)
from app.config import Settings, get_settings
from app.main import create_app
from app.ports.repository import ItemSecret
from app.services.alerts import AlertEngine
from app.services.budgets import BudgetService
from app.services.recurring import RecurringService
from app.services.rollups import RollupService
from app.services.sync import SyncService

TEST_UID = "u1"


@pytest.fixture
def repo() -> MemoryRepository:
    return MemoryRepository()


@pytest.fixture
def provider() -> FakeBankProvider:
    return FakeBankProvider()


@pytest.fixture
def notifier() -> FakeNotifier:
    return FakeNotifier()


@pytest.fixture
def settings() -> Settings:
    return Settings(app_env="local", auth_disabled=True, dev_uid=TEST_UID, internal_secret="s3cr3t")


@pytest.fixture
def client(
    repo: MemoryRepository,
    provider: FakeBankProvider,
    settings: Settings,
    notifier: FakeNotifier,
) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_repository] = lambda: repo
    app.dependency_overrides[get_provider] = lambda: provider
    app.dependency_overrides[get_current_uid] = lambda: TEST_UID
    app.dependency_overrides[get_notifier] = lambda: notifier
    app.dependency_overrides[get_sync_service] = lambda: SyncService(
        provider,
        repo,
        alert_engine=AlertEngine(repo, notifier),
        budget_service=BudgetService(repo),
        rollup_service=RollupService(repo),
        recurring_service=RecurringService(provider, repo, alert_engine=AlertEngine(repo, notifier)),
    )
    return TestClient(app)


@pytest.fixture
def seeded_item(repo: MemoryRepository) -> str:
    """An item with stored credentials so sync can run. Returns the item_id."""
    item_id = "item_1"
    repo.save_item_secret(ItemSecret(item_id=item_id, uid=TEST_UID, access_token="access-x"))
    from app.domain.models import PlaidItem

    repo.upsert_item(TEST_UID, PlaidItem(id=item_id, institution_name="Test Bank"))
    return item_id
