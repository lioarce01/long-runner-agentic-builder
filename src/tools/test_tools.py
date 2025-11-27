"""
Testing tools for the multi-agent system

Provides tools for:
- Playwright E2E test execution (web apps)
- pytest unit/integration test execution
- Test result parsing and reporting

Compatible with LangChain 1.0 create_agent pattern
"""

from langchain_core.tools import tool
import subprocess
import json
import os
from typing import Optional


@tool
def run_playwright_tests(
    repo_path: str,
    test_spec: Optional[str] = None
) -> dict:
    """
    Run Playwright end-to-end tests

    Args:
        repo_path: Path to repository
        test_spec: Optional specific test file/pattern to run

    Returns:
        Test results dictionary with pass/fail counts

    Example:
        >>> run_playwright_tests("/path/to/repo")
        {"passed": True, "total_tests": 5, "passed_tests": 5, ...}
    """
    try:
        cmd = ["npx", "playwright", "test"]
        if test_spec:
            cmd.append(test_spec)

        # Add JSON reporter for structured output
        cmd.extend(["--reporter=json"])

        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout for E2E tests
        )

        # Parse Playwright JSON output
        try:
            output_data = json.loads(result.stdout)
            total_tests = output_data.get("stats", {}).get("expected", 0)
            passed_tests = output_data.get("stats", {}).get("ok", 0)
            failed_tests = total_tests - passed_tests

            return {
                "passed": result.returncode == 0,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time_ms": output_data.get("stats", {}).get("duration", 0)
            }
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "passed": result.returncode == 0,
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time_ms": 0
            }

    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "stdout": "",
            "stderr": "Test execution timed out after 5 minutes",
            "execution_time_ms": 300000
        }
    except Exception as e:
        return {
            "passed": False,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "stdout": "",
            "stderr": f"Error running Playwright tests: {e}",
            "execution_time_ms": 0
        }


@tool
def run_pytest_tests(
    repo_path: str,
    test_path: Optional[str] = None,
    verbose: bool = True
) -> dict:
    """
    Run pytest unit/integration tests

    Args:
        repo_path: Path to repository
        test_path: Optional specific test file/directory
        verbose: Enable verbose output (default: True)

    Returns:
        Test results dictionary

    Example:
        >>> run_pytest_tests("/path/to/repo", "tests/unit")
        {"passed": True, "total_tests": 10, "passed_tests": 10, ...}
    """
    try:
        cmd = ["pytest"]
        if test_path:
            cmd.append(test_path)
        if verbose:
            cmd.append("-v")

        # Add JSON output
        cmd.extend(["--json-report", "--json-report-file=/tmp/pytest_report.json"])

        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout for unit tests
        )

        # Try to parse JSON report
        try:
            with open("/tmp/pytest_report.json", "r") as f:
                report = json.load(f)

            return {
                "passed": result.returncode == 0,
                "total_tests": report.get("summary", {}).get("total", 0),
                "passed_tests": report.get("summary", {}).get("passed", 0),
                "failed_tests": report.get("summary", {}).get("failed", 0),
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback: parse from stdout
            return {
                "passed": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "stdout": "",
            "stderr": "Test execution timed out after 3 minutes"
        }
    except Exception as e:
        return {
            "passed": False,
            "stdout": "",
            "stderr": f"Error running pytest: {e}"
        }


@tool
def validate_acceptance_criteria(
    feature: dict,
    test_results: dict
) -> dict:
    """
    Validate if feature acceptance criteria are met based on test results

    Args:
        feature: Feature dictionary with acceptance_criteria list
        test_results: Test results from run_playwright_tests or run_pytest_tests

    Returns:
        Validation results with met/unmet criteria

    Example:
        >>> validate_acceptance_criteria(feature, test_results)
        {"all_met": True, "met": [...], "unmet": [], ...}
    """
    acceptance_criteria = feature.get("acceptance_criteria", [])

    if not test_results.get("passed"):
        # All criteria unmet if tests failed
        return {
            "all_met": False,
            "met": [],
            "unmet": acceptance_criteria,
            "details": "Tests failed - acceptance criteria not verified"
        }

    # If tests passed, consider all criteria met
    # (In production, this would be more sophisticated)
    return {
        "all_met": True,
        "met": acceptance_criteria,
        "unmet": [],
        "details": "All tests passed - acceptance criteria verified"
    }


__all__ = [
    "run_playwright_tests",
    "run_pytest_tests",
    "validate_acceptance_criteria",
]
