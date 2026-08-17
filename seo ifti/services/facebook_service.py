"""
Facebook / Meta Graph API Service.
Handles Facebook Page connection, automated daily posting, and feed synchronization.
"""

import logging
from typing import Any, Dict, List, Optional
import httpx

from config import settings

logger = logging.getLogger("socials_os.facebook")

GRAPH_API_VERSION = "v19.0"
GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class FacebookService:
    def __init__(self):
        self.page_id = settings.facebook_page_id
        self.page_access_token = settings.facebook_page_access_token
        self.user_access_token = settings.facebook_user_access_token

    def is_configured(self) -> bool:
        return bool(self.page_id and self.page_access_token)

    async def get_page_profile(self) -> Dict[str, Any]:
        """Fetches page metadata, follower counts, and connection health."""
        if not self.is_configured():
            return {
                "connected": False,
                "error": "Facebook Page ID or Page Access Token is missing from configuration.",
            }

        url = f"{GRAPH_BASE_URL}/{self.page_id}"
        params = {
            "fields": "id,name,about,fan_count,followers_count,link,category,verification_status",
            "access_token": self.page_access_token,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                data = response.json()

                if response.status_code != 200:
                    error_msg = data.get("error", {}).get("message", "Unknown Facebook API error")
                    logger.warning(f"Facebook Graph API error fetching page profile: {error_msg}")
                    return {
                        "connected": False,
                        "page_id": self.page_id,
                        "error": error_msg,
                        "raw_error": data.get("error"),
                    }

                return {
                    "connected": True,
                    "page_id": data.get("id", self.page_id),
                    "name": data.get("name", f"Facebook Page {self.page_id}"),
                    "about": data.get("about", "Active Business / Creator Page"),
                    "followers_count": data.get("followers_count", data.get("fan_count", 0)),
                    "fan_count": data.get("fan_count", 0),
                    "category": data.get("category", "Technology / Creator"),
                    "link": data.get("link", f"https://facebook.com/{self.page_id}"),
                }
        except Exception as e:
            logger.error(f"Failed to connect to Facebook Graph API: {e}")
            return {
                "connected": False,
                "page_id": self.page_id,
                "error": str(e),
            }

    async def publish_post(self, message: str, link: Optional[str] = None) -> Dict[str, Any]:
        """
        Publishes a status update or link to the Facebook Page feed.
        Uses Page Access Token for official page publication.
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Facebook Page credentials are not configured in .env",
            }

        url = f"{GRAPH_BASE_URL}/{self.page_id}/feed"
        payload = {
            "message": message,
            "access_token": self.page_access_token,
        }
        if link:
            payload["link"] = link

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(url, data=payload)
                data = response.json()

                if response.status_code != 200:
                    error_msg = data.get("error", {}).get("message", "Publishing failed")
                    logger.error(f"Facebook publish failed: {error_msg} | Response: {data}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "raw_error": data.get("error"),
                    }

                post_id = data.get("id")
                # Format post link: page_id_post_id -> https://facebook.com/{page_id}/posts/{post_id}
                clean_post_id = post_id.split("_")[-1] if post_id and "_" in post_id else post_id
                post_url = f"https://www.facebook.com/{self.page_id}/posts/{clean_post_id}"

                logger.info(f"Successfully published post to Facebook page {self.page_id}: {post_id}")
                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": post_url,
                    "data": data,
                }
        except Exception as e:
            logger.error(f"Exception while publishing to Facebook: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_recent_posts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves recent posts published on the Facebook Page."""
        if not self.is_configured():
            return []

        url = f"{GRAPH_BASE_URL}/{self.page_id}/feed"
        params = {
            "fields": "id,message,created_time,shares,permalink_url",
            "limit": limit,
            "access_token": self.page_access_token,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                if response.status_code != 200:
                    return []
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            logger.warning(f"Could not fetch recent Facebook posts: {e}")
            return []


facebook_service = FacebookService()
