"""
Code quality tools for the multi-agent system

Provides tools for:
- Linting (ruff)
- Type checking (mypy)
- Code quality reports

Compatible with LangChain 1.0 create_agent pattern
"""

from langchain_core.tools import tool
import subprocess
from typing import Optional


@tool
def run_ruff_check(
    repo_path: str,
    file_paths: Optional[list[str]] = None
) -> dict:
    """
    Run ruff linter on Python code

    Args:
        repo_path: Path to repository
        file_paths: Optional list of specific files to check

    Returns:
        Lint results dictionary

    Example:
        >>> run_ruff_check("/path/to/repo")
        {"passed": True, "issues_found": 0, "output": "..."}
    """
    try:
        cmd = ["ruff", "check"]
        if file_paths:
            cmd.extend(file_paths)
        else:
            cmd.append(".")

        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"  # Replace invalid chars instead of crashing
        )

        return {
            "passed": result.returncode == 0,
            "issues_found": result.stdout.count("\n") if result.stdout else 0,
            "output": result.stdout,
            "errors": result.stderr
        }

    except FileNotFoundError:
        return {
            "passed": False,
            "issues_found": 0,
            "output": "",
            "errors": "ruff not found - please install: pip install ruff"
        }
    except Exception as e:
        return {
            "passed": False,
            "issues_found": 0,
            "output": "",
            "errors": f"Error running ruff: {e}"
        }


@tool
def run_mypy_check(
    repo_path: str,
    file_paths: Optional[list[str]] = None
) -> dict:
    """
    Run mypy type checker on Python code

    Args:
        repo_path: Path to repository
        file_paths: Optional list of specific files to check

    Returns:
        Type check results dictionary

    Example:
        >>> run_mypy_check("/path/to/repo")
        {"passed": True, "issues_found": 0, "output": "..."}
    """
    try:
        cmd = ["mypy"]
        if file_paths:
            cmd.extend(file_paths)
        else:
            cmd.append(".")

        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"  # Replace invalid chars instead of crashing
        )

        return {
            "passed": result.returncode == 0,
            "issues_found": result.stdout.count("error:"),
            "output": result.stdout,
            "errors": result.stderr
        }

    except FileNotFoundError:
        return {
            "passed": False,
            "issues_found": 0,
            "output": "",
            "errors": "mypy not found - please install: pip install mypy"
        }
    except Exception as e:
        return {
            "passed": False,
            "issues_found": 0,
            "output": "",
            "errors": f"Error running mypy: {e}"
        }


@tool
def run_all_quality_checks(
    repo_path: str,
    changed_files: Optional[list[str]] = None
) -> dict:
    """
    Run all code quality checks (ruff + mypy)

    Args:
        repo_path: Path to repository
        changed_files: Optional list of changed files to check

    Returns:
        Combined quality check results

    Example:
        >>> run_all_quality_checks("/path/to/repo")
        {"passed": True, "ruff": {...}, "mypy": {...}}
    """
    ruff_results = run_ruff_check.invoke({"repo_path": repo_path, "file_paths": changed_files})
    mypy_results = run_mypy_check.invoke({"repo_path": repo_path, "file_paths": changed_files})

    return {
        "passed": ruff_results["passed"] and mypy_results["passed"],
        "ruff": ruff_results,
        "mypy": mypy_results,
        "summary": {
            "total_issues": ruff_results["issues_found"] + mypy_results["issues_found"],
            "ruff_issues": ruff_results["issues_found"],
            "mypy_issues": mypy_results["issues_found"]
        }
    }


__all__ = [
    "run_ruff_check",
    "run_mypy_check",
    "run_all_quality_checks",
]
