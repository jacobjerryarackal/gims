from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from storage.chroma import chroma_storage
from api.routes import chat, memories, hitl, audit, metrics
from api.middleware.logging import logging_middleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await chroma_storage.connect()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="GIMS - GPT Intelligence Memory System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://your-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REGISTER the logging middleware
app.middleware("http")(logging_middleware)

# Routes
app.include_router(chat.router, prefix="/api/chat")
app.include_router(memories.router, prefix="/api/memories")
app.include_router(hitl.router, prefix="/api/hitl")
app.include_router(audit.router, prefix="/api/audit")
app.include_router(metrics.router, prefix="/api/metrics")

@app.get("/health")
async def health_check():
    from services.health_service import health_service
    return await health_service.check_health()

@app.get("/")
async def root():
    return {"message": "GIMS API", "version": "1.0.0", "docs": "/docs"}