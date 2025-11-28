"""
GitHub tools for repository creation and management

Provides tools for:
- Creating GitHub repositories
- Pushing code to GitHub
- Managing repository settings

Compatible with LangChain 1.0 create_agent pattern
"""

from langchain_core.tools import tool
from langchain.tools import InjectedState
from typing_extensions import Annotated
import os
import subprocess
import requests
from typing import Optional


@tool
def create_github_repo(
    repo_name: str,
    description: str,
    state: Annotated[dict, InjectedState],
    private: bool = False
) -> str:
    """
    Create a new GitHub repository using GitHub API

    Args:
        repo_name: Repository name (e.g., "api-test")
        description: Repository description
        runtime: Tool runtime for state access
        private: Whether to make repo private (default: False)

    Returns:
        Success message with repo URL

    Example:
        >>> create_github_repo("my-api", "FastAPI application")
        "Created repo: https://github.com/username/my-api"
    """
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        return "⚠️  GITHUB_TOKEN not set - skipping GitHub repo creation"

    try:
        # Create repo via GitHub API
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        data = {
            "name": repo_name,
            "description": description,
            "private": private,
            "auto_init": False  # Don't create README, we'll push our own
        }

        response = requests.post(
            "https://api.github.com/user/repos",
            headers=headers,
            json=data
        )

        if response.status_code == 201:
            repo_data = response.json()
            clone_url = repo_data["clone_url"]
            html_url = repo_data["html_url"]

            # Save repo URL to state for later use
            state["github_repo_url"] = html_url

            print(f"\n{'='*60}")
            print(f"🎉 GITHUB REPO CREATED")
            print(f"   Repository: {html_url}")
            print(f"   Private: {private}")
            print(f"{'='*60}\n")

            return f"✅ Created GitHub repo: {html_url}"
        elif response.status_code == 422:
            # Repo already exists
            return f"⚠️  Repository '{repo_name}' already exists on GitHub"
        else:
            return f"❌ Failed to create repo: {response.status_code} - {response.text}"

    except Exception as e:
        return f"❌ Error creating GitHub repo: {e}"


@tool
def push_to_github(
    repo_name: str,
    state: Annotated[dict, InjectedState],
    branch: str = "main"
) -> str:
    """
    Push local git repository to GitHub

    Args:
        repo_name: Repository name
        runtime: Tool runtime for state access
        branch: Branch to push (default: main)

    Returns:
        Success message

    Example:
        >>> push_to_github("api-test")
        "Pushed to GitHub: https://github.com/username/api-test"
    """
    repo_path = state.get("repo_path", "")
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        return "⚠️  GITHUB_TOKEN not set - skipping GitHub push"

    try:
        # Get GitHub username
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        user_response = requests.get("https://api.github.com/user", headers=headers)

        if user_response.status_code != 200:
            return f"❌ Failed to get GitHub user info: {user_response.status_code}"

        username = user_response.json()["login"]
        remote_url = f"https://{github_token}@github.com/{username}/{repo_name}.git"

        # Check if remote already exists
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            # Add remote
            subprocess.run(
                ["git", "remote", "add", "origin", remote_url],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
        else:
            # Update remote URL
            subprocess.run(
                ["git", "remote", "set-url", "origin", remote_url],
                cwd=repo_path,
                check=True,
                capture_output=True
            )

        # Rename branch to main if needed
        subprocess.run(
            ["git", "branch", "-M", branch],
            cwd=repo_path,
            capture_output=True
        )

        # Push to GitHub
        push_result = subprocess.run(
            ["git", "push", "-u", "origin", branch],
            cwd=repo_path,
            capture_output=True,
            text=True
        )

        if push_result.returncode == 0:
            repo_url = f"https://github.com/{username}/{repo_name}"

            print(f"\n{'='*60}")
            print(f"🚀 PUSHED TO GITHUB")
            print(f"   Repository: {repo_url}")
            print(f"   Branch: {branch}")
            print(f"{'='*60}\n")

            return f"✅ Pushed to GitHub: {repo_url}"
        else:
            return f"❌ Push failed: {push_result.stderr}"

    except subprocess.CalledProcessError as e:
        return f"❌ Git command failed: {e.stderr}"
    except Exception as e:
        return f"❌ Error pushing to GitHub: {e}"


@tool
def add_github_remote(
    repo_name: str,
    state: Annotated[dict, InjectedState],
    username: Optional[str] = None
) -> str:
    """
    Add GitHub remote to local repository

    Args:
        repo_name: Repository name
        runtime: Tool runtime for state access
        username: GitHub username (fetched from API if not provided)

    Returns:
        Success message

    Example:
        >>> add_github_remote("api-test")
        "Added remote: origin -> https://github.com/username/api-test.git"
    """
    repo_path = state.get("repo_path", "")
    github_token = os.getenv("GITHUB_TOKEN")

    if not github_token:
        return "⚠️  GITHUB_TOKEN not set - skipping remote setup"

    try:
        # Get username if not provided
        if not username:
            headers = {
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get("https://api.github.com/user", headers=headers)

            if response.status_code == 200:
                username = response.json()["login"]
            else:
                return f"❌ Failed to get GitHub username: {response.status_code}"

        remote_url = f"https://{github_token}@github.com/{username}/{repo_name}.git"

        # Add remote
        result = subprocess.run(
            ["git", "remote", "add", "origin", remote_url],
            cwd=repo_path,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return f"✅ Added remote: origin -> https://github.com/{username}/{repo_name}.git"
        else:
            # Remote might already exist
            if "already exists" in result.stderr:
                return f"⚠️  Remote 'origin' already exists"
            return f"❌ Failed to add remote: {result.stderr}"

    except Exception as e:
        return f"❌ Error adding remote: {e}"


__all__ = [
    "create_github_repo",
    "push_to_github",
    "add_github_remote",
]
