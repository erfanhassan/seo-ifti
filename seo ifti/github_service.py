"""
GitHub Service Module - Enterprise Repository Advocate & Polish Suite.

Provides complete repository transformation capabilities:
1. Killer README with dynamic Status Badges & Visuals
2. Open Source MIT License (LICENSE)
3. Community Guidelines (CONTRIBUTING.md)
4. Contributor Covenant (CODE_OF_CONDUCT.md)
5. Stack-Specific .gitignore
6. Issue Templates (.github/ISSUE_TEMPLATE/bug_report.md, feature_request.md)
7. Pull Request Template (.github/PULL_REQUEST_TEMPLATE.md)
8. Repository About Description & Topics Synchronization
9. Official v1.0.0 Release Creation
"""

import base64
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from github import Auth, Github, GithubException
from github.GithubRetry import GithubRetry
from github.ContentFile import ContentFile
from github.Repository import Repository

logger = logging.getLogger("github_advocate.service")

# Directories to skip when scanning repository trees
IGNORED_DIRS: Set[str] = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    "dist",
    "build",
    "coverage",
    ".next",
    ".nuxt",
    "target",
    "bin",
    "obj",
    "vendor",
}

IGNORED_EXTENSIONS: Set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    ".mp4", ".mov", ".avi", ".zip", ".tar", ".gz", ".7z",
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", ".exe",
    ".bin", ".lock", ".map", ".min.js", ".min.css",
}

IMAGE_EXTENSIONS: Set[str] = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}

MANIFEST_FILENAMES: Set[str] = {
    "package.json", "pyproject.toml", "requirements.txt", "Pipfile",
    "setup.py", "setup.cfg", "Cargo.toml", "go.mod", "pom.xml",
    "build.gradle", "build.gradle.kts", "Gemfile", "composer.json",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
}

ENTRYPOINT_FILENAMES: Set[str] = {
    "main.py", "app.py", "server.py", "index.ts", "index.js",
    "server.ts", "server.js", "src/index.ts", "src/index.js",
    "src/main.py", "src/app.py", "src/App.tsx", "src/App.vue",
    "src/main.rs", "main.go", "cmd/main.go",
}


# ==============================================================================
# Standard Enterprise Open Source Templates
# ==============================================================================

def generate_mit_license(author_name: str = "Erfan Hassan", year: Optional[int] = None) -> str:
    """Generates a standard, legally binding MIT License."""
    current_year = year or datetime.now(timezone.utc).year
    return f"""MIT License

Copyright (c) {current_year} {author_name}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def generate_contributing_guide(owner_or_repo: str, repo_name: str = "", tech_stack_hint: str = "") -> str:
    """Generates a comprehensive CONTRIBUTING.md guide."""
    target_name = repo_name or owner_or_repo
    return f"""# 🤝 Contributing to {target_name}

Thank you for your interest in contributing to **{target_name}**! We welcome bug fixes, feature proposals, documentation improvements, and architectural enhancements from developers of all skill levels.

---

## 📜 Code of Conduct

All contributors and maintainers are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) to maintain a respectful and welcoming environment.

---

## 🛠️ Getting Started & Development Workflow

### 1. Fork & Clone
1. Fork the repository to your own GitHub account.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/{target_name}.git
   cd {target_name}
   ```

### 2. Create a Feature Branch
Always create a descriptive branch for your work:
```bash
git checkout -b feature/your-feature-name
# or for bugfixes
git checkout -b fix/issue-description
```

### 3. Local Environment Setup
{tech_stack_hint or "Install project dependencies using the standard package manager for this repository."}

### 4. Make Your Changes & Test
- Keep commits small, focused, and descriptive using Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`).
- Verify that your code builds and passes any existing automated tests.

---

## 🚀 Submitting a Pull Request (PR)

1. Push your branch to your GitHub fork:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Open a Pull Request against the `main` branch.
3. Fill in the Pull Request template with details about what changed, why, and how you tested it.
4. Maintainers will review your PR and provide constructive feedback.

---

## 🐛 Reporting Issues

- **Bug Reports**: Use our [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md) with reproduction steps and logs.
- **Feature Requests**: Use our [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md) explaining the problem and proposed solution.

