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
from src.utils.paths import get_prompt_path
from src.state.schemas import AppBuilderState
from src.mcp_config.client import get_mcp_tools
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
async def create_test_agent():
    """
    Create the Test Agent using LangChain 1.0's create_agent

    Returns:
        Compiled agent
    """
    # Load system prompt
    prompt_path = get_prompt_path("testing.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    # Get model
    model = get_test_model()

    # Load MCP tools
    mcp_tools = await get_mcp_tools()

    # Define custom tools
    # run_pytest_tests now auto-saves real results to test-results/
    custom_tools = [
        # Testing tools (auto-save results)
        run_playwright_tests,
        run_pytest_tests,
        validate_acceptance_criteria,
        # Test strategy
        determine_test_strategy,
        # Feature status
        update_feature_status,
    ]

    # Combine all tools
    # CRITICAL: NO MCP tools for Testing Agent to prevent result fabrication
    # The LLM was using MCP filesystem tools to create fake test-results JSON files
    # Now it can ONLY call run_pytest_tests which executes real pytest
    tools = custom_tools  # NO mcp_tools
    print(f"[OK] Testing agent: {len(custom_tools)} custom tools (NO MCP - prevents result fabrication)")

    # Create agent using LangChain 1.0 pattern with custom state schema
    # NOTE: create_agent() handles tool binding internally, no need for bind_tools()
    agent = create_agent(
        model,
        tools=tools,
        system_prompt=system_prompt,
        state_schema=AppBuilderState
    )

    return agent


__all__ = ["create_test_agent"]
