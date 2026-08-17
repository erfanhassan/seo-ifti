"""
FastAPI Router for Socials OS (Facebook & Twitter/X Management Suite).
Handles account diagnostics, AI content generation, daily scheduling, and direct publishing.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import settings
from database import ActivityLog, DailyTopicSchedule, SocialPost, get_db
from services.ai_service import (
    generate_daily_package,
    generate_facebook_content,
    generate_twitter_content,
    generate_linkedin_content,
)
from services.facebook_service import facebook_service
from services.twitter_service import twitter_service

logger = logging.getLogger("socials_os.router")

router = APIRouter(prefix="/api/socials", tags=["Socials OS"])


# -----------------------------------------------------------------------------
# Request Schemas
# -----------------------------------------------------------------------------
class GenerateContentRequest(BaseModel):
    platform: str = Field(..., description="'facebook', 'twitter', or 'linkedin'")
    topic: str = Field(..., description="Topic or theme for the post")
    custom_instructions: Optional[str] = None


class CreatePostRequest(BaseModel):
    platform: str = Field(..., description="'facebook', 'twitter', or 'linkedin'")
    topic: Optional[str] = "Tech & AI Innovation"
    title: Optional[str] = None
    content: str = Field(..., description="Post message or tweet text")
    thread: Optional[List[str]] = None
    scheduled_at: Optional[str] = None  # ISO timestamp
    publish_now: Optional[bool] = False


class UpdatePostRequest(BaseModel):
    content: Optional[str] = None
    topic: Optional[str] = None
    title: Optional[str] = None
    scheduled_at: Optional[str] = None


class TriggerDailyRequest(BaseModel):
    custom_topic: Optional[str] = None
    auto_publish: Optional[bool] = False


# -----------------------------------------------------------------------------
# 1. Accounts Health & Diagnostics
# -----------------------------------------------------------------------------
@router.get("/accounts", summary="Get status of Facebook & Twitter connected accounts")
async def get_accounts_status():
    """Fetches real-time connection status for Facebook Page and Twitter / X."""
    fb_status = await facebook_service.get_page_profile()
    tw_status = await twitter_service.check_connection()

    return {
        "facebook": {
            "page_id": settings.facebook_page_id,
            "configured": facebook_service.is_configured(),
            "profile": fb_status,
        },
        "twitter": {
            "client_id": settings.twitter_client_id,
            "configured": twitter_service.is_configured(),
            "status": tw_status,
        },
        "linkedin": {
            "configured": True,
            "mode": "1-click copy & publish",
            "message": "LinkedIn 2026 Dwell Time & 'See More' algorithm generator active",
        },
    }


# -----------------------------------------------------------------------------
# 2. AI Content Generation
# -----------------------------------------------------------------------------
@router.post("/generate", summary="Generate AI post for Facebook, Twitter, or LinkedIn via DeepSeek")
async def generate_content(payload: GenerateContentRequest):
    """Generates platform-specific copy tailored for Facebook, Twitter/X, or LinkedIn."""
    platform = payload.platform.lower()
    
    if platform == "facebook":
        result = await generate_facebook_content(
            topic=payload.topic,
            custom_instructions=payload.custom_instructions,
        )
        return {
            "success": True,
            "platform": "facebook",
            "title": result.get("title", payload.topic),
            "content": result.get("content", ""),
        }
    elif platform in ("twitter", "x"):
        result = await generate_twitter_content(
            topic=payload.topic,
            custom_instructions=payload.custom_instructions,
        )
        return {
            "success": True,
            "platform": "twitter",
            "tweet": result.get("tweet", ""),
            "thread": result.get("thread", []),
        }
    elif platform == "linkedin":
        result = await generate_linkedin_content(
            topic=payload.topic,
            custom_instructions=payload.custom_instructions,
        )
        return {
            "success": True,
            "platform": "linkedin",
            "title": result.get("title", payload.topic),
            "content": result.get("content", ""),
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid platform. Must be 'facebook', 'twitter', or 'linkedin'.")


@router.post("/daily-package/generate", summary="Generate combined daily content for all platforms")
async def generate_daily_content(payload: TriggerDailyRequest):
    """Generates today's daily topic along with Facebook, Twitter, and LinkedIn copy."""
    package = await generate_daily_package(custom_topic=payload.custom_topic)
    return {"success": True, "package": package}


