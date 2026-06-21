"""Categorization-rule endpoints: list, create, delete."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_uid, get_repository
from app.api.schemas import MessageOut, RuleIn
from app.domain.models import Rule
from app.ports.repository import Repository

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("", response_model=list[Rule])
def list_rules(
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
):
    return sorted(repo.get_rules(uid), key=lambda r: (r.priority, r.created_at))


@router.post("", response_model=Rule, status_code=status.HTTP_201_CREATED)
def create_rule(
    body: RuleIn,
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
):
    rule = Rule(
        id=f"rule_{uuid.uuid4().hex[:12]}",
        match_type=body.match_type,
        pattern=body.pattern,
        category=body.category,
        priority=body.priority,
    )
    repo.add_rule(uid, rule)
    return rule


@router.delete("/{rule_id}", response_model=MessageOut)
def delete_rule(
    rule_id: str,
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
):
    repo.delete_rule(uid, rule_id)
    return MessageOut(message="deleted")
