# Antigravity Growth OS & Socials OS

**Socials OS** is an enterprise multi-agent social media growth, video transcoding, and autonomous engagement platform powered by FastAPI, SQLite, FFmpeg, and DeepSeek AI.

It is unified under a modern Top Navigation Bar supporting:
1. **GitHub**: Complete GitHub Developer Advocate & Open Source Growth Suite (8-point checklist, AI documentation, v1.0.0 releases).
2. **Socials**: Socials OS Multi-Agent Suite (The Grid Calendar, Sniper Copilot, Reddit Karma Tracker, Video Transcoder & Drive Lab).
3. **Website**: Modern Website Engine & Landing Page Generator preview.

---

## 🌟 Architecture Breakdown

```
├── config.py                     # App configuration (GitHub, DeepSeek, Socials, Reddit, FFmpeg)
├── database.py                   # SQLite + SQLAlchemy models & initial seeders
├── github_service.py             # GitHub Developer Advocate service
├── main.py                       # FastAPI application & 4-hour background scheduler
├── requirements.txt              # Production dependencies
│
├── services/
│   ├── ai_service.py             # DeepSeek copywriter (6 platforms), Sniper persona, Reddit founder persona
│   ├── ffmpeg_service.py         # Video quality control, probing, 1080p H.264 transcoding & routing
│   ├── scheduler_service.py      # Algorithmic SEO optimal posting times (get_optimal_post_time)
│   ├── sniper_service.py         # URL scraper & high-authority founder comment generator
│   ├── reddit_service.py         # PRAW/Reddit scanner (r/HealthTech, r/SaaS, r/MachineLearning, r/medicine)
│   └── social_api_service.py     # Unified Social API dispatcher (YouTube, FB, IG, TikTok, X, LinkedIn)
│
├── routers/
│   ├── github_router.py          # GitHub Advocate API endpoints
│   └── socials_router.py         # Socials OS API endpoints (Drive webhook, posts, sniper, reddit, transcode)
│
├── static/
│   ├── css/styles.css            # Dark glassmorphism styling & design tokens
│   └── js/
│       ├── app.js                # Top Nav Bar switcher (GitHub / Socials / Website)
│       ├── socials_view.js       # Socials OS dynamic UI logic & modals
│       └── github_view.js        # GitHub Advocate UI logic
│
└── templates/
    └── index.html                # Unified Master SPA template
```

---

## 🚀 Key Features

### 1. Multi-Platform Publisher & Transcoder (Google Drive Webhook)
- **Trigger**: Listens for video/image uploads and editor summaries via `/api/socials/drive-webhook`.
- **Quality Control (QC)**:
  - **Massive Raw Master (>2GB)**: Routed directly to **YouTube** and **Facebook** (lossless bitrate).
  - **Compressed Mobile Copy**: Transcoded with FFmpeg to **1080p, H.264, 30fps (<300MB)** for **Instagram, TikTok, and Twitter/X**.
- **DeepSeek 6-Platform Copywriter**:
  - **Facebook**: Community-driven, asks an open-ended question to drive comments.
  - **Instagram**: Story hook, 10-15 hyper-relevant SEO hashtags.
  - **LinkedIn**: Professional & authoritative, focuses on AI architecture, Bangladesh/global tech impact, clean line breaks.
  - **Twitter/X**: Punchy & concise (<280 chars).
  - **YouTube**: SEO-optimized title, description with timestamp chapters, tags.
  - **TikTok**: High-energy viral hook & trending tags.
- **SEO Scheduler**: `get_optimal_post_time(platform)` queues posts for algorithmic peak windows:
  - LinkedIn: Tue / Wed / Thu at 9:00 AM
  - TikTok: Tue / Thu at 7:00 PM
  - Instagram: Wed / Fri at 6:00 PM
  - Twitter/X: Mon / Wed / Fri at 8:00 AM & 12:00 PM
  - YouTube: Thu / Fri at 3:00 PM, Sat at 10:00 AM
  - Facebook: Mon / Wed / Fri at 1:00 PM

### 2. Sniper Copilot (URL-Triggered Engagement)
- Paste any LinkedIn, Twitter/X, Instagram, TikTok, or Reddit URL.
- Backend scrapes post context and passes it to DeepSeek.
- Persona: *"High-level digital networker and AI Founder"* generating 2-3 sentences of pure value.
- 1-click **Copy to Clipboard** for safe manual posting with zero ban risk.

### 3. Reddit Karma Builder
- Autonomous 4-hour background cron job (plus on-demand "Run Reddit Hunter Now").
- Scans target subreddits: `r/HealthTech`, `r/SaaS`, `r/MachineLearning`, `r/medicine`.
- DeepSeek senior founder persona drafts comprehensive technical answers (no marketing, no links).
- Posts natively via PRAW / Reddit API and tracks live upvote karma in SQLite.

---

## 🛠️ Setup & Execution

### 1. Environment Setup
```bash
cp .env.example .env
```
Ensure your `.env` contains your `DEEPSEEK_API_KEY` and any optional social/Reddit credentials.

### 2. Install Dependencies
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```
Open **http://localhost:8080** in your browser.