# -----------------------------------------------------------------------------
# 3. Posts Management (CRUD & Queue)
# -----------------------------------------------------------------------------
@router.get("/posts", summary="List all scheduled and published posts")
def list_posts(
    platform: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Returns posts filtered by platform and status."""
    query = db.query(SocialPost)
    if platform:
        query = query.filter(SocialPost.platform == platform.lower())
    if status_filter:
        query = query.filter(SocialPost.status == status_filter.lower())

    posts = query.order_by(SocialPost.created_at.desc()).all()
    return {"posts": [p.to_dict() for p in posts], "total": len(posts)}


@router.post("/posts", summary="Create or save a Facebook post, Tweet, or LinkedIn post")
async def create_post(payload: CreatePostRequest, db: Session = Depends(get_db)):
    """Creates a new post/tweet and optionally publishes it immediately."""
    platform = payload.platform.lower()
    if platform not in ("facebook", "twitter", "linkedin"):
        raise HTTPException(status_code=400, detail="Platform must be 'facebook', 'twitter', or 'linkedin'")

    post_uid = f"{platform[:2]}_{uuid.uuid4().hex[:8]}"
    
    # Parse schedule time if provided
    scheduled_dt = None
    if payload.scheduled_at:
        try:
            scheduled_dt = datetime.fromisoformat(payload.scheduled_at.replace("Z", "+00:00"))
        except Exception:
            pass

    post = SocialPost(
        post_uid=post_uid,
        platform=platform,
        topic=payload.topic or "Growth & Tech Strategy",
        title=payload.title or payload.topic or f"{platform.capitalize()} Post",
        content=payload.content,
        thread_json=json.dumps(payload.thread or []),
        status="scheduled" if not payload.publish_now else "draft",
        scheduled_at=scheduled_dt,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    # If publish_now requested, trigger direct API publish
    if payload.publish_now:
        return await execute_publish_post(post.id, db)

    return {"success": True, "post": post.to_dict()}


@router.put("/posts/{post_id}", summary="Update an existing scheduled post")
def update_post(post_id: int, payload: UpdatePostRequest, db: Session = Depends(get_db)):
    post = db.query(SocialPost).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if payload.content is not None:
        post.content = payload.content
    if payload.topic is not None:
        post.topic = payload.topic
    if payload.title is not None:
        post.title = payload.title
    if payload.scheduled_at is not None:
        try:
            post.scheduled_at = datetime.fromisoformat(payload.scheduled_at.replace("Z", "+00:00"))
        except Exception:
            pass

    db.commit()
    db.refresh(post)
    return {"success": True, "post": post.to_dict()}


@router.delete("/posts/{post_id}", summary="Delete a post")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(SocialPost).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    db.delete(post)
    db.commit()
    return {"success": True, "deleted_id": post_id}


# -----------------------------------------------------------------------------
# 4. Instant Publishing Direct to Platform
# -----------------------------------------------------------------------------
@router.post("/posts/{post_id}/publish", summary="Publish post immediately to Facebook or Twitter")
async def publish_post_endpoint(post_id: int, db: Session = Depends(get_db)):
    """Triggers instant live publication via Meta Graph API or Twitter API."""
    return await execute_publish_post(post_id, db)


async def execute_publish_post(post_id: int, db: Session) -> Dict[str, Any]:
    post = db.query(SocialPost).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.platform == "facebook":
        res = await facebook_service.publish_post(message=post.content)
        if res.get("success"):
            post.status = "published"
            post.remote_post_id = res.get("post_id")
            post.post_url = res.get("post_url")
            post.published_at = datetime.now(timezone.utc)
            post.error_message = None
        else:
            post.status = "failed"
            post.error_message = res.get("error", "Facebook publishing failed")

        try:
            log = ActivityLog(
                event_type="facebook_publish",
                platform="facebook",
                message=f"Facebook post {post.id} publish status: {post.status}",
                details_json=json.dumps(res),
            )
            db.add(log)
        except Exception as le:
            logger.warning(f"Could not record activity log: {le}")

        db.commit()
        db.refresh(post)
        return {"success": res.get("success", False), "result": res, "post": post.to_dict()}

    elif post.platform == "twitter":
        res = await twitter_service.publish_tweet(text=post.content)
        if res.get("success"):
            post.status = "published"
            post.remote_post_id = res.get("tweet_id")
            post.post_url = res.get("tweet_url")
            post.published_at = datetime.now(timezone.utc)
            post.error_message = None
        else:
            post.status = "failed"
            post.error_message = res.get("error", "Twitter publishing failed")

        try:
            log = ActivityLog(
                event_type="twitter_publish",
                platform="twitter",
                message=f"Twitter post {post.id} publish status: {post.status}",
                details_json=json.dumps(res),
            )
            db.add(log)
        except Exception as le:
            logger.warning(f"Could not record activity log: {le}")

        db.commit()
        db.refresh(post)
        return {"success": res.get("success", False), "result": res, "post": post.to_dict()}

    elif post.platform == "linkedin":
        post.status = "published"
        post.published_at = datetime.now(timezone.utc)
        post.error_message = None
        db.commit()
        db.refresh(post)
        return {
            "success": True,
            "result": {"success": True, "message": "Copied to clipboard and marked ready for LinkedIn!"},
            "post": post.to_dict(),
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported platform {post.platform}")


# -----------------------------------------------------------------------------
# 5. Daily Autonomous Generation & Scheduler Trigger
# -----------------------------------------------------------------------------
@router.post("/trigger-daily-cron", summary="Trigger today's autonomous post creation & scheduling")
async def trigger_daily_cron(
    payload: TriggerDailyRequest,
    db: Session = Depends(get_db)
):
    """
    Generates today's topic posts for both Facebook and Twitter.
    Queues them or immediately publishes them.
    """
    weekday_name = datetime.now(timezone.utc).strftime("%A")
    scheduled_topic = db.query(DailyTopicSchedule).filter_by(day_name=weekday_name, active=True).first()
    topic = payload.custom_topic or (scheduled_topic.topic if scheduled_topic else "Autonomous Software Systems in 2026")

    # Generate daily package via AI
    package = await generate_daily_package(custom_topic=topic)
    now = datetime.now(timezone.utc)

    # 1. Facebook Post
    fb_post = SocialPost(
        post_uid=f"fb_daily_{uuid.uuid4().hex[:6]}",
        platform="facebook",
        topic=topic,
        title=f"Facebook: {topic}",
        content=package.get("facebook_content", ""),
        status="scheduled" if not payload.auto_publish else "draft",
        scheduled_at=now,
    )
    db.add(fb_post)

    # 2. Twitter Post
    tw_post = SocialPost(
        post_uid=f"tw_daily_{uuid.uuid4().hex[:6]}",
        platform="twitter",
        topic=topic,
        title=f"Tweet: {topic}",
        content=package.get("twitter_content", ""),
        status="scheduled" if not payload.auto_publish else "draft",
        scheduled_at=now,
    )
    db.add(tw_post)
    db.commit()
    db.refresh(fb_post)
    db.refresh(tw_post)

    results = {"facebook": fb_post.to_dict(), "twitter": tw_post.to_dict()}

    if payload.auto_publish:
        fb_pub = await execute_publish_post(fb_post.id, db)
        tw_pub = await execute_publish_post(tw_post.id, db)
        results["facebook_publish"] = fb_pub
        results["twitter_publish"] = tw_pub

    return {
        "success": True,
        "topic": topic,
        "posts_created": results,
    }


# -----------------------------------------------------------------------------
# 6. Daily Topics Configuration
# -----------------------------------------------------------------------------
@router.get("/daily-topics", summary="Get weekly topic schedule")
def get_daily_topics(db: Session = Depends(get_db)):
    topics = db.query(DailyTopicSchedule).order_by(DailyTopicSchedule.id).all()
    return {"topics": [t.to_dict() for t in topics]}
