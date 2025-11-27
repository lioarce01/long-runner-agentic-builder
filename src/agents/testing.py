"""
Test Agent - Validates features with adaptive testing

This agent runs E2E tests for web apps, API tests for backends,
unit tests for CLIs, and validates acceptance criteria.

Compatible with:
- LangChain 1.1.0 (create_agent pattern)
- LangGraph 1.0.4
"""

from langchain.agents import create_agent
from langchain_core.tools import tool
from src.utils.model import get_test_model
from src.tools.test_tools import (
    run_playwright_tests,
    run_pytest_tests,
    validate_acceptance_criteria
)
from src.tools.feature_tools import update_feature_status
import os
import json
from datetime import datetime


@tool
def save_test_results(
    repo_path: str,
    feature_id: str,
    test_results: dict
) -> str:
    """
    Save test results to file for debugging

    Args:
        repo_path: Path to repository
        feature_id: Feature ID
        test_results: Test results dictionary

    Returns:
        Path to saved results file
    """
    results_dir = os.path.join(repo_path, "test-results")
    os.makedirs(results_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(results_dir, f"{feature_id}_{timestamp}.json")

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2)

    return results_file


@tool
def capture_test_screenshot(
    repo_path: str,
    feature_id: str,
    screenshot_name: str = "test_screenshot"
) -> str:
    """
    Placeholder for screenshot capture during Playwright tests

    Args:
        repo_path: Path to repository
        feature_id: Feature ID
        screenshot_name: Name for the screenshot

    Returns:
        Path to screenshot (or message if not applicable)

    Note: In production, this would integrate with Playwright's
    screenshot API during test execution.
    """
    screenshots_dir = os.path.join(repo_path, "test-results", "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(
        screenshots_dir,
        f"{feature_id}_{screenshot_name}_{timestamp}.png"
    )

    return f"Screenshot would be saved to: {screenshot_path}"


@tool
def determine_test_strategy(project_metadata: dict, feature: dict) -> dict:
    """
    Determine appropriate testing strategy based on project type

    Args:
        project_metadata: Project metadata dictionary
        feature: Feature dictionary

    Returns:
        Test strategy dictionary

    Example:
        >>> determine_test_strategy(
        ...     {"type": "web_app"},
        ...     {"id": "f-001", "title": "Login page"}
        ... )
        {"strategy": "e2e", "tools": ["playwright"], ...}
    """
    project_type = project_metadata.get("type", "web_app")
    feature_tech = feature.get("tech_stack", {})

    strategy = {
        "project_type": project_type,
        "feature_id": feature.get("id"),
        "recommended_tests": []
    }

    # Determine testing approach based on project type
    if project_type == "web_app":
        if feature_tech.get("frontend"):
            strategy["recommended_tests"].append({
                "type": "e2e",
                "tool": "playwright",
                "description": "Browser automation for UI testing"
            })
        if feature_tech.get("backend"):
            strategy["recommended_tests"].append({
                "type": "api",
                "tool": "pytest+requests",
                "description": "API endpoint testing"
            })

    elif project_type == "rest_api":
        strategy["recommended_tests"].append({
            "type": "api",
            "tool": "pytest+requests",
            "description": "API endpoint testing with requests library"
        })

    elif project_type == "cli_tool":
        strategy["recommended_tests"].append({
            "type": "unit",
            "tool": "pytest",
            "description": "Command-line interface testing"
        })

    else:
        # Default to unit tests
        strategy["recommended_tests"].append({
            "type": "unit",
            "tool": "pytest",
            "description": "Unit testing"
        })

    return strategy


# Create Test Agent with LangChain 1.0 pattern
def create_test_agent():
    """
    Create the Test Agent using LangChain 1.0's create_agent

    Returns:
        Compiled agent
    """
    # Load system prompt
    prompt_path = "config/prompts/testing.txt"
    with open(prompt_path, "r") as f:
        system_prompt = f.read()

    # Get model
    model = get_test_model()

    # Define tools
    tools = [
        # Testing tools
        run_playwright_tests,
        run_pytest_tests,
        validate_acceptance_criteria,
        # Test strategy
        determine_test_strategy,
        # Results management
        save_test_results,
        capture_test_screenshot,
        # Feature status
        update_feature_status,
    ]

    # Create agent using LangChain 1.0 pattern
    agent = create_agent(
        model,
        tools=tools,
        system_prompt=system_prompt
    )

    return agent


__all__ = ["create_test_agent"]
