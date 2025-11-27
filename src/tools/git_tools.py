"""
Git operation tools for the multi-agent system

Provides tools for:
- Repository initialization
- Commit creation
- Log parsing
- Branch management

Compatible with LangChain 1.0 create_agent pattern
"""

from langchain_core.tools import tool
import subprocess
import os
from typing import Optional


@tool
def create_git_repo(path: str) -> str:
    """
    Initialize a new git repository

    Args:
        path: Directory path for the repository

    Returns:
        Success message or error

    Example:
        >>> create_git_repo("/path/to/project")
        "Git repository initialized at /path/to/project"
    """
    try:
        os.makedirs(path, exist_ok=True)
        result = subprocess.run(
            ["git", "init"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        return f"Git repository initialized at {path}"
    except subprocess.CalledProcessError as e:
        return f"Error initializing git repository: {e.stderr}"
    except Exception as e:
        return f"Error: {e}"


@tool
def create_git_commit(
    repo_path: str,
    message: str,
    add_all: bool = True
) -> str:
    """
    Create a git commit

    Args:
        repo_path: Path to repository
        message: Commit message
        add_all: Whether to add all changes first (default: True)

    Returns:
        Commit SHA or error message

    Example:
        >>> create_git_commit("/path/to/repo", "feat: Add login feature")
        "Commit created: abc123def"
    """
    try:
        # Add files if requested
        if add_all:
            subprocess.run(
                ["git", "add", "."],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )

        # Create commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        # Get commit SHA
        sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        commit_sha = sha_result.stdout.strip()[:7]
        return f"Commit created: {commit_sha}"

    except subprocess.CalledProcessError as e:
        return f"Error creating commit: {e.stderr}"
    except Exception as e:
        return f"Error: {e}"


@tool
def get_git_log(
    repo_path: str,
    max_count: int = 10
) -> str:
    """
    Get git commit history

    Args:
        repo_path: Path to repository
        max_count: Maximum number of commits to retrieve

    Returns:
        Git log output (formatted)

    Example:
        >>> get_git_log("/path/to/repo", max_count=5)
        "abc123 - feat: Add login (2025-11-27)\\n..."
    """
    try:
        result = subprocess.run(
            [
                "git", "log",
                f"--max-count={max_count}",
                "--pretty=format:%h - %s (%ad)",
                "--date=short"
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error getting git log: {e.stderr}"
    except Exception as e:
        return f"Error: {e}"


@tool
def get_git_status(repo_path: str) -> str:
    """
    Get git repository status

    Args:
        repo_path: Path to repository

    Returns:
        Git status output

    Example:
        >>> get_git_status("/path/to/repo")
        "On branch main\\nnothing to commit, working tree clean"
    """
    try:
        result = subprocess.run(
            ["git", "status"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error getting git status: {e.stderr}"
    except Exception as e:
        return f"Error: {e}"


@tool
def get_git_diff(repo_path: str, cached: bool = False) -> str:
    """
    Get git diff (changes)

    Args:
        repo_path: Path to repository
        cached: Show staged changes instead of unstaged (default: False)

    Returns:
        Git diff output

    Example:
        >>> get_git_diff("/path/to/repo")
        "diff --git a/file.py b/file.py\\n..."
    """
    try:
        cmd = ["git", "diff"]
        if cached:
            cmd.append("--cached")

        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error getting git diff: {e.stderr}"
    except Exception as e:
        return f"Error: {e}"


@tool
def get_last_commit_sha(repo_path: str) -> str:
    """
    Get SHA of the last commit

    Args:
        repo_path: Path to repository

    Returns:
        Short commit SHA (7 chars) or error

    Example:
        >>> get_last_commit_sha("/path/to/repo")
        "abc123d"
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()[:7]
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"
    except Exception as e:
        return f"Error: {e}"


__all__ = [
    "create_git_repo",
    "create_git_commit",
    "get_git_log",
    "get_git_status",
    "get_git_diff",
    "get_last_commit_sha",
]