Thank you for helping make **{target_name}** amazing! ⭐
"""


def generate_code_of_conduct(author_name: str = "Erfan Hassan", contact_email: str = "support@erfanhassan.com") -> str:
    """Generates the industry standard Contributor Covenant Code of Conduct v2.1."""
    return f"""# Contributor Covenant Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone, regardless of age, body
size, visible or invisible disability, ethnicity, sex characteristics, gender
identity and expression, level of experience, education, socio-economic status,
nationality, personal appearance, race, caste, color, religion, or sexual
identity and orientation.

We pledge to act and interact in ways that contribute to an open, welcoming,
diverse, inclusive, and healthy community.

## Our Standards

Examples of behavior that contributes to a positive environment for our
community include:

* Demonstrating empathy and kindness toward other people
* Being respectful of differing opinions, viewpoints, and experiences
* Giving and gracefully accepting constructive feedback
* Accepting responsibility and apologizing to those affected by our mistakes,
  and learning from the experience
* Focusing on what is best not just for us as individuals, but for the
  overall community

Examples of unacceptable behavior include:

* The use of sexualized language or imagery, and sexual attention or advances of
  any kind
* Trolling, insulting or derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or email
  address, without their explicit permission
* Other conduct which could reasonably be considered inappropriate in a
  professional setting

## Enforcement Responsibilities

Community leaders are responsible for clarifying and enforcing our standards of
acceptable behavior and will take appropriate and fair corrective action in
response to any behavior that they deem inappropriate, threatening, offensive,
or harmful.

## Scope

This Code of Conduct applies within all community spaces, and also applies when
an individual is officially representing the community in public spaces.

## Enforcement & Reporting

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported to the project maintainers ({author_name}) at [{contact_email}](mailto:{contact_email}).
All complaints will be reviewed and investigated promptly and fairly.
"""


def generate_gitignore(languages: Any = None) -> str:
    """Generates a multi-stack .gitignore covering Python, Node.js, Web, and macOS."""
    return """# ==============================================================================
# Enterprise Multi-Stack .gitignore
# ==============================================================================

# Operating System Files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
desktop.ini

# Environment Variables & Secrets
.env
.env.local
.env.*.local
*.env
*.pem
*.key
*.cert
credentials.json
service_account*.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.venv/
venv/
ENV/
env/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# Node.js & Web
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*
.pnpm-debug.log*
.next/
out/
.nuxt/
.vuepress/dist
.cache/
.parcel-cache/
.turbo/

# IDE & Editor Files
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json
.idea/
*.sublime-workspace
*.sublime-project
*.swp
*.swo

# Docker
*.log
docker-compose.override.yml
"""


def generate_bug_report_template() -> str:
    """Generates an issue template for bug reports."""
    return """---
name: 🐛 Bug Report
description: Create a report to help us fix an issue
title: "[BUG]: "
labels: ["bug", "triage"]
assignees: []
---

### 📝 Description
A clear and concise description of what the bug is.

### 🔁 Steps to Reproduce
1. Go to '...'
2. Run command '...'
3. See error

### 🎯 Expected Behavior
A clear and concise description of what you expected to happen.

### 📸 Screenshots & Logs
If applicable, add screenshots or terminal logs to help explain your problem.

```text
Paste logs here
```

### 💻 Environment
- **OS**: [e.g. macOS 14.2, Ubuntu 22.04, Windows 11]
- **Runtime / Version**: [e.g. Python 3.11, Node 20.x]
- **Browser (if applicable)**: [e.g. Chrome 120]

### 📌 Additional Context
Add any other context about the problem here.
"""


def generate_feature_request_template() -> str:
    """Generates an issue template for feature requests."""
    return """---
name: 🚀 Feature Request
description: Suggest an idea or enhancement for this project
title: "[FEAT]: "
labels: ["enhancement"]
assignees: []
---

### 💡 Is your feature request related to a problem? Please describe.
A clear and concise description of what the problem or limitation is. Ex. I'm always frustrated when [...]

### 🌟 Describe the solution you'd like
A clear and concise description of what you want to happen.

### 🔄 Describe alternatives you've considered
A clear and concise description of any alternative solutions or features you've considered.

