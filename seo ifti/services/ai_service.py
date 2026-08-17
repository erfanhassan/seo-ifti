"""
DeepSeek AI Content Generation Service for Facebook & Twitter/X.
Specializes in high-converting Facebook posts, viral Twitter/X tweets, and daily topic generation.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI
from config import settings

logger = logging.getLogger("socials_os.ai_service")


def get_deepseek_client() -> AsyncOpenAI:
    """Returns an AsyncOpenAI client configured for DeepSeek API."""
    api_key = settings.deepseek_api_key or "sk-dummy-key"
    base_url = settings.deepseek_base_url or "https://api.deepseek.com"
    return AsyncOpenAI(api_key=api_key, base_url=base_url)


FACEBOOK_PROMPT = """
[System Persona]
You are an elite Social Media Manager and an AI Startup Founder writing content for Facebook in 2026. Your primary objective is to maximize organic reach and engagement by strictly adhering to the algorithm rules of Facebook ("Meaningful Interaction" Engine).

[Global Directives for 2026 Algorithms]
- No Engagement Bait: Never explicitly ask for likes, shares, or retweets.
- The Kicker: Always end every post with a thought-provoking, open-ended question that requires a subjective opinion to drive deep replies.
- Formatting: Avoid walls of text. Use single sentences and double line breaks to make scanning easy.

[Platform: Facebook - The "Meaningful Interaction" Engine]
Facebook's algorithm prioritizes Dwell Time and Community Replies.
Structure the post strictly as follows:
1. Hook (Pattern Interrupt): A contrarian or highly relatable statement that makes people stop scrolling.
2. The Story/Context: Share a real-world, grounded scenario or personal insight.
3. The Breakdown: 3 bullet points explaining the "how" or "why."
4. The Kicker: A debate-inducing question.

Constraints:
- Tone: Conversational, community-focused, and authentic.
- Length: 150-250 words.
- DO NOT use hashtags.
- DO NOT include external links or mentions of links in the post. Transition directly into The Kicker question.

Output valid JSON strictly adhering to:
{
  "title": "Short descriptive topic title",
  "content": "Full Facebook post structured with Hook, Story/Context, 3 Bullet Breakdown, and The Kicker question (150-250 words, zero hashtags, single sentences and double line breaks)"
}
"""

TWITTER_PROMPT = """
[System Persona]
You are an elite Social Media Manager and an AI Startup Founder writing content for Twitter (X) in 2026. Your primary objective is to maximize organic reach and engagement by strictly adhering to the algorithm rules of Twitter/X ("Reply Depth" Multiplier).

[Global Directives for 2026 Algorithms]
- No Engagement Bait: Never explicitly ask for likes, shares, or retweets.
- The Kicker: Always end the thread with a thought-provoking, open-ended question that requires a subjective opinion to drive deep replies.
- Formatting: Avoid walls of text. Use single sentences and double line breaks to make scanning easy.

[Platform: Twitter/X - The "Reply Depth" Multiplier]
X's algorithm rewards Reply Depth and early impressions.
Structure the 4-part thread strictly as follows:
- Tweet 1 (The Thread Hook): (1/4) A bold claim or surprising fact that opens a "curiosity gap."
- Tweet 2 (The Data/Insight): (2/4) The core mechanism, architecture, or business value behind the claim.
- Tweet 3 (The Application): (3/4) How businesses or developers can actually implement this today.
- Tweet 4 (The Call to Conversation): (4/4) A strong, slightly polarizing opinion followed by a question that begs for a counter-argument.

Constraints:
- Tone: Urgent, punchy, analytical, and highly opinionated.
- Length: Max 280 characters per tweet (strict constraint).
- Format: Use numbers (1/4, 2/4, 3/4, 4/4) to indicate it's a thread.
- Avoid generic filler words. Make every sentence hit hard.

Also provide a standalone "tweet" (<280 characters) summarizing the core punchy insight.

Output valid JSON strictly adhering to:
{
  "tweet": "Single punchy standalone tweet under 280 characters with curiosity hook and kicker question",
  "thread": [
    "1/4 [Bold claim / curiosity hook under 280 chars]",
    "2/4 [Core mechanism / data insight under 280 chars]",
    "3/4 [Actionable implementation / architecture under 280 chars]",
    "4/4 [Polarizing opinion + debate kicker question under 280 chars]"
  ]
}
"""

LINKEDIN_PROMPT = """
[System Persona]
You are an elite Social Media Strategist and a Bootstrapped AI Startup Founder writing high-converting thought-leadership content for LinkedIn in 2026. Your primary objective is to maximize Dwell Time and Meaningful Conversation Depth.

[LinkedIn 2026 Algorithm Rules]
1. The "See More" Hook: The first 2 lines must create a massive curiosity gap or contrarian stance that forces the user to click "...see more".
2. Format for Mobile: Short, punchy single sentences. Generous double line breaks (white space). Zero huge blocks of text.
3. No Outbound Links in Post Body: Do not include links or mentions of links. Transition directly from the insights into the closing kicker question.
4. Angle & Storytelling:
   - "The Bootstrapped AI Founder" persona.
   - Build in Public: real metrics, scaling hurdles (e.g. medical AI apps, Antigravity stack, Replit), unit economics, server costs.
   - Contrarian business frameworks (e.g., zero-cash physical ad network acquisitions, AI agent orchestration over syntax).
