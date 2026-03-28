from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from ....domain.services import FeedService, TagService, KeywordService, PushService, AIQueryService
from ....config.dependencies import (
    get_feed_service, get_tag_service, get_keyword_service,
    get_push_service, get_ai_query_service,
)

# ── Items ────────────────────────────────────────────────────────────────────
items_router = APIRouter(prefix="/items", tags=["items"])


@items_router.get("/")
async def list_items(
    source_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    min_score: Optional[int] = None,
    read: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    svc: FeedService = Depends(get_feed_service),
):
    return await svc.list_items(source_id, tag_id, min_score, read, limit, offset)


@items_router.patch("/{item_id}/read", status_code=204)
async def mark_read(item_id: int, svc: FeedService = Depends(get_feed_service)):
    await svc.mark_read(item_id)


# ── Tags ─────────────────────────────────────────────────────────────────────
tags_router = APIRouter(prefix="/tags", tags=["tags"])


class TagCreate(BaseModel):
    name: str
    color: str = "#00B37E"


@tags_router.get("/")
async def list_tags(svc: TagService = Depends(get_tag_service)):
    return await svc.list_tags()


@tags_router.post("/", status_code=201)
async def create_tag(body: TagCreate, svc: TagService = Depends(get_tag_service)):
    return await svc.create_tag(body.name, body.color)


@tags_router.delete("/{tag_id}", status_code=204)
async def delete_tag(tag_id: int, svc: TagService = Depends(get_tag_service)):
    await svc.delete_tag(tag_id)


# ── Keywords ─────────────────────────────────────────────────────────────────
keywords_router = APIRouter(prefix="/keywords", tags=["keywords"])


class KeywordCreate(BaseModel):
    term: str
    threshold: int = 60
    notify: bool = True


@keywords_router.get("/")
async def list_keywords(svc: KeywordService = Depends(get_keyword_service)):
    return await svc.list_keywords()


@keywords_router.post("/", status_code=201)
async def create_keyword(body: KeywordCreate, svc: KeywordService = Depends(get_keyword_service)):
    return await svc.create_keyword(body.term, body.threshold, body.notify)


@keywords_router.delete("/{keyword_id}", status_code=204)
async def delete_keyword(keyword_id: int, svc: KeywordService = Depends(get_keyword_service)):
    await svc.delete_keyword(keyword_id)


# ── Push ─────────────────────────────────────────────────────────────────────
push_router = APIRouter(prefix="/push", tags=["push"])


class PushSubscribeBody(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


@push_router.post("/subscribe", status_code=201)
async def subscribe(body: PushSubscribeBody, svc: PushService = Depends(get_push_service)):
    return await svc.subscribe(body.endpoint, body.p256dh, body.auth)


# ── AI ───────────────────────────────────────────────────────────────────────
ai_router = APIRouter(prefix="/ai", tags=["ai"])


class AIQueryBody(BaseModel):
    prompt: str


@ai_router.post("/query")
async def ai_query(body: AIQueryBody, svc: AIQueryService = Depends(get_ai_query_service)):
    return {"response": await svc.query(body.prompt)}
