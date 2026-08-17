"""
Global Application Configuration for Growth OS & Socials OS (Facebook & Twitter/X Management).
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Core Server
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8080")))
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    environment: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "production"))
    admin_api_key: str = Field(default_factory=lambda: os.getenv("ADMIN_API_KEY", "admin_sec_growth_suite_2026"))
    webhook_secret: str = Field(default_factory=lambda: os.getenv("WEBHOOK_SECRET", "whsec_growth_suite_2026"))

    # GitHub Service (Preserved)
    github_token: str = Field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))

    # DeepSeek AI Reasoning
    deepseek_api_key: str = Field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    deepseek_base_url: str = Field(
        default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    )
    deepseek_model: str = Field(
        default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    )

    # Database
    database_url: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./socials_os.db")
    )

    # Facebook / Meta Graph API
    facebook_page_id: str = Field(default_factory=lambda: os.getenv("FACEBOOK_PAGE_ID", ""))
    facebook_page_access_token: str = Field(default_factory=lambda: os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", ""))
    facebook_user_access_token: str = Field(default_factory=lambda: os.getenv("FACEBOOK_USER_ACCESS_TOKEN", ""))

    # Twitter / X API
    twitter_api_key: str = Field(default_factory=lambda: os.getenv("TWITTER_API_KEY", ""))
    twitter_api_secret: str = Field(default_factory=lambda: os.getenv("TWITTER_API_SECRET", ""))
    twitter_access_token: str = Field(default_factory=lambda: os.getenv("TWITTER_ACCESS_TOKEN", ""))
    twitter_access_token_secret: str = Field(default_factory=lambda: os.getenv("TWITTER_ACCESS_TOKEN_SECRET", ""))
    twitter_bearer_token: str = Field(default_factory=lambda: os.getenv("TWITTER_BEARER_TOKEN", ""))
    twitter_client_id: str = Field(default_factory=lambda: os.getenv("TWITTER_CLIENT_ID", ""))
    twitter_client_secret: str = Field(default_factory=lambda: os.getenv("TWITTER_CLIENT_SECRET", ""))

    # Storage
    media_storage_dir: str = Field(
        default_factory=lambda: os.getenv("MEDIA_STORAGE_DIR", "./media_storage")
    )

    class Config:
        case_sensitive = False
        extra = "ignore"


settings = Settings()
