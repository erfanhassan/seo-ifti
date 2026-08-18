"""
Growth OS & Socials OS - Main Server Application.
Integrates GitHub Developer Advocate AI and Socials OS (Facebook & Twitter Management).
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from database import DailyTopicSchedule, SessionLocal, SocialPost, init_db
from routers.github_router import router as github_router
from routers.socials_router import router as socials_router
from services.ai_service import generate_daily_package
from services.facebook_service import facebook_service
from services.twitter_service import twitter_service

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=settings.log_level.upper(),
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("growth_os.main")

scheduler = AsyncIOScheduler()


async def scheduled_daily_socials_job():
    """Daily background task to generate and queue/post today's Facebook and Twitter content."""
    logger.info("Executing scheduled daily social media content creation for Facebook & Twitter...")
    db = SessionLocal()
    try:
        weekday_name = datetime.now(timezone.utc).strftime("%A")
        scheduled_topic = db.query(DailyTopicSchedule).filter_by(day_name=weekday_name, active=True).first()
        topic = scheduled_topic.topic if scheduled_topic else "Architecting Autonomous AI Software & Growth in 2026"

        package = await generate_daily_package(custom_topic=topic)
        now = datetime.now(timezone.utc)

        # 1. Queue Facebook post
        fb_post = SocialPost(
            post_uid=f"fb_daily_auto_{now.strftime('%Y%m%d')}",
            platform="facebook",
            topic=topic,
            title=f"Facebook: {topic}",
            content=package.get("facebook_content", ""),
            status="scheduled",
            scheduled_at=now,
        )
        db.add(fb_post)

        # 2. Queue Twitter post
        tw_post = SocialPost(
            post_uid=f"tw_daily_auto_{now.strftime('%Y%m%d')}",
            platform="twitter",
            topic=topic,
            title=f"Tweet: {topic}",
            content=package.get("twitter_content", ""),
            status="scheduled",
            scheduled_at=now,
        )
        db.add(tw_post)
        db.commit()

        logger.info(f"Daily social media posts successfully queued for {weekday_name} on topic: {topic}")
    except Exception as e:
        logger.error(f"Error in daily scheduled social media job: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Growth OS Database & Services...")
    init_db()
    os.makedirs(settings.media_storage_dir, exist_ok=True)
    os.makedirs("static/css", exist_ok=True)
    os.makedirs("static/js", exist_ok=True)

    # Start Daily Background Scheduler for Facebook & Twitter
    try:
        scheduler.add_job(
            scheduled_daily_socials_job,
            "interval",
            hours=24,
            id="daily_socials_job",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Daily Facebook & Twitter autonomous scheduler started successfully.")
    except Exception as e:
        logger.warning(f"Could not start APScheduler: {e}")

    yield

    # Shutdown
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler shut down.")


# -----------------------------------------------------------------------------
# Rate Limiting & Protection Middleware
# -----------------------------------------------------------------------------
import time
from collections import defaultdict
from fastapi.responses import JSONResponse

_ip_request_history: Dict[str, List[float]] = defaultdict(list)

def _is_rate_limited(ip: str, max_requests: int = 30, window_seconds: int = 60) -> bool:
    """Sliding-window IP rate limiter to protect backend from crawlers/scrapers."""
    now = time.time()
    history = _ip_request_history[ip]
    # Prune old requests outside the window
    _ip_request_history[ip] = [t for t in history if now - t < window_seconds]
    if len(_ip_request_history[ip]) >= max_requests:
        return True
    _ip_request_history[ip].append(now)
    return False


is_production = settings.environment.lower() == "production"

app = FastAPI(
    title="Growth OS & Socials OS",
    description="Unified Socials OS (Facebook & Twitter Management) and GitHub Developer Advocate Suite",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

# Global Rate Limiting Middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    # Protect AI and generation endpoints with strict rate limiting
    if path.startswith("/api/socials/generate") or path.startswith("/api/changes") or path.startswith("/api/socials/daily-package"):
        if _is_rate_limited(f"{client_ip}:ai", max_requests=settings.rate_limit_per_minute, window_seconds=60):
            logger.warning(f"Rate limit exceeded for IP {client_ip} on {path}")
            return JSONResponse(
                status_code=429,
                content={"success": False, "error": "Rate limit exceeded. Please wait a moment before generating again."},
            )
    elif path.startswith("/api/"):
        if _is_rate_limited(f"{client_ip}:general", max_requests=60, window_seconds=60):
            return JSONResponse(
                status_code=429,
                content={"success": False, "error": "Too many requests. Please slow down."},
            )

    response = await call_next(request)
    return response

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Routers
app.include_router(github_router)
app.include_router(socials_router)


# -----------------------------------------------------------------------------
# Root Dashboard Route
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
def get_dashboard():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/healthz", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "Growth OS & Socials OS",
        "version": "2.0.0",
        "deepseek_configured": bool(settings.deepseek_api_key),
        "facebook_configured": bool(settings.facebook_page_id and settings.facebook_page_access_token),
        "twitter_configured": bool(settings.twitter_api_key or settings.twitter_bearer_token),
        "github_configured": bool(settings.github_token),
        "database": "sqlite_active",
        "scheduler_running": scheduler.running if scheduler else False,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)
