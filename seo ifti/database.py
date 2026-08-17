"""
Database configuration and SQLAlchemy ORM models for Socials OS (Facebook & Twitter/X).
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

from config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=False,
)

SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

Base = declarative_base()


class SocialPost(Base):
    """Stores Facebook posts and Twitter/X tweets & threads."""
    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    post_uid = Column(String(64), unique=True, index=True)
    platform = Column(String(32), nullable=False, index=True)  # 'facebook' or 'twitter'
    topic = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    thread_json = Column(Text, default="[]")  # JSON array for multi-tweet threads
    status = Column(String(32), default="scheduled", index=True)  # 'draft', 'scheduled', 'published', 'failed'
    
    post_url = Column(String(512), nullable=True)
    remote_post_id = Column(String(128), nullable=True)
    error_message = Column(Text, nullable=True)
    
    scheduled_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def thread(self) -> List[str]:
        try:
            return json.loads(self.thread_json or "[]")
        except Exception:
            return []

    @thread.setter
    def thread(self, value: List[str]):
        self.thread_json = json.dumps(value)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "post_uid": self.post_uid,
            "platform": self.platform,
            "topic": self.topic or "Growth & Tech Strategy",
            "title": self.title or self.topic or f"{self.platform.capitalize()} Post",
            "content": self.content,
            "thread": self.thread,
            "status": self.status,
            "post_url": self.post_url,
            "remote_post_id": self.remote_post_id,
            "error_message": self.error_message,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DailyTopicSchedule(Base):
    """Configurable schedule of daily topics for automated content creation."""
    __tablename__ = "daily_topics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    day_name = Column(String(32), nullable=False)  # Monday, Tuesday, etc.
    topic = Column(String(255), nullable=False)
    custom_instructions = Column(Text, nullable=True)
    active = Column(Boolean, default=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "day_name": self.day_name,
            "topic": self.topic,
            "custom_instructions": self.custom_instructions,
            "active": self.active,
        }


class ActivityLog(Base):
    """System activity, publishing logs, and webhook events."""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_type = Column(String(64), nullable=False, index=True)
    platform = Column(String(32), nullable=True)
    message = Column(Text, nullable=False)
    details_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "platform": self.platform,
            "message": self.message,
            "details": json.loads(self.details_json or "{}"),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def get_db():
    """FastAPI Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Creates database tables, applies migrations, and seeds initial schedule and posts if empty."""
    Base.metadata.create_all(bind=engine)
    
    # Safe SQLite column migration
    try:
        with engine.connect() as conn:
            # Migration: Ensure platform and created_at exist in activity_logs
            cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(activity_logs);").fetchall()]
            if cols and "platform" not in cols:
                conn.exec_driver_sql("ALTER TABLE activity_logs ADD COLUMN platform VARCHAR(32);")
            if cols and "created_at" not in cols:
                conn.exec_driver_sql("ALTER TABLE activity_logs ADD COLUMN created_at DATETIME;")
            conn.commit()
    except Exception as me:
        logger.warning(f"Database migration check notice: {me}")

    db = SessionLocal()
    try:
        # Seed daily topic schedule if none exist
        if db.query(DailyTopicSchedule).count() == 0:
            topics = [
                DailyTopicSchedule(day_name="Monday", topic="Architecting Autonomous AI Multi-Agent Workflows in 2026", active=True),
                DailyTopicSchedule(day_name="Tuesday", topic="Eliminating Software Engineering Friction with Deterministic Systems", active=True),
                DailyTopicSchedule(day_name="Wednesday", topic="Scaling Tech Startups & Open Source Communities Globally", active=True),
                DailyTopicSchedule(day_name="Thursday", topic="Next-Gen Developer Experience, Tooling & Automation", active=True),
                DailyTopicSchedule(day_name="Friday", topic="AI-Assisted Code Quality, CI/CD, and Production Stability", active=True),
                DailyTopicSchedule(day_name="Saturday", topic="Weekend Breakdown: High-Impact Lessons from Building Modern Software", active=True),
                DailyTopicSchedule(day_name="Sunday", topic="Weekly Retrospective & The Future of Intelligent Software", active=True),
            ]
            db.add_all(topics)
            db.commit()

        # Seed initial posts for Facebook and Twitter if none exist
        if db.query(SocialPost).count() == 0:
            now = datetime.now(timezone.utc)
            sample_fb = SocialPost(
                post_uid="fb_post_initial_01",
                platform="facebook",
                topic="AI Multi-Agent Systems",
                title="The Shift to Deterministic AI Systems",
                content=(
                    "🚀 We are witnessing a massive paradigm shift in how modern software is built.\n\n"
                    "The bottleneck is no longer model intelligence—it's deterministic orchestration, auditability, and eliminating repetitive operational friction.\n\n"
                    "By combining structured AI workflows with reliable automation, development teams can reclaim over 15 hours every single week.\n\n"
                    "How are you utilizing AI automation in your daily development or workflow today? Let's discuss in the comments below! 👇\n\n"
                    "#AI #SoftwareEngineering #Automation #TechInnovation #Growth"
                ),
                status="scheduled",
                scheduled_at=now + timedelta(hours=2),
            )

            sample_tw = SocialPost(
                post_uid="tw_post_initial_01",
                platform="twitter",
                topic="Autonomous Software Architecture",
                title="Why Simplicity Scales",
                content="The secret to autonomous software isn't doing more work—it's building deterministic automation that executes reliably every single day.\n\nSimplicity scales. Complexity breaks. ⚡ #Tech #AI #Developer",
                status="scheduled",
                scheduled_at=now + timedelta(hours=3),
            )

            sample_li = SocialPost(
                post_uid="li_post_initial_01",
                platform="linkedin",
                topic="The Bootstrapped AI Stack",
                title="Scaling to 1,000 Users on <$100/mo",
                content=(
                    "Most founders spend $50,000 on cloud infrastructure before validating their first 100 users.\n\n"
                    "Here is how we scaled our medical AI workflow for doctors to 1,000 active users for under $100/month.\n\n"
                    "When you build in public as a bootstrapped AI founder in 2026, the vanity metrics fade fast.\n\n"
                    "Here is the exact playbook we used to eliminate friction and stay profitable from day 1:\n\n"
                    "1. Lightweight frameworks beat heavy AWS infrastructure.\n"
                    "We swapped bulky microservices for streamlined Antigravity & SQLite execution loops. Latency dropped by 65% and our cloud bills flatlined.\n\n"
                    "2. Deterministic AI workflows over raw prompt hype.\n"
                    "Instead of hoping an LLM gets it right, we wrapped our agents in strict validation schemas. 99.4% task completion without manual intervention.\n\n"
                    "3. Partnering for zero-cash distribution.\n"
                    "Instead of burning ad spend, we tapped into existing supply chains and distribution networks. Instant monetization, zero acquisition debt.\n\n"
                    "The future belongs to high-leverage solo operators and nimble teams running autonomous systems.\n\n"
                    "What is the single biggest operational expense you eliminated this year that gave you the highest leverage?"
                ),
                status="published",
                scheduled_at=now + timedelta(hours=4),
            )

            db.add_all([sample_fb, sample_tw, sample_li])
            db.commit()

        # Ensure at least one LinkedIn post exists if none
        if db.query(SocialPost).filter_by(platform="linkedin").count() == 0:
            now = datetime.now(timezone.utc)
            sample_li = SocialPost(
                post_uid="li_post_initial_01",
                platform="linkedin",
                topic="The Bootstrapped AI Stack",
                title="Scaling to 1,000 Users on <$100/mo",
                content=(
                    "Most founders spend $50,000 on cloud infrastructure before validating their first 100 users.\n\n"
                    "Here is how we scaled our medical AI workflow for doctors to 1,000 active users for under $100/month.\n\n"
                    "When you build in public as a bootstrapped AI founder in 2026, the vanity metrics fade fast.\n\n"
                    "Here is the exact playbook we used to eliminate friction and stay profitable from day 1:\n\n"
                    "1. Lightweight frameworks beat heavy AWS infrastructure.\n"
                    "We swapped bulky microservices for streamlined Antigravity & SQLite execution loops. Latency dropped by 65% and our cloud bills flatlined.\n\n"
                    "2. Deterministic AI workflows over raw prompt hype.\n"
                    "Instead of hoping an LLM gets it right, we wrapped our agents in strict validation schemas. 99.4% task completion without manual intervention.\n\n"
                    "3. Partnering for zero-cash distribution.\n"
                    "Instead of burning ad spend, we tapped into existing supply chains and distribution networks. Instant monetization, zero acquisition debt.\n\n"
                    "The future belongs to high-leverage solo operators and nimble teams running autonomous systems.\n\n"
                    "What is the single biggest operational expense you eliminated this year that gave you the highest leverage?"
                ),
                status="published",
                scheduled_at=now,
            )
            db.add(sample_li)
            db.commit()

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()
