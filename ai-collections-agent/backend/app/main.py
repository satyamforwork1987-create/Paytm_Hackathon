"""
AI Collections & Retention Agent — FastAPI entry point.
Autonomous AI teammate for recovering failed Paytm payments.
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.utils.logger import setup_logging
from app.routes.webhooks import router as webhook_router
from app.routes.dashboard import router as dashboard_router
from app.routes.customers import router as customer_router
from app.routes.ai_agent import router as ai_agent_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle handler."""
    logger.info("🚀 Starting AI Collections Agent...")
    await init_db()
    logger.info("✅ Database tables initialized")
    yield
    logger.info("🛑 Shutting down AI Collections Agent")


app = FastAPI(
    title="AI Collections & Retention Agent",
    description=(
        "Autonomous AI teammate that recovers failed Paytm payments "
        "and prevents subscription churn using Google Gemini AI."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(webhook_router)
app.include_router(dashboard_router)
app.include_router(customer_router)
app.include_router(ai_agent_router)


@app.get("/", tags=["health"])
async def root():
    return {
        "service": "AI Collections Agent",
        "status": "operational",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "environment": settings.PAYTM_ENVIRONMENT}
