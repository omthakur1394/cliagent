import requests
import base64

import os

# --- Config ---
MAX_FILES = 2
MAX_TOKENS_PER_FILE = 1000
SKIP_EXTENSIONS = [
    '.min.js', '.lock', '.csv', '.png', '.svg',
    '.jpg', '.jpeg', '.gif', '.ico', '.pdf',
    '.zip', '.exe', '.env', '.txt', '.md', '.ipynb'
]

def estimate_tokens(text: str) -> int:
    # rough estimate: 1 token ≈ 4 characters
    return len(text) // 4

def should_skip(filename: str) -> bool:
    for ext in SKIP_EXTENSIONS:
        if filename.endswith(ext):
            return True
    return False

def get_file_content(owner: str, repo: str, path: str) -> str | None:
    try:
        headers = {"Accept": "application/vnd.github+json"}
        github_token = os.environ.get("GITHUB_TOKEN", "")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
            headers=headers
        )
        data = response.json()

        if data.get("encoding") == "base64":
            content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            return content
        return None

    except Exception:
        return None

def get_filtered_files(repo_url: str) -> list:
    try:
        parts = repo_url.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]

        headers = {"Accept": "application/vnd.github+json"}
        github_token = os.environ.get("GITHUB_TOKEN", "")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        # get repo file tree
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"[token_limiter] GitHub API Error: {response.status_code} - {response.text}")
            return []

        tree = response.json().get("tree", [])

        files = []

        for item in tree:
            path = item.get("path", "")
            item_type = item.get("type", "")

            # only process files, skip dirs and unwanted extensions
            if item_type != "blob" or should_skip(path):
                continue

            files.append(path)

        print(f"[token_limiter] {len(files)} files ready for review")
        return files

    except Exception as e:
        print(f"[token_limiter] error: {e}")
        return []