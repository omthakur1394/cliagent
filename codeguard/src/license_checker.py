import requests
import os

OPEN_SOURCE_LICENSES = [
    "mit", "apache-2.0", "gpl-2.0", "gpl-3.0",
    "bsd-2-clause", "bsd-3-clause", "lgpl-2.1",
    "mpl-2.0", "isc", "unlicense", "cc0-1.0",
    "other", "noassertion"
]

def is_open_source(repo_url: str) -> tuple[bool, str]:
    try:
        # extract owner/repo from url
        parts = repo_url.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]
        
        # strip .git if present
        if repo.endswith(".git"):
            repo = repo[:-4]

        headers = {"Accept": "application/vnd.github+json"}
        github_token = os.environ.get("GITHUB_TOKEN", "")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        # Hit the license endpoint specifically
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/license",
            headers=headers
        )

        if response.status_code == 404:
            # no license file found = allowed to review
            return False, "none"

        data = response.json()
        
        license_key = data.get("license", {}).get("key", "").lower()
        license_spdx = data.get("license", {}).get("spdx_id", "").lower()

        if license_key in OPEN_SOURCE_LICENSES or license_spdx in OPEN_SOURCE_LICENSES:
            return True, license_spdx if license_spdx else license_key

        return False, license_key

    except Exception as e:
        print(f"[license_checker] error: {e}")
        return False, "unknown"