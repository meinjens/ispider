from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, HttpUrl
from typing import Optional

from ....domain.models import SourcePriority
from ....domain.services import SourceService
from ....config.dependencies import get_source_service

router = APIRouter(prefix="/sources", tags=["sources"])


class SourceCreate(BaseModel):
    url: HttpUrl
    name: str
    priority: SourcePriority = SourcePriority.HIGH
    tag_ids: list[int] = []


class SourceUpdate(BaseModel):
    active: Optional[bool] = None
    priority: Optional[SourcePriority] = None
    tag_ids: Optional[list[int]] = None


@router.get("/")
async def list_sources(active_only: bool = False, svc: SourceService = Depends(get_source_service)):
    return await svc.list_sources(active_only=active_only)


@router.post("/", status_code=201)
async def add_source(body: SourceCreate, svc: SourceService = Depends(get_source_service)):
    return await svc.add_source(str(body.url), body.name, body.priority, body.tag_ids)


@router.put("/{source_id}")
async def update_source(source_id: int, body: SourceUpdate, svc: SourceService = Depends(get_source_service)):
    try:
        return await svc.update_source(source_id, body.active, body.priority, body.tag_ids)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: int, svc: SourceService = Depends(get_source_service)):
    await svc.delete_source(source_id)


@router.post("/opml", status_code=201)
async def import_opml(file: UploadFile = File(...), svc: SourceService = Depends(get_source_service)):
    content = await file.read()
    return await svc.import_opml(content.decode("utf-8"))
