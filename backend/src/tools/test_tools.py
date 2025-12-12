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


def _parse_pytest_output(stdout: str, returncode: int) -> dict:
    """
    Parse pytest verbose output to extract test counts
    
    Parses lines like:
    - "5 passed" or "5 passed, 2 failed"
    - "PASSED" / "FAILED" markers in verbose output
    """
    import re
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    # Try to find summary line like "5 passed, 2 failed, 1 error"
    summary_pattern = r'(\d+)\s+(passed|failed|error|skipped|warning)'
    matches = re.findall(summary_pattern, stdout, re.IGNORECASE)
    
    for count, status in matches:
        count = int(count)
        status = status.lower()
        if status == 'passed':
            passed_tests = count
        elif status == 'failed':
            failed_tests = count
        total_tests += count if status in ['passed', 'failed'] else 0
    
    # If no summary found, count PASSED/FAILED lines in verbose output
    if total_tests == 0:
        passed_tests = len(re.findall(r'\bPASSED\b', stdout))
        failed_tests = len(re.findall(r'\bFAILED\b', stdout))
        total_tests = passed_tests + failed_tests
    
    return {
        "passed": returncode == 0 and failed_tests == 0,
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests
    }


def _save_test_results(repo_path: str, feature_id: str, results: dict) -> str:
    """
    Auto-save test results to test-results/ directory
    This is NOT a tool - it's called automatically by run_pytest_tests
    """
    from datetime import datetime
    
    results_dir = os.path.join(repo_path, "test-results")
    os.makedirs(results_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(results_dir, f"{feature_id}_{timestamp}.json")
    
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[AUTO-SAVED] Test results: {results_file}")
    return results_file


@tool
def run_pytest_tests(
    repo_path: str,
    feature_id: str,
    test_path: Optional[str] = None,
    verbose: bool = True
) -> dict:
    """
    Run pytest unit/integration tests and AUTO-SAVE results

    Args:
        repo_path: Path to repository
        feature_id: Feature ID being tested (e.g., "f-001") - REQUIRED for result tracking
        test_path: Optional specific test file/directory
        verbose: Enable verbose output (default: True)

    Returns:
        Test results dictionary with pass/fail counts
        Results are automatically saved to test-results/{feature_id}_{timestamp}.json

    Example:
        >>> run_pytest_tests("/path/to/repo", "f-001", "tests/")
        {"passed": True, "total_tests": 10, "passed_tests": 10, ...}
    """
    import platform
    
    print(f"\n{'='*50}")
    print(f"RUNNING PYTEST for {feature_id}")
    print(f"  repo: {repo_path}")
    print(f"  test_path: {test_path or 'tests/'}")
    print(f"{'='*50}")
    
    try:
        # Use the project's venv python to run pytest
        # This ensures tests run with project dependencies, not multi-agent dependencies
        is_windows = platform.system() == "Windows"
        venv_path = os.path.join(repo_path, ".venv")
        
        if is_windows:
            python_path = os.path.join(venv_path, "Scripts", "python.exe")
        else:
            python_path = os.path.join(venv_path, "bin", "python")
        
        # Check if project venv exists
        if os.path.exists(python_path):
            # Use project's python to run pytest as module
            cmd = [python_path, "-m", "pytest"]
            print(f"  Using project venv: {python_path}")
        else:
            # Fallback to system pytest (for backwards compatibility)
            cmd = ["pytest"]
            print(f"  ⚠️  Project venv not found, using system pytest")
        
        if test_path:
            cmd.append(test_path)
        if verbose:
            cmd.append("-v")
        
        # Add extra flags for better output parsing
        cmd.append("--tb=short")  # Short traceback for errors
        
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=180  # 3 minute timeout for unit tests
        )

        # Parse pytest output to get test counts
        parsed = _parse_pytest_output(result.stdout, result.returncode)
        
        test_results = {
            "passed": parsed["passed"],
            "total_tests": parsed["total_tests"],
            "passed_tests": parsed["passed_tests"],
            "failed_tests": parsed["failed_tests"],
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
        # AUTO-SAVE results (cannot be faked by LLM)
        _save_test_results(repo_path, feature_id, test_results)
        
        print(f"  Result: {'PASSED' if parsed['passed'] else 'FAILED'}")
        print(f"  Tests: {parsed['passed_tests']}/{parsed['total_tests']} passed")
        print(f"{'='*50}\n")
        
        return test_results

    except subprocess.TimeoutExpired:
        test_results = {
            "passed": False,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "stdout": "",
            "stderr": "Test execution timed out after 3 minutes"
        }
        _save_test_results(repo_path, feature_id, test_results)
        return test_results
        
    except Exception as e:
        test_results = {
            "passed": False,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "stdout": "",
            "stderr": f"Error running pytest: {e}"
        }
        _save_test_results(repo_path, feature_id, test_results)
        return test_results


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