### 📌 Additional context
Add any other context or screenshots about the feature request here.
"""


def generate_pr_template() -> str:
    """Generates a pull request template."""
    return """## 📌 Description
Please include a summary of the changes and the related issue.

Fixes # (issue)

## 🛠️ Type of Change
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] 🚀 New feature (non-breaking change which adds functionality)
- [ ] ⚡ Performance improvement
- [ ] 📝 Documentation update
- [ ] ♻️ Code refactoring / Cleanup

## ✅ Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have updated the documentation accordingly
- [ ] My changes generate no new warnings or build errors
- [ ] I have tested my changes locally
"""


# ==============================================================================
# Data Structures
# ==============================================================================

@dataclass
class RepoContext:
    """Structured context extracted from a repository to guide DeepSeek."""
    repo_name: str
    full_name: str
    description: str
    default_branch: str
    stars_count: int
    forks_count: int
    is_profile_repo: bool
    existing_topics: List[str]
    existing_readme: Optional[str]
    file_tree_summary: str
    language: str = "Python"
    manifest_contents: Dict[str, str] = field(default_factory=dict)
    sample_code_contents: Dict[str, str] = field(default_factory=dict)
    entrypoints_content: Dict[str, str] = field(default_factory=dict)
    discovered_images: List[str] = field(default_factory=list)
    existing_files: List[str] = field(default_factory=list)


@dataclass
class PolishBundle:
    """Complete bundle of 8 enterprise artifacts for a repository."""
    readme_md: str
    license_content: str
    contributing_md: str
    code_of_conduct_md: str
    gitignore_content: str
    bug_report_template: str
    feature_request_template: str
    pr_template: str
    topics: List[str]
    about_description: str
    release_tag: str
    release_name: str
    release_notes: str


# ==============================================================================
# GitHub Service Implementation
# ==============================================================================

class GitHubService:
    """
    High-level interface interacting with GitHub via PyGithub.
    Executes full 8-point repository transformations.
    """

    def __init__(self, github_token: str):
        if not github_token:
            raise ValueError("GITHUB_TOKEN is required to initialize GitHubService.")
        self._auth = Auth.Token(github_token)
        self._retry_config = GithubRetry(total=0)
        self._gh = Github(auth=self._auth, per_page=100, retry=self._retry_config)
        self._user_login: Optional[str] = None
        self._user_name: Optional[str] = None
        self._avatar_url: Optional[str] = None

    def get_authenticated_user_login(self) -> str:
        """Returns the username of the authenticated token owner."""
        if not self._user_login:
            user = self._gh.get_user()
            self._user_login = user.login
            self._user_name = user.name or user.login
            self._avatar_url = user.avatar_url
        return self._user_login

    def get_user_profile(self) -> Dict[str, Any]:
        """Returns user profile data for frontend consumption."""
        user = self._gh.get_user()
        return {
            "authenticated": True,
            "login": user.login,
            "name": user.name or user.login,
            "avatar_url": user.avatar_url,
            "bio": user.bio or "",
            "html_url": user.html_url,
            "public_repos": user.public_repos,
            "followers": user.followers,
            "following": user.following,
        }

    def get_user_profile_data(self) -> Dict[str, Any]:
        """Returns user profile metadata."""
        return self.get_user_profile()

    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Returns current rate limit metrics."""
        try:
            rl = self._gh.get_rate_limit()
            core = getattr(rl, "core", None) or getattr(getattr(rl, "resources", None), "core", None)
            if core:
                return {
                    "limit": core.limit,
                    "remaining": core.remaining,
                    "reset_timestamp": core.reset.timestamp() if hasattr(core.reset, "timestamp") else 0,
                }
            limit, remaining = self._gh.rate_limiting
            return {"limit": limit, "remaining": remaining, "reset_timestamp": 0}
        except Exception as e:
            logger.warning(f"Could not retrieve rate limit: {e}")
            return {"limit": 5000, "remaining": 5000, "reset_timestamp": 0}

    def get_repository(self, repo_name_or_full_name: str) -> Repository:
        """Fetches PyGithub Repository object."""
        if "/" in repo_name_or_full_name:
            return self._gh.get_repo(repo_name_or_full_name)
        login = self.get_authenticated_user_login()
        return self._gh.get_repo(f"{login}/{repo_name_or_full_name}")

    def list_public_repositories(self, username: Optional[str] = None) -> List[Repository]:
        """Lists all public, non-fork repositories."""
        target = username or self.get_authenticated_user_login()
        logger.info(f"Fetching public repositories for user: {target}")
        user = self._gh.get_user(target)
        repos = [r for r in user.get_repos(type="public", sort="updated", direction="desc") if not r.fork]
        logger.info(f"Found {len(repos)} public repositories.")
        return repos

    def list_repositories_with_status(self) -> Dict[str, Any]:
        """
        Returns full list of user repositories formatted for the Socials OS / GitHub Advocate UI.
        Uses ThreadPoolExecutor for high-speed concurrent repository auditing.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        login = self.get_authenticated_user_login()
        repos = self.list_public_repositories(login)

        def process_single_repo(r: Repository) -> Dict[str, Any]:
            default_branch = r.default_branch or "main"
            readme_len = 0
            has_readme = False

            try:
                cf = r.get_readme()
                if cf and cf.content:
                    raw = base64.b64decode(cf.content).decode("utf-8", errors="replace")
                    readme_len = len(raw)
                    has_readme = True
            except Exception:
                pass

            checklist = self.inspect_repo_polish_checklist(r)
            checklist["has_readme"] = has_readme
            is_profile = (r.name.lower() == login.lower())

            # Calculate 8-point score
            score_items = [
                checklist.get("has_readme", False),
                checklist.get("has_license", False),
                checklist.get("has_contributing", False),
                checklist.get("has_code_of_conduct", False),
                checklist.get("has_gitignore", False),
                checklist.get("has_issue_templates", False),
                checklist.get("has_pr_template", False),
                checklist.get("has_topics", False),
            ]
            score = sum(1 for item in score_items if item)
            score_pct = int((score / 8.0) * 100)

            return {
                "name": r.name,
                "full_name": r.full_name,
                "owner": login,
                "html_url": r.html_url,
                "description": r.description or "No description provided.",
                "default_branch": default_branch,
                "language": r.language or "Python",
                "stars": r.stargazers_count,
                "forks": r.forks_count,
                "topics": r.get_topics(),
                "has_readme": has_readme,
                "readme_length": readme_len,
                "is_profile_repo": is_profile,
                "checklist": checklist,
                "status": {
                    "has_readme": checklist.get("has_readme", False),
                    "has_license": checklist.get("has_license", False),
                    "has_contributing": checklist.get("has_contributing", False),
                    "has_code_of_conduct": checklist.get("has_code_of_conduct", False),
                    "has_gitignore": checklist.get("has_gitignore", False),
                    "has_issue_templates": checklist.get("has_issue_templates", False),
                    "has_pr_template": checklist.get("has_pr_template", False),
                    "has_topics": checklist.get("has_topics", False),
                    "score": score,
                },
                "health_score": score_pct,
                "updated_at": r.updated_at.isoformat() if r.updated_at else "",
            }

        repo_list = []
        with ThreadPoolExecutor(max_workers=min(12, len(repos) or 1)) as executor:
            futures = [executor.submit(process_single_repo, repo) for repo in repos]
            for future in as_completed(futures):
                try:
                    repo_list.append(future.result())
                except Exception as e:
                    logger.warning(f"Error scanning single repository: {e}")

        # Keep deterministic order (e.g., by name or updated)
        repo_list.sort(key=lambda x: x.get("name", "").lower())
        return {"repositories": repo_list}

    def inspect_repo_polish_checklist(self, repo: Repository) -> Dict[str, bool]:
        """
        Audits a repository against the 8-Point Professional Open Source Checklist.
        """
        default_branch = repo.default_branch or "main"
        checklist = {
            "has_readme": False,
            "has_license": False,
            "has_contributing": False,
            "has_code_of_conduct": False,
            "has_gitignore": False,
            "has_issue_templates": False,
            "has_pr_template": False,
            "has_topics": len(repo.get_topics()) >= 3,
            "has_release": False,
        }

        try:
            tree = repo.get_git_tree(sha=default_branch, recursive=True)
            paths = {e.path.lower() for e in tree.tree if e.type == "blob"}

            checklist["has_readme"] = any(p in paths for p in ["readme.md", "readme"])
            checklist["has_license"] = any("license" in p for p in paths)
            checklist["has_contributing"] = any("contributing" in p for p in paths)
            checklist["has_code_of_conduct"] = any("code_of_conduct" in p for p in paths)
            checklist["has_gitignore"] = ".gitignore" in paths or any(p.endswith(".gitignore") for p in paths)
            checklist["has_issue_templates"] = any(".github/issue_template" in p for p in paths)
            checklist["has_pr_template"] = any("pull_request_template" in p for p in paths)

        except Exception as e:
            logger.warning(f"Tree check failed for {repo.full_name}: {e}")

        # Check releases
        try:
            releases = list(repo.get_releases())
            checklist["has_release"] = len(releases) > 0
        except Exception:
            pass

        return checklist

    def get_repo_summary_list(self) -> List[Dict[str, Any]]:
        """
        Fetches summary data with 8-point checklist status for each repository.
        """
        login = self.get_authenticated_user_login()
        repos = self.list_public_repositories(login)
        summaries = []

        for r in repos:
            default_branch = r.default_branch or "main"
            readme_len = 0
            has_readme = False

            try:
                cf = r.get_readme()
                if cf and cf.content:
                    raw = base64.b64decode(cf.content).decode("utf-8", errors="replace")
                    readme_len = len(raw)
                    has_readme = True
            except Exception:
                pass

            checklist = self.inspect_repo_polish_checklist(r)
            checklist["has_readme"] = has_readme
            is_profile = (r.name.lower() == login.lower())

            # Calculate health score (0 - 100%)
            points = sum([1 for v in checklist.values() if v])
            score_pct = int((points / len(checklist)) * 100)

            summaries.append({
                "name": r.name,
                "full_name": r.full_name,
                "html_url": r.html_url,
                "description": r.description or "No description provided.",
                "default_branch": default_branch,
                "stars": r.stargazers_count,
                "forks": r.forks_count,
                "topics": r.get_topics(),
                "has_readme": has_readme,
                "readme_length": readme_len,
                "is_profile_repo": is_profile,
                "checklist": checklist,
                "health_score": score_pct,
                "updated_at": r.updated_at.isoformat() if r.updated_at else "",
            })

        return summaries

    def extract_repo_context(
        self,
        repo: Repository,
        max_tree_depth: int = 4,
        max_manifest_chars: int = 3000,
        max_code_chars: int = 4000,
    ) -> RepoContext:
        """
        Extracts codebase tree, manifests, code samples, and discovered image assets.
        """
        repo_name = repo.name
        full_name = repo.full_name
        description = repo.description or ""
        default_branch = repo.default_branch or "main"
        existing_topics = repo.get_topics()
        login = self.get_authenticated_user_login()
        is_profile_repo = (repo_name.lower() == login.lower())

        existing_readme: Optional[str] = None
        try:
            cf = repo.get_readme()
            if cf and cf.content:
                existing_readme = base64.b64decode(cf.content).decode("utf-8", errors="replace")
        except Exception:
            pass

        file_tree_paths: List[str] = []
        discovered_images: List[str] = []
        manifest_paths: List[str] = []
        entrypoint_paths: List[str] = []
        existing_files: Set[str] = set()

        try:
            tree = repo.get_git_tree(sha=default_branch, recursive=True)
            for element in tree.tree:
                path = element.path
                existing_files.add(path)
                parts = path.split("/")

                if any(part in IGNORED_DIRS or part.startswith(".") for part in parts[:-1]):
                    continue

                if element.type == "blob":
                    ext = "." + path.split(".")[-1].lower() if "." in path else ""
                    if ext in IMAGE_EXTENSIONS:
                        if any(k in path.lower() for k in ["asset", "screenshot", "img", "image", "doc", "demo", "preview"]):
                            discovered_images.append(path)

                    filename = parts[-1]
                    if filename in MANIFEST_FILENAMES:
                        manifest_paths.append(path)
                    elif path in ENTRYPOINT_FILENAMES or filename in ENTRYPOINT_FILENAMES:
                        entrypoint_paths.append(path)

                    if len(parts) <= max_tree_depth:
                        file_tree_paths.append(path)

        except Exception as e:
            logger.warning(f"Git tree traversal failed for {full_name}: {e}")

        tree_summary = "\n".join(file_tree_paths[:120])
        if len(file_tree_paths) > 120:
            tree_summary += f"\n... [{len(file_tree_paths) - 120} more files omitted]"

        manifest_contents: Dict[str, str] = {}
        for m_path in manifest_paths[:3]:
            try:
                cf = repo.get_contents(m_path, ref=default_branch)
                if isinstance(cf, ContentFile) and cf.content:
                    raw = base64.b64decode(cf.content).decode("utf-8", errors="replace")
                    manifest_contents[m_path] = raw[:max_manifest_chars]
            except Exception:
                pass

        sample_code_contents: Dict[str, str] = {}
        for e_path in entrypoint_paths[:2]:
            try:
                cf = repo.get_contents(e_path, ref=default_branch)
                if isinstance(cf, ContentFile) and cf.content:
                    raw = base64.b64decode(cf.content).decode("utf-8", errors="replace")
                    sample_code_contents[e_path] = raw[:max_code_chars]
            except Exception:
                pass

        # Combine manifests and code samples into entrypoints_content
        entrypoints_content = {**manifest_contents, **sample_code_contents}

        return RepoContext(
            repo_name=repo_name,
            full_name=full_name,
            description=description,
            default_branch=default_branch,
            stars_count=repo.stargazers_count,
            forks_count=repo.forks_count,
            is_profile_repo=is_profile_repo,
            existing_topics=existing_topics,
            existing_readme=existing_readme,
            file_tree_summary=tree_summary,
            language=repo.language or "Python",
            manifest_contents=manifest_contents,
            sample_code_contents=sample_code_contents,
            entrypoints_content=entrypoints_content,
            discovered_images=discovered_images,
            existing_files=list(existing_files),
        )

    def scan_repository_context(self, owner: str, repo: str) -> RepoContext:
        """Adapter method to scan repository context by owner and repo name."""
        repository = self.get_repository(f"{owner}/{repo}")
        return self.extract_repo_context(repository)

    def apply_batch_changes(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        changes: Optional[List[Dict[str, str]]] = None,
        commit_message: str = "chore(advocate): polish repository documentation and templates",
    ) -> Dict[str, Any]:
        """Applies a list of file changes to the repository."""
        repository = self.get_repository(f"{owner}/{repo}")
        results = []
        changes_list = changes or []
        for change in changes_list:
            path = change.get("path")
            content = change.get("content", "")
            if path:
                try:
                    res = self.write_file_safe(
                        repo=repository,
                        file_path=path,
                        content=content,
                        commit_message=commit_message,
                    )
                    results.append(res)
                except Exception as e:
                    results.append({"path": path, "status": "permission_restricted", "error": str(e)})
        return {"success": True, "files_updated": len(results), "details": results}

    def sync_repository_metadata(
        self,
        owner: str,
        repo: str,
        description: Optional[str] = None,
        topics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Synchronizes repository About description and SEO topics."""
        repository = self.get_repository(f"{owner}/{repo}")
        updated_desc = False
        applied_topics = []
        permission_restricted = False
        error_msg = None

        if description:
            try:
                updated_desc = self.update_about_section(repository, description=description)
            except GithubException as ge:
                if ge.status == 403:
                    permission_restricted = True
                    error_msg = "Fine-grained token requires 'Administration: Read and Write' permission to edit repository About description."
                logger.warning(f"Could not update description for {owner}/{repo}: {ge}")
            except Exception as e:
                logger.warning(f"Could not update description for {owner}/{repo}: {e}")

        if topics:
            try:
                applied_topics = self.update_topics(repository, raw_topics=topics)
            except GithubException as ge:
                if ge.status == 403:
                    permission_restricted = True
                    error_msg = "Fine-grained token requires 'Administration: Read and Write' permission to set repository Topics."
                logger.warning(f"Could not replace topics for {owner}/{repo}: {ge}")
            except Exception as e:
                logger.warning(f"Could not replace topics for {owner}/{repo}: {e}")

        return {
            "description_updated": updated_desc,
            "topics_applied": applied_topics,
            "permission_restricted": permission_restricted,
            "permission_note": error_msg,
        }

    def write_file_safe(
        self,
        repo: Repository,
        file_path: str,
        content: str,
        commit_message: str = "chore: add enterprise open source polish [skip ci]",
    ) -> Dict[str, Any]:
        """
        Creates or updates a file on the default branch without slow retries on 403.
        """
        default_branch = repo.default_branch or "main"
        try:
            try:
                existing = repo.get_contents(file_path, ref=default_branch)
                if isinstance(existing, ContentFile):
                    res = repo.update_file(
                        path=file_path,
                        message=commit_message,
                        content=content,
                        sha=existing.sha,
                        branch=default_branch,
                    )
                    return {"path": file_path, "status": "updated", "sha": res["commit"].sha}
            except GithubException as ge:
                if ge.status == 403:
                    raise ge
                pass

            res = repo.create_file(
                path=file_path,
                message=commit_message,
                content=content,
                branch=default_branch,
            )
            return {"path": file_path, "status": "created", "sha": res["commit"].sha}

        except GithubException as e:
            logger.warning(f"Could not write {file_path} on {repo.full_name} ({e.status}): {e.data if hasattr(e, 'data') else e}")
            raise

    def update_topics(self, repo: Repository, raw_topics: List[str]) -> List[str]:
        """Sanitizes and replaces topics for the repository."""
        sanitized: List[str] = []
        for topic in raw_topics:
            t = re.sub(r"[^a-z0-9\-]", "-", topic.strip().lower()).strip("-")
            if t and len(t) <= 35 and t not in sanitized:
                sanitized.append(t)

        final_topics = sanitized[:15]
        if final_topics:
            repo.replace_topics(final_topics)
            logger.info(f"Updated topics for {repo.full_name}: {final_topics}")
        return final_topics

    def update_about_section(self, repo: Repository, description: str, homepage: Optional[str] = None) -> bool:
        """Updates the repository short description and homepage URL."""
        if not description:
            return False
        cleaned_desc = description.strip()[:350]
        kwargs: Dict[str, Any] = {"description": cleaned_desc}
        if homepage:
            kwargs["homepage"] = homepage
        repo.edit(**kwargs)
        logger.info(f"Updated About section for {repo.full_name}")
        return True

    def create_initial_release(
        self,
        repo: Optional[Any] = None,
        owner: Optional[str] = None,
        release_notes: Optional[str] = None,
        tag: str = "v1.0.0",
        name: str = "v1.0.0 - Production Release",
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates formal GitHub Release with release notes (supports repo object or owner/repo strings)."""
        target_repo = repo
        if isinstance(repo, str) and owner:
            target_repo = self.get_repository(f"{owner}/{repo}")
        elif isinstance(repo, str):
            target_repo = self.get_repository(repo)
        elif repo is None and owner:
            target_repo = self.get_repository(owner)

        if not target_repo or not hasattr(target_repo, "default_branch"):
            return {"tag": tag, "status": "failed", "error": "Invalid repository"}

        default_branch = target_repo.default_branch or "main"
        release_msg = message or release_notes or "Initial production release with comprehensive documentation and open source community standards."

        try:
            for rel in target_repo.get_releases():
                if rel.tag_name == tag:
                    return {"tag": tag, "status": "already_exists", "html_url": rel.html_url}

            release = target_repo.create_git_release(
                tag=tag,
                name=name,
                message=release_msg,
                target_commitish=default_branch,
                draft=False,
                prerelease=False,
            )
            logger.info(f"Created release {tag} for {target_repo.full_name}")
            return {"tag": tag, "status": "created", "html_url": release.html_url}
        except Exception as e:
            logger.warning(f"Could not create release {tag} for {target_repo.full_name}: {e}")
            return {"tag": tag, "status": "failed", "error": str(e)}

    @staticmethod
    def is_agent_commit(commit_message: str) -> bool:
        """Detects if a commit originated from the agent to prevent infinite loops."""
        if not commit_message:
            return False
        indicators = [
            "[skip ci]",
            "auto-generate comprehensive readme",
            "audit & enhance readme",
            "enterprise open source polish",
            "github developer advocate ai agent",
            "docs(readme):",
        ]
        msg_lower = commit_message.lower()
        return any(ind in msg_lower for ind in indicators)
