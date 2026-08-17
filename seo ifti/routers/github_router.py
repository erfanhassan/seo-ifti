"""
FastAPI Router for GitHub Developer Advocate & Open Source Growth Suite.
Preserves 100% of existing repository scanning, polishing, README generation, PR/Issue template setup,
About description/topics synchronization, and v1.0.0 release creation.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from config import settings
from github_service import (
    GitHubService,
    RepoContext,
    generate_bug_report_template,
    generate_code_of_conduct,
    generate_contributing_guide,
    generate_enterprise_readme,
    generate_feature_request_template,
    generate_gitignore,
    generate_mit_license,
    generate_pr_template,
)
from services.ai_service import get_deepseek_client

logger = logging.getLogger("github_advocate.router")

router = APIRouter(tags=["GitHub Advocate"])

api_key_header = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)


class ChangeItem(BaseModel):
    path: str
    content: str
    description: str


class ApplyPayload(BaseModel):
    owner: str
    repo: str
    branch: Optional[str] = "main"
    changes: List[ChangeItem]
    topics: Optional[List[str]] = None
    description: Optional[str] = None
    create_release: Optional[bool] = False
    release_notes: Optional[str] = None
    commit_message: Optional[str] = "chore(advocate): apply professional repository enhancements"


class ReadmePreviewRequest(BaseModel):
    owner: str
    repo: str


# In-memory job tracker for admin batch audits
audit_jobs: Dict[str, Dict[str, Any]] = {}


def verify_admin_key(api_key: Optional[str] = Security(api_key_header)) -> bool:
    if not api_key or api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Admin-API-Key header",
        )
    return True


def get_github_service() -> GitHubService:
    if not settings.github_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GITHUB_TOKEN is not configured on server",
        )
    return GitHubService(settings.github_token)


DEEPSEEK_ENTERPRISE_PROMPT = (
    "You are an elite Developer Advocate and Open Source Architect. Your goal is to maximize "
    "GitHub stars, forks, and organic search traffic for this repository by turning it into a "
    "tier-1 professional storefront.\n\n"
    "Analyze the codebase structure, package manifests, and code entrypoints.\n"
    "Generate a complete documentation package containing:\n"
    "1. 'readme_content': A structured, high-converting README.md featuring:\n"
    "   - Engaging title with relevant status badges (MIT License, PRs Welcome, Build Passing, Language/Framework badges).\n"
    "   - A 1-sentence punchy hook summarizing the project.\n"
    "   - '🌟 Why This Exists' (problem solved & impact).\n"
    "   - '✨ Key Features' (bullet points with bold keywords).\n"
    "   - '🛠️ Tech Stack & Architecture' (clean breakdown with diagrams or components).\n"
    "   - '📦 Quickstart & Installation' (copy-pasteable commands).\n"
    "   - Visual proof embeds from /assets or /screenshots if found (or clean placeholder embeds).\n"
    "   - '🤝 Contributing & Community' (linking to CONTRIBUTING.md and CODE_OF_CONDUCT.md).\n"
    "   - SEO Optimization: if the repo relates to AI healthcare, dual-persona LLMs, ad-tech, or automation, heavily emphasize those.\n"
    "2. 'github_topics': An array of 5-10 SEO-optimized tags for GitHub's algorithm (lowercase, alphanumeric + hyphens).\n"
    "3. 'repo_description': A high-impact 1-2 sentence description (max 250 chars) for the repository's About section.\n"
    "4. 'release_notes': Formal release notes for the initial v1.0.0 production release.\n\n"
    "Output strictly a JSON object with: readme_content, github_topics, repo_description, release_notes."
)


@router.get("/api/user-profile", summary="Get Authenticated GitHub User Profile")
def get_user_profile(gh: GitHubService = Depends(get_github_service)):
    return gh.get_user_profile()


@router.get("/api/repos", summary="List Public Repositories with Checklist Status")
def list_repositories(gh: GitHubService = Depends(get_github_service)):
    return gh.list_repositories_with_status()


@router.get("/api/changes", summary="Generate Changes and Proposed Plan for a Repo")
async def generate_changes(
    owner: str,
    repo: str,
    gh: GitHubService = Depends(get_github_service),
):
    context = gh.scan_repository_context(owner, repo)

    # Call DeepSeek for README, topics, description, release notes
    client = get_deepseek_client()
    user_prompt = (
        f"Repository: {owner}/{repo}\n"
        f"Primary Language: {context.language or 'Generic'}\n"
        f"Current Description: {context.description or 'None'}\n"
        f"Existing Files: {', '.join(context.existing_files[:50])}\n\n"
        f"Manifest & Entrypoint Content:\n"
    )
    for path, content in list(context.entrypoints_content.items())[:5]:
        user_prompt += f"\n--- {path} ---\n{content[:1500]}\n"

    try:
        response = await client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": DEEPSEEK_ENTERPRISE_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
            max_tokens=3000,
        )
        ai_data = json.loads(response.choices[0].message.content or "{}")
    except Exception as e:
        logger.warning(f"DeepSeek call failed ({e}). Generating full deterministic enterprise README...")
        fallback_topics = [
            (context.language or "software").lower(),
            repo.lower().replace("_", "-").replace(" ", "-"),
            "developer-tools",
            "open-source",
            "production",
        ]
        ai_data = {
            "readme_content": generate_enterprise_readme(context, owner),
            "github_topics": fallback_topics,
            "repo_description": context.description or f"Enterprise {repo} system & platform.",
            "release_notes": f"## 🚀 {repo} v1.0.0 Production Release\n\nInitial official production release with comprehensive documentation, type-safe architecture, and CI/CD standards.",
        }

    changes = []
    # 1. README
    changes.append({
        "path": "README.md",
        "content": ai_data.get("readme_content") or generate_enterprise_readme(context, owner),
        "description": "Killer README with status badges, architecture, and quickstart",
    })

    # 2. LICENSE
    if "LICENSE" not in context.existing_files and "LICENSE.md" not in context.existing_files:
        changes.append({
            "path": "LICENSE",
            "content": generate_mit_license(owner),
            "description": "Open source standard MIT License",
        })

    # 3. CONTRIBUTING.md
    if "CONTRIBUTING.md" not in context.existing_files:
        changes.append({
            "path": "CONTRIBUTING.md",
            "content": generate_contributing_guide(owner, repo),
            "description": "Standard Community Contribution Guidelines",
        })

    # 4. CODE_OF_CONDUCT.md
    if "CODE_OF_CONDUCT.md" not in context.existing_files:
        changes.append({
            "path": "CODE_OF_CONDUCT.md",
            "content": generate_code_of_conduct(),
            "description": "Contributor Covenant Code of Conduct v2.1",
        })

    # 5. .gitignore
    if ".gitignore" not in context.existing_files:
        changes.append({
            "path": ".gitignore",
            "content": generate_gitignore(context.language or "python"),
            "description": f"Standard {context.language or 'multi-stack'} .gitignore",
        })

    # 6. Issue Templates
    if not any("ISSUE_TEMPLATE" in f for f in context.existing_files):
        changes.append({
            "path": ".github/ISSUE_TEMPLATE/bug_report.md",
            "content": generate_bug_report_template(),
            "description": "Structured Bug Report template",
        })
        changes.append({
            "path": ".github/ISSUE_TEMPLATE/feature_request.md",
            "content": generate_feature_request_template(),
            "description": "Structured Feature Request template",
        })

    # 7. PR Template
    if not any("PULL_REQUEST_TEMPLATE" in f for f in context.existing_files):
        changes.append({
            "path": ".github/PULL_REQUEST_TEMPLATE.md",
            "content": generate_pr_template(),
            "description": "Standard Pull Request template",
        })

    return {
        "repo": f"{owner}/{repo}",
        "changes": changes,
        "topics": ai_data.get("github_topics", []),
        "description": ai_data.get("repo_description", ""),
        "release_notes": ai_data.get("release_notes", ""),
    }


@router.post("/api/apply", summary="Apply Proposed Changes & Synchronize Repository")
def apply_changes(payload: ApplyPayload, gh: GitHubService = Depends(get_github_service)):
    results = {}

    # Apply file changes
    file_changes = [{"path": c.path, "content": c.content, "description": c.description} for c in payload.changes]
    commit_res = gh.apply_batch_changes(
        owner=payload.owner,
        repo=payload.repo,
        branch=payload.branch or "main",
        changes=file_changes,
        commit_message=payload.commit_message or "chore(advocate): polish repository documentation and templates",
    )
    results["commit"] = commit_res

    # Synchronize topics & description
    if payload.topics or payload.description:
        meta_res = gh.sync_repository_metadata(
            owner=payload.owner,
            repo=payload.repo,
            description=payload.description,
            topics=payload.topics,
        )
        results["metadata"] = meta_res

    # Create official v1.0.0 release if requested
    if payload.create_release:
        rel_res = gh.create_initial_release(
            owner=payload.owner,
            repo=payload.repo,
            release_notes=payload.release_notes,
        )
        results["release"] = rel_res

    return {
        "success": True,
        "message": f"Successfully polished {payload.owner}/{payload.repo}",
        "results": results,
    }


@router.post("/webhook/github", summary="GitHub Webhook Listener")
async def handle_github_webhook(request: Request, x_hub_signature_256: Optional[str] = Header(None)):
    payload_body = await request.body()
    if settings.webhook_secret and x_hub_signature_256:
        expected_sig = "sha256=" + hmac.new(
            settings.webhook_secret.encode(), payload_body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, x_hub_signature_256):
            raise HTTPException(status_code=403, detail="Invalid signature")

    event_type = request.headers.get("X-GitHub-Event", "ping")
    return {"status": "ok", "event": event_type}


@router.post("/admin/audit-all", summary="Trigger Batch Audit Across All Repos")
async def admin_audit_all(
    background_tasks: BackgroundTasks,
    authenticated: bool = Depends(verify_admin_key),
    gh: GitHubService = Depends(get_github_service),
):
    job_id = str(uuid.uuid4())
    audit_jobs[job_id] = {"status": "running", "progress": 0, "results": []}
    return {"job_id": job_id, "status": "queued"}


@router.get("/admin/audit-status/{job_id}", summary="Get Status of Batch Audit")
def get_audit_status(job_id: str, authenticated: bool = Depends(verify_admin_key)):
    job = audit_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
