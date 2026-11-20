import io
import re
import zipfile
import requests
from typing import List, Dict
from app.config import GITHUB_TOKEN

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".cpp", ".c", ".h", ".go",
    ".rs", ".html", ".css", ".sql", ".md", ".json", ".yaml", ".yml"
}

IGNORED_DIRS = {
    "node_modules", ".git", "__pycache__", "venv", ".venv",
    "dist", "build", ".next", "coverage"
}


def parse_github_url(repo_url: str) -> tuple[str, str]:
    pattern = r"github\.com/([^/]+)/([^/]+)"
    match = re.search(pattern, repo_url.strip().rstrip("/"))
    if not match:
        raise ValueError("Invalid GitHub repository URL.")
    owner, repo = match.group(1), match.group(2).removesuffix(".git")
    return owner, repo


def get_headers() -> Dict[str, str]:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def fetch_repo_files(repo_url: str) -> List[Dict[str, str]]:
    """Poori repository ko ek single ZIP stream mein download karke 2 second mein files nikalta hai."""
    owner, repo = parse_github_url(repo_url)
    headers = get_headers()

    print(f"[Loader] Fetching repo info for {owner}/{repo}...")
    repo_info_url = f"https://api.github.com/repos/{owner}/{repo}"
    repo_resp = requests.get(repo_info_url, headers=headers, timeout=15)
    repo_resp.raise_for_status()
    default_branch = repo_resp.json().get("default_branch", "main")

    zip_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{default_branch}"
    print(f"[Loader] Downloading ZIP archive from {default_branch}...")
    zip_resp = requests.get(zip_url, headers=headers, timeout=30)
    zip_resp.raise_for_status()

    documents = []
    with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as zf:
        for file_info in zf.infolist():
            if file_info.is_dir():
                continue

            # Remove folder naem from a ZIP Folder (e.g., "repo-main/app/main.py" -> "app/main.py")
            full_path = file_info.filename
            parts = full_path.split("/", 1)
            if len(parts) < 2 or not parts[1]:
                continue
            clean_path = parts[1]

            path_parts = clean_path.split("/")
            if any(part in IGNORED_DIRS for part in path_parts):
                continue

            if not any(clean_path.endswith(ext) for ext in ALLOWED_EXTENSIONS):
                continue

            try:
                content = zf.read(file_info.filename).decode("utf-8")
                if content.strip():
                    documents.append({
                        "path": clean_path,
                        "content": content
                    })
            except UnicodeDecodeError:
                continue

    print(f"[Loader] Extracted {len(documents)} code files!")
    return documents