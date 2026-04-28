import os
import subprocess
import shutil
import requests

def verify_repo_owner(repo_url: str) -> bool:
    """Check if the GitHub token belongs to the actual repo owner."""
    try:
        github_token = os.environ.get("GITHUB_TOKEN", "")
        if not github_token:
            return False

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}"
        }

        # who does this token belong to?
        user_response = requests.get(
            "https://api.github.com/user",
            headers=headers
        )
        token_owner = user_response.json().get("login", "").lower()

        # get repo owner from URL
        parts = repo_url.rstrip("/").split("/")
        repo_owner = parts[-2].lower()

        print(f"[git_manager] Token owner : {token_owner}")
        print(f"[git_manager] Repo owner  : {repo_owner}")

        return token_owner == repo_owner

    except Exception as e:
        print(f"[git_manager] Ownership check failed: {e}")
        return False

def get_clone_url(repo_url: str) -> str:
    github_token = os.environ.get("GITHUB_TOKEN", "")
    if github_token and "://" in repo_url:
        protocol, rest = repo_url.split("://", 1)
        return f"{protocol}://{github_token}@{rest}"
    return repo_url

def clone_repo(repo_url: str) -> str:
    """Clones a repository into a local workspaces folder."""
    parts = repo_url.rstrip("/").split("/")
    repo_name = parts[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    workspaces_dir = os.path.join(os.getcwd(), "workspaces")
    os.makedirs(workspaces_dir, exist_ok=True)

    repo_path = os.path.join(workspaces_dir, repo_name)

    if os.path.exists(repo_path):
        import stat
        def remove_readonly(func, path, excinfo):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(repo_path, onerror=remove_readonly)

    clone_url = get_clone_url(repo_url)

    print(f"\n[git_manager] Cloning repository '{repo_name}'...")
    try:
        subprocess.run(
            ["git", "clone", clone_url, repo_path],
            check=True, capture_output=True, text=True
        )
        print("[git_manager] Clone successful.")
        return repo_path
    except subprocess.CalledProcessError as e:
        print(f"[git_manager] Failed to clone: {e.stderr}")
        return ""

def get_local_files(repo_path: str) -> list:
    """Returns a list of absolute file paths in the local repo."""
    excluded_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', 'env'}
    excluded_exts = {
        '.min.js', '.lock', '.csv', '.png', '.svg',
        '.jpg', '.jpeg', '.gif', '.ico', '.pdf',
        '.zip', '.exe', '.ipynb', '.class', '.jar',
        '.pyc', '.o', '.war'
    }

    file_list = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for f in files:
            if not any(f.endswith(ext) for ext in excluded_exts):
                file_list.append(os.path.join(root, f))

    return file_list

def commit_changes(repo_path: str, repo_url: str, message: str = "Auto-fixed code issues via CodeGuard"):
    """Verifies ownership then commits and pushes changes."""
    try:
        # check if anything changed
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path, capture_output=True, text=True
        )
        if not status.stdout.strip():
            print("\n[git_manager] No changes were made to the code.")
            return

        # verify ownership before allowing push
        print("\n[git_manager] Verifying repo ownership...")
        if not verify_repo_owner(repo_url):
            print("\n❌ Permission denied.")
            print("Only the repository owner can commit and push changes.")
            return

        print(f"\n[git_manager] ✅ Ownership verified. Changes are ready in '{repo_path}'.")
        user_input = input("❓ Do you want to commit AND push these changes? (y/N): ").strip().lower()

        if user_input in ['y', 'yes']:
            print("[git_manager] Committing changes...")
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=repo_path, check=True, capture_output=True, text=True
            )

            print("[git_manager] Pushing to GitHub...")
            result = subprocess.run(
                ["git", "push"],
                cwd=repo_path, capture_output=True, text=True
            )

            if result.returncode == 0:
                print("[git_manager] ✅ Changes pushed to GitHub successfully!")
            else:
                print(f"[git_manager] ❌ Push failed: {result.stderr}")
                print("[git_manager] 💡 Make sure your GitHub token has 'repo' write access.")
        else:
            print("[git_manager] Commit skipped. Files remain in workspace.")

    except subprocess.CalledProcessError as e:
        print(f"[git_manager] Failed: {e.stderr}")

def cleanup_workspace(repo_path: str):
    """Delete cloned repo after review is done."""
    try:
        import stat
        def remove_readonly(func, path, excinfo):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, onerror=remove_readonly)
            print("[git_manager] ✅ Workspace cleaned up.")
    except Exception as e:
        print(f"[git_manager] Cleanup failed: {e}")