import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.observability.tracer import init_tracer, flush_traces, shutdown_traces
from app.models.database import init_db
from app.api import health, search, profiles, research, saved

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("founder-radar")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize Neatlogs tracer before any model activity
    logger.info("Initializing Neatlogs telemetry and OTLP instrumentation...")
    init_tracer()

    # 2. Initialize database schema
    logger.info("Initializing SQLite database schema...")
    init_db()

    yield

    # Shutdown: flush and close traces
    logger.info("Flushing Neatlogs traces...")
    flush_traces()
    shutdown_traces()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Global Founder Intelligence Platform — Discover founders, investigate signals, and organize research.",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(health.router)
app.include_router(search.router)
app.include_router(profiles.router)
app.include_router(research.router)
app.include_router(saved.router)


@app.get("/")
def home():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs_url": "/docs",
        "health_url": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)