5. The Kicker: End with a thought-provoking, debate-inducing question that requires subjective experience to answer.
6. Zero Engagement Bait: Never explicitly ask for likes, reposts, or shares.

Output valid JSON strictly adhering to:
{
  "title": "Short descriptive topic title",
  "content": "Full LinkedIn post text formatted with the 2-line curiosity hook, double line breaks, founder insights, and closing kicker question (150-280 words)"
}
"""

DAILY_TOPIC_PROMPT = """
[System Persona]
You are an elite Social Media Manager and an AI Startup Founder writing content for Facebook, Twitter (X), and LinkedIn in 2026. Your primary objective is to maximize organic reach and engagement by strictly adhering to the algorithm rules of each platform.

[Global Directives for 2026 Algorithms]
- No Engagement Bait: Never explicitly ask for likes, shares, or retweets.
- The Kicker: Always end every post or thread with a thought-provoking, open-ended question that requires a subjective opinion to drive deep replies.
- Formatting: Avoid walls of text. Use single sentences and double line breaks to make scanning easy.

For Facebook:
- 150-250 words.
- Structure: Hook (Pattern Interrupt) -> Story/Context -> 3 Bullet Breakdown -> The Kicker debate question.
- No hashtags. No external links.

For Twitter/X:
- Standalone punchy tweet (< 280 chars) or 1st tweet of 4-part thread (< 280 chars) with high reply depth potential.

For LinkedIn:
- 150-280 words. The "See More" 2-line curiosity hook, mobile line breaks, Bootstrapped Founder persona, kicker question.

