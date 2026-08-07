"""Explorations routes.

  GET    /explorations               ?q
  GET    /explorations/{id}
  PATCH  /explorations/{id}          rename / pin / verified
  DELETE /explorations/{id}
  POST   /explorations               (v1: rejected — creation is implicit via /chat)
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from trialmind.db_explorations import (
    Exploration, delete_exploration, get_exploration, list_explorations, patch_exploration,
)
from trialmind.errors import APIError

router = APIRouter(prefix="/explorations", tags=["explorations"])


class ExplorationListOut(BaseModel):
    items: list[Exploration]


class ExplorationPatchBody(BaseModel):
    title: str | None = None
    pinned: bool | None = None
    verified: bool | None = None


@router.get("", response_model=ExplorationListOut)
async def list_all(q: str = "") -> ExplorationListOut:
    items = await list_explorations(q=q)
    return ExplorationListOut(items=items)


@router.get("/{exp_id}", response_model=Exploration)
async def get_one(exp_id: UUID) -> Exploration:
    exp = await get_exploration(exp_id, with_messages=True)
    if exp is None:
        raise APIError.not_found("exploration", str(exp_id))
    return exp


@router.patch("/{exp_id}", response_model=Exploration)
async def patch_one(exp_id: UUID, body: ExplorationPatchBody) -> Exploration:
    exp = await patch_exploration(
        exp_id, title=body.title, pinned=body.pinned, verified=body.verified,
    )
    if exp is None:
        raise APIError.not_found("exploration", str(exp_id))
    return exp


@router.delete("/{exp_id}", status_code=204)
async def delete_one(exp_id: UUID) -> None:
    ok = await delete_exploration(exp_id)
    if not ok:
        raise APIError.not_found("exploration", str(exp_id))
