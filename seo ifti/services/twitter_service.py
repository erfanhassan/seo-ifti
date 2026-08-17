"""
Twitter / X API v2 Service.
Handles Twitter connection diagnostics, AI tweet formatting, single tweets, and threads.
"""

import logging
from typing import Any, Dict, List, Optional
import httpx
import tweepy

from config import settings

logger = logging.getLogger("socials_os.twitter")


class TwitterService:
    def __init__(self):
        self.api_key = settings.twitter_api_key
        self.api_secret = settings.twitter_api_secret
        self.access_token = settings.twitter_access_token
        self.access_token_secret = settings.twitter_access_token_secret
        self.bearer_token = settings.twitter_bearer_token
        self.client_id = settings.twitter_client_id
        self.client_secret = settings.twitter_client_secret

    def is_configured(self) -> bool:
        return bool(self.api_key or self.bearer_token or self.client_id or self.access_token)

    def get_tweepy_client(self) -> Optional[tweepy.Client]:
        """Initializes a Tweepy v2 Client with available credentials."""
        try:
            # If OAuth 1.0a User Context is configured, prioritize it for posting without Bearer token conflict
            if self.api_key and self.api_secret and self.access_token and self.access_token_secret:
                return tweepy.Client(
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret,
                )
            # Otherwise use Bearer token or available keys
            return tweepy.Client(
                bearer_token=self.bearer_token or None,
                consumer_key=self.api_key or None,
                consumer_secret=self.api_secret or None,
            )
        except Exception as e:
            logger.warning(f"Could not build Tweepy client: {e}")
            return None

    async def check_connection(self) -> Dict[str, Any]:
        """Tests connection to Twitter API v2 using User Context / Tweepy and Bearer Token."""
        if not self.is_configured():
            return {
                "connected": False,
                "error": "Twitter API credentials not configured in .env",
            }

        # 1. If User Access Token is available, verify via Tweepy get_me
        if self.api_key and self.api_secret and self.access_token and self.access_token_secret:
            try:
                client = self.get_tweepy_client()
                if client:
                    me = client.get_me(user_auth=True)
                    if me and me.data:
                        return {
                            "connected": True,
                            "user_id": str(me.data.id),
                            "name": me.data.name,
                            "username": me.data.username,
                            "handle": f"@{me.data.username}",
                            "has_user_auth": True,
                            "has_bearer_token": bool(self.bearer_token),
                            "message": f"Connected as @{me.data.username} ({me.data.name}). Direct posting active.",
                        }
            except Exception as e:
                logger.warning(f"Tweepy get_me check encountered error: {e}")

        # 2. Fallback to Bearer token inspection
        return {
            "connected": bool(self.api_key or self.bearer_token),
            "client_id": self.client_id,
            "has_bearer_token": bool(self.bearer_token),
            "has_consumer_keys": bool(self.api_key and self.api_secret),
            "message": "Twitter / X credentials loaded from .env.",
        }

    async def publish_tweet(self, text: str) -> Dict[str, Any]:
        """
        Publishes a single tweet (<280 characters) to Twitter / X.
        Uses Twitter API v2 POST /2/tweets.
        """
        if not text or not text.strip():
            return {"success": False, "error": "Tweet content cannot be empty."}

        clean_text = text.strip()
        if len(clean_text) > 280:
            clean_text = clean_text[:277] + "..."

        # 1. Try Tweepy v2 Client with OAuth 1.0a User Context
        try:
            client = self.get_tweepy_client()
            if client:
                has_user_auth = bool(self.access_token and self.access_token_secret)
                resp = client.create_tweet(text=clean_text, user_auth=has_user_auth)
                if resp and resp.data:
                    tweet_id = resp.data.get("id")
                    tweet_url = f"https://x.com/i/web/status/{tweet_id}"
                    logger.info(f"Successfully published Tweet ID: {tweet_id}")
                    return {
                        "success": True,
                        "tweet_id": str(tweet_id),
                        "tweet_url": tweet_url,
                        "text": clean_text,
                    }
        except tweepy.errors.HTTPException as he:
            err_details = str(he)
            if "credits depleted" in err_details.lower() or he.response.status_code == 402:
                msg = "Twitter API error 402 (Credits Depleted / Payment Required). Your Twitter Developer App credits may need renewal in the X Developer Portal."
            elif he.response.status_code == 403:
                msg = "Twitter API error 403 (Forbidden). Check that your App permissions are set to 'Read and Write' in the X Developer Portal."
            else:
                msg = f"Twitter API error: {he}"
            logger.warning(f"Tweepy create_tweet HTTPException: {msg}")
            return {"success": False, "error": msg}
        except Exception as e:
            logger.warning(f"Tweepy create_tweet exception: {e}. Trying direct HTTP fallback...")

        # 2. Direct HTTP v2 Request fallback (if OAuth 2.0 user Bearer is provided)
        if self.bearer_token:
            try:
                headers = {
                    "Authorization": f"Bearer {self.bearer_token}",
                    "Content-Type": "application/json",
                }
                payload = {"text": clean_text}

                async with httpx.AsyncClient(timeout=20.0) as http_client:
                    response = await http_client.post(
                        "https://api.twitter.com/2/tweets",
                        json=payload,
                        headers=headers,
                    )
                    data = response.json()

                    if response.status_code in (200, 201):
                        tweet_data = data.get("data", {})
                        tweet_id = tweet_data.get("id", "unknown")
                        tweet_url = f"https://x.com/i/web/status/{tweet_id}"
                        return {
                            "success": True,
                            "tweet_id": str(tweet_id),
                            "tweet_url": tweet_url,
                            "text": clean_text,
                        }
                    else:
                        error_msg = data.get("detail") or data.get("title") or str(data)
                        logger.error(f"Twitter API v2 error: {error_msg}")
                        return {
                            "success": False,
                            "error": error_msg,
                            "raw_response": data,
                        }
            except Exception as ex:
                logger.error(f"Exception posting tweet: {ex}")
                return {"success": False, "error": str(ex)}

        return {"success": False, "error": "Twitter publish failed. Ensure your X Developer App has Read and Write permissions."}

    async def publish_thread(self, tweets: List[str]) -> Dict[str, Any]:
        """Publishes a sequential thread of tweets to Twitter / X."""
        if not tweets:
            return {"success": False, "error": "No tweets in thread."}

        published_ids = []
        last_tweet_id = None

        for idx, text in enumerate(tweets):
            try:
                # Post with in_reply_to_tweet_id if subsequent tweet
                client = self.get_tweepy_client()
                if client:
                    has_user_auth = bool(self.access_token and self.access_token_secret)
                    if last_tweet_id:
                        resp = client.create_tweet(text=text, in_reply_to_tweet_id=last_tweet_id, user_auth=has_user_auth)
                    else:
                        resp = client.create_tweet(text=text, user_auth=has_user_auth)

                    if resp and resp.data:
                        t_id = resp.data.get("id")
                        last_tweet_id = t_id
                        published_ids.append(str(t_id))
            except Exception as e:
                logger.error(f"Error publishing thread item {idx}: {e}")
                break

        if published_ids:
            first_id = published_ids[0]
            return {
                "success": True,
                "thread_ids": published_ids,
                "thread_url": f"https://x.com/i/web/status/{first_id}",
                "count": len(published_ids),
            }
        else:
            return {"success": False, "error": "Failed to publish thread items."}


twitter_service = TwitterService()
