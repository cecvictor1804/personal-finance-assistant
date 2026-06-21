"""User settings endpoints: alert thresholds, home country, email, and FCM token registration."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_uid, get_repository
from app.api.schemas import FcmTokenIn
from app.domain.models import UserSettings
from app.ports.repository import Repository

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=UserSettings)
def get_settings(
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
):
    return repo.get_settings(uid) or UserSettings()


@router.put("", response_model=UserSettings)
def update_settings(
    body: UserSettings,
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
):
    repo.save_settings(uid, body)
    return body


@router.post("/fcm-token", response_model=UserSettings)
def register_fcm_token(
    body: FcmTokenIn,
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
):
    settings = repo.get_settings(uid) or UserSettings()
    if body.token and body.token not in settings.fcm_tokens:
        settings.fcm_tokens.append(body.token)
        repo.save_settings(uid, settings)
    return settings
