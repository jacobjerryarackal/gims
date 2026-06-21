from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from storage.chroma import chroma_storage
from api.routes import chat, memories, hitl, audit, metrics
from api.middleware.logging import logging_middleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    await chroma_storage.connect()
    yield

app = FastAPI(
    title="GIMS - GPT Intelligence Memory System",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://your-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add /api prefix to all routers
app.include_router(chat.router, prefix="/api")
app.include_router(memories.router, prefix="/api")
app.include_router(hitl.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")

@app.get("/health")
async def health_check():
    from services.health_service import health_service
    return await health_service.check_health()

@app.get("/")
async def root():
    return {"message": "GIMS API", "version": "1.0.0", "docs": "/docs"}