Output valid JSON:
{
  "topic": "The central theme / topic of the day",
  "facebook_content": "Full Facebook post following the 4-part structure (150-250 words, zero hashtags, double line breaks)",
  "twitter_content": "Single punchy tweet strictly under 280 characters with kicker question",
  "linkedin_content": "Full LinkedIn post formatted for mobile with 2-line curiosity hook and kicker question"
}
"""


async def generate_facebook_content(
    topic: str,
    custom_instructions: Optional[str] = None
) -> Dict[str, Any]:
    """Generates a Facebook post on the specified topic via DeepSeek AI adhering to 2026 algorithm rules."""
    if not settings.deepseek_api_key:
        return _fallback_facebook_post(topic)

    client = get_deepseek_client()
    user_prompt = f"Topic / Idea:\n{topic}"
    if custom_instructions:
        user_prompt += f"\n\nAdditional creator instructions:\n{custom_instructions}"

    try:
        response = await client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": FACEBOOK_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1500,
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception as e:
        logger.error(f"DeepSeek Facebook generation error: {e}")
        return _fallback_facebook_post(topic)


async def generate_twitter_content(
    topic: str,
    custom_instructions: Optional[str] = None
) -> Dict[str, Any]:
    """Generates Twitter/X tweets & 4-part threads on the specified topic via DeepSeek AI adhering to 2026 algorithm rules."""
    if not settings.deepseek_api_key:
        return _fallback_twitter_post(topic)

    client = get_deepseek_client()
    user_prompt = f"Topic / Idea:\n{topic}"
    if custom_instructions:
        user_prompt += f"\n\nAdditional creator instructions:\n{custom_instructions}"

    try:
        response = await client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": TWITTER_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1200,
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)

        # Enforce 280 char limit strictly
        if "tweet" in parsed and len(parsed["tweet"]) > 280:
            parsed["tweet"] = parsed["tweet"][:277] + "..."
        if "thread" in parsed and isinstance(parsed["thread"], list):
            parsed["thread"] = [
                t[:277] + "..." if len(t) > 280 else t for t in parsed["thread"]
            ]

        return parsed
    except Exception as e:
        logger.error(f"DeepSeek Twitter generation error: {e}")
        return _fallback_twitter_post(topic)


async def generate_linkedin_content(
    topic: str,
    custom_instructions: Optional[str] = None
) -> Dict[str, Any]:
    """Generates a high-converting LinkedIn post following Dwell Time and 'See More' hook optimization."""
    if not settings.deepseek_api_key:
        return _fallback_linkedin_post(topic)

    client = get_deepseek_client()
    user_prompt = f"Topic / Idea:\n{topic}"
    if custom_instructions:
        user_prompt += f"\n\nAdditional creator instructions:\n{custom_instructions}"

    try:
        response = await client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": LINKEDIN_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1500,
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception as e:
        logger.error(f"DeepSeek LinkedIn generation error: {e}")
        return _fallback_linkedin_post(topic)

        return parsed
    except Exception as e:
        logger.error(f"DeepSeek Twitter generation error: {e}")
        return _fallback_twitter_post(topic)


async def generate_daily_package(
    custom_topic: Optional[str] = None
) -> Dict[str, Any]:
    """Generates a complete daily content package for both Facebook and Twitter adhering to 2026 algorithm rules."""
    if not settings.deepseek_api_key:
        topic = custom_topic or "Scaling Autonomous AI Architecture in 2026"
        return {
            "topic": topic,
            "facebook_content": _fallback_facebook_post(topic).get("content", ""),
            "twitter_content": _fallback_twitter_post(topic).get("tweet", ""),
        }

    client = get_deepseek_client()
    prompt = f"Create today's daily growth content adhering to the 2026 algorithms. Topic focus: {custom_topic or 'Autonomous AI agents, founder engineering, and modern scalable system architecture'}."

    try:
        response = await client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": DAILY_TOPIC_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1800,
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)

        if "twitter_content" in parsed and len(parsed["twitter_content"]) > 280:
            parsed["twitter_content"] = parsed["twitter_content"][:277] + "..."

        return parsed
    except Exception as e:
        logger.error(f"DeepSeek daily package generation error: {e}")
        fallback_topic = custom_topic or "Autonomous Software Architecture"
        return {
            "topic": fallback_topic,
            "facebook_content": _fallback_facebook_post(fallback_topic).get("content", ""),
            "twitter_content": _fallback_twitter_post(fallback_topic).get("tweet", ""),
        }


# -----------------------------------------------------------------------------
# Fallback Templates
# -----------------------------------------------------------------------------
def _clean_topic_phrase(topic: str) -> str:
    cleaned = topic.strip().rstrip(".:-")
    if ":" in cleaned:
        parts = cleaned.split(":", 1)
        main_title = parts[0].strip()
        if len(main_title) >= 5:
            return main_title
    if len(cleaned) > 80:
        cleaned = cleaned[:77] + "..."
    return cleaned


def _fallback_facebook_post(topic: str) -> Dict[str, Any]:
    clean_topic = _clean_topic_phrase(topic)
    return {
        "title": f"{clean_topic}",
        "content": (
            f"Most founders and engineering leaders are approaching {clean_topic} completely backwards.\n\n"
            "Last month, our team threw away three weeks of work after realizing we were optimizing for shiny tooling instead of deterministic leverage.\n\n"
            "Here is the grounded reality of what actually works in production:\n\n"
            "• Stop chasing every new model update—master predictable task execution first.\n\n"
            "• Clean data pipelines and strict schema validation outperform clever prompt chaining every single time.\n\n"
            "• If your architecture requires human intervention on basic edge cases, it is not autonomous.\n\n"
            "The teams scaling in 2026 are not writing more boilerplate; they are ruthlessly eliminating friction from core operational loops.\n\n"
            "Where are you seeing the biggest bottleneck in deploying real-world systems right now: reliability, latency, or integration overhead?"
        ),
    }


def _fallback_linkedin_post(topic: str) -> Dict[str, Any]:
    clean_topic = _clean_topic_phrase(topic)
    return {
        "title": f"{clean_topic}",
        "content": (
            f"Most founders spend $50,000 on cloud infrastructure before validating their first 100 users.\n\n"
            f"Here is how we scaled our venture on {clean_topic} for under $100/month.\n\n"
            "When you build in public as a bootstrapped founder in 2026, the vanity metrics fade fast.\n\n"
            "Here is the exact playbook we used to eliminate friction and stay profitable from day 1:\n\n"
            "1. Lightweight frameworks beat heavy distributed setups.\n"
            "We swapped bulky microservices for streamlined Antigravity & SQLite execution loops. Latency dropped by 65% and our cloud bills flatlined.\n\n"
            "2. Deterministic AI workflows over raw prompt hype.\n"
            "Instead of hoping an LLM gets it right, we wrapped our agents in strict validation schemas. 99.4% task completion without manual intervention.\n\n"
            "3. Partnering for zero-cash distribution.\n"
            "Instead of burning ad spend, we tapped into existing supply chains and distribution networks. Instant monetization, zero acquisition debt.\n\n"
            "The future belongs to high-leverage solo operators and nimble teams running autonomous systems.\n\n"
            "What is the single biggest operational expense you eliminated this year that gave you the highest leverage?"
        ),
    }


def _fallback_twitter_post(topic: str) -> Dict[str, Any]:
    clean_topic = _clean_topic_phrase(topic)
    t1 = f"1/4 90% of teams building with {clean_topic} will fail this year because they confuse tool adoption with architectural leverage."
    if len(t1) > 280:
        t1 = t1[:277] + "..."

    return {
        "tweet": f"90% of teams building with {clean_topic} will fail this year because they confuse tool adoption with architectural leverage.\n\nSimplicity scales. Fragile prompt chains break.\n\nAre you prioritizing deterministic workflows or raw model hype?",
        "thread": [
            t1,
            "2/4 The core differentiator in 2026 is deterministic execution. If your autonomous agents fail 5% of the time on edge cases, your unit economics collapse in production.",
            "3/4 How top engineers fix this today: wrap models in rigid validation schemas, isolate state in SQLite/PostgreSQL, and build self-healing retry loops before writing a single user feature.",
            "4/4 Betting on raw model intelligence without deterministic guardrails is technical debt suicide.\n\nWhat is your biggest failure mode when deploying autonomous systems in production?",
        ],
    }

