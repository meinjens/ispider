from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .adapters.inbound.api.routers.sources import router as sources_router
from .adapters.inbound.api.routers.misc import (
    items_router, tags_router, keywords_router, push_router, ai_router,
)
from .config.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(title="iSpider API", version="0.1.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(sources_router, prefix="/api")
app.include_router(items_router, prefix="/api")
app.include_router(tags_router, prefix="/api")
app.include_router(keywords_router, prefix="/api")
app.include_router(push_router, prefix="/api")
app.include_router(ai_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
