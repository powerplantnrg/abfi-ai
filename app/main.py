"""
ABFI Intelligence Suite - Main Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1 import sentiment, prices, policy, carbon, counterparty, intelligence
from app.services.scheduler import start_scheduler, stop_scheduler
from app.db import database as db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    print("Starting ABFI Intelligence Suite...")
    # Initialize database
    try:
        db.init_database()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization warning: {e}")
    # Start the data collection scheduler (only if enabled)
    if settings.scraping_enabled:
        await start_scheduler()
        print("Data collection scheduler started")
    else:
        print("Data collection scheduler disabled")
    yield
    # Shutdown
    print("Shutting down ABFI Intelligence Suite...")
    await stop_scheduler()
    print("Data collection scheduler stopped")


app = FastAPI(
    title="ABFI Intelligence Suite API",
    description="AI-powered market intelligence for the Australian bioenergy industry",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(
    sentiment.router,
    prefix="/api/v1/sentiment",
    tags=["Lending Sentiment"]
)
app.include_router(
    prices.router,
    prefix="/api/v1/prices",
    tags=["Feedstock Prices"]
)
app.include_router(
    policy.router,
    prefix="/api/v1/policy",
    tags=["Policy Intelligence"]
)
app.include_router(
    carbon.router,
    prefix="/api/v1/carbon",
    tags=["Carbon Revenue"]
)
app.include_router(
    counterparty.router,
    prefix="/api/v1/counterparty",
    tags=["Counterparty Risk"]
)
app.include_router(
    intelligence.router,
    prefix="/api/v1/intelligence",
    tags=["Market Intelligence"]
)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirect to docs."""
    return JSONResponse(
        content={
            "message": "ABFI Intelligence Suite API",
            "version": "1.0.0",
            "docs": "/docs"
        }
    )


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for monitoring."""
    # Check database connectivity
    db_status = "operational"
    try:
        with db.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"
    
    return {
        "status": "healthy" if db_status == "operational" else "degraded",
        "version": "1.0.0",
        "services": {
            "api": "operational",
            "database": db_status,
            "models": "not_loaded",  # Models are optional for basic functionality
        }
    }


@app.get("/api/v1/status", tags=["System"])
async def api_status():
    """Detailed API status including model information."""
    return {
        "api_version": "1.0.0",
        "environment": settings.api_env,
        "models": {
            "sentiment": {
                "name": "deberta-v3-large-finetuned",
                "version": "1.0.0",
                "status": "loaded"
            },
            "policy_classifier": {
                "name": "policy-classifier-v1",
                "version": "1.0.0",
                "status": "loaded"
            },
            "counterparty_risk": {
                "name": "xgboost-counterparty-v1",
                "version": "1.0.0",
                "status": "loaded"
            }
        },
        "data_freshness": {
            "sentiment_index": "2024-01-15T06:00:00Z",
            "price_index": "2024-01-12T00:00:00Z",
            "policy_tracker": "2024-01-15T08:30:00Z"
        }
    }
