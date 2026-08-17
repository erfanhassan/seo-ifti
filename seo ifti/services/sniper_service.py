"""
Sniper Copilot Service: URL-Triggered High-Authority Social Comment Generator.
"""

import logging
import re
from typing import Any, Dict, Optional
import httpx
from bs4 import BeautifulSoup

from database import SessionLocal, SniperEngagement
from services.ai_service import generate_sniper_comment

logger = logging.getLogger("socials_os.sniper_service")


class SniperService:
    @staticmethod
    def detect_platform(url: str) -> str:
        u = url.lower()
        if "linkedin.com" in u:
            return "linkedin"
        elif "twitter.com" in u or "x.com" in u:
            return "twitter"
        elif "instagram.com" in u:
            return "instagram"
        elif "facebook.com" in u or "fb.com" in u:
            return "facebook"
        elif "tiktok.com" in u:
            return "tiktok"
        elif "reddit.com" in u:
            return "reddit"
        elif "youtube.com" in u or "youtu.be" in u:
            return "youtube"
        elif "substack.com" in u or "medium.com" in u:
            return "blog"
        return "general"

    async def scrape_url_context(self, url: str) -> Dict[str, str]:
        """Fetches page content and extracts OpenGraph / Twitter metadata and text body."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        detected_platform = self.detect_platform(url)

        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")

                    # Try OpenGraph & Meta tags
                    og_title = (
                        soup.find("meta", property="og:title")
                        or soup.find("meta", attrs={"name": "twitter:title"})
                    )
                    og_desc = (
                        soup.find("meta", property="og:description")
                        or soup.find("meta", attrs={"name": "description"})
                        or soup.find("meta", attrs={"name": "twitter:description"})
                    )
                    author_meta = (
                        soup.find("meta", attrs={"name": "author"})
                        or soup.find("meta", property="article:author")
                    )

                    title_text = og_title["content"].strip() if og_title and og_title.get("content") else ""
                    desc_text = og_desc["content"].strip() if og_desc and og_desc.get("content") else ""
                    author_text = author_meta["content"].strip() if author_meta and author_meta.get("content") else ""

                    # If page has paragraphs, gather body snippet
                    paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 30]
                    body_snippet = " ".join(paragraphs[:3])[:800]

                    context_parts = []
                    if title_text:
                        context_parts.append(f"Title/Headline: {title_text}")
                    if desc_text:
                        context_parts.append(f"Post Content: {desc_text}")
                    if body_snippet and body_snippet not in desc_text:
                        context_parts.append(f"Context: {body_snippet}")

                    full_context = "\n".join(context_parts)
                    if not full_context.strip():
                        full_context = f"Discussion on {detected_platform.capitalize()} regarding industry tech and AI innovation."

                    return {
                        "platform": detected_platform,
                        "author": author_text or self._extract_author_from_url(url),
                        "context": full_context[:1200],
                        "source": "scraped",
                    }
        except Exception as e:
            logger.warning(f"Live scrape failed for {url}: {e}")

        # Graceful fallback heuristic context
        return {
            "platform": detected_platform,
            "author": self._extract_author_from_url(url),
            "context": self._generate_fallback_context(url, detected_platform),
            "source": "heuristic",
        }

    def _extract_author_from_url(self, url: str) -> str:
        parts = url.replace("https://", "").replace("http://", "").split("/")
        if len(parts) > 1 and parts[1]:
            candidate = parts[1].replace("@", "").split("?")[0]
            if candidate not in ["posts", "p", "status", "comments", "reel", "watch"]:
                return candidate.replace("-", " ").title()
        return "Tech Leader"

    def _generate_fallback_context(self, url: str, platform: str) -> str:
        slug = url.split("?")[0].rstrip("/").split("/")[-1].replace("-", " ")
        return (
            f"High-impact post on {platform.capitalize()} regarding engineering scalability, "
            f"agentic workflows, and market execution. ({slug})"
        )

    async def execute_sniper_flow(
        self,
        url: str,
        tone: str = "Authority Founder",
        manual_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs complete scraping -> DeepSeek founder persona -> SQLite logging."""
        scraped = await self.scrape_url_context(url)
        context = manual_context.strip() if manual_context and manual_context.strip() else scraped["context"]
        platform = scraped["platform"]
        author = scraped["author"]

        comment = await generate_sniper_comment(
            scraped_context=context,
            platform=platform,
            tone=tone,
            author_name=author,
        )

        # Save to database
        db = SessionLocal()
        try:
            engagement = SniperEngagement(
                url=url,
                platform=platform,
                author_name=author,
                scraped_context=context,
                generated_comment=comment,
                persona_used="high_level_founder",
                tone=tone,
                copied_to_clipboard=False,
            )
            db.add(engagement)
            db.commit()
            db.refresh(engagement)
            record_id = engagement.id
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving SniperEngagement: {e}")
            record_id = 1
        finally:
            db.close()

        return {
            "id": record_id,
            "url": url,
            "platform": platform,
            "author": author,
            "scraped_context": context,
            "generated_comment": comment,
            "tone": tone,
            "persona": "High-Level Digital Networker & AI Founder",
            "copy_ready": True,
        }


sniper_service = SniperService()
