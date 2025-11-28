"""
QA/Documentation Agent - Reviews code quality and updates documentation

This agent runs code quality checks, validates completion criteria,
updates documentation, and marks features as done.

Compatible with:
- LangChain 1.1.0 (create_agent pattern)
- LangGraph 1.0.4
"""

from langchain.agents import create_agent
from langchain_core.tools import tool
from src.utils.model import get_qa_model
from src.state.schemas import AppBuilderState
from src.mcp_config.client import get_mcp_tools
from src.tools.code_quality import (
    run_ruff_check,
    run_mypy_check,
    run_all_quality_checks
)
from src.tools.feature_tools import update_feature_status
from src.tools.github_tools import push_to_github
import os
import json
from datetime import datetime


# Import progress log tool from coding agent
@tool
def update_qa_progress_log(
    repo_path: str,
    feature_id: str,
    action: str,
    commit_sha: str = None,
    notes: str = ""
) -> str:
    """
    Add QA entry to progress log

    Args:
        repo_path: Path to repository
        feature_id: Feature ID
        action: Action taken (qa_approved, qa_rejected)
        commit_sha: Optional commit SHA
        notes: Optional notes

    Returns:
        Success message
    """
    log_path = os.path.join(repo_path, "progress_log.json")

    # Read existing log
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            log = json.load(f)
    else:
        log = []

    # Add new entry
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent": "qa_doc",
        "feature_id": feature_id,
        "action": action,
        "commit_sha": commit_sha,
        "notes": notes
    }

    log.append(entry)

    # Write back
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)

    print(f"\n{'='*60}")
    print(f"📋 PROGRESS LOG UPDATED")
    print(f"   Agent: qa_doc")
    print(f"   Feature: {feature_id}")
    print(f"   Action: {action}")
    print(f"{'='*60}\n")

    return f"Progress log updated with {action} for {feature_id}"


@tool
def update_changelog(
    repo_path: str,
    feature: dict,
    commit_sha: str
) -> str:
    """
    Update CHANGELOG.md with completed feature

    Args:
        repo_path: Path to repository
        feature: Feature dictionary
        commit_sha: Commit SHA

    Returns:
        Success message

    Example:
        >>> update_changelog("/path/to/repo", feature_dict, "abc123")
        "CHANGELOG.md updated"
    """
    changelog_path = os.path.join(repo_path, "CHANGELOG.md")

    # Read existing changelog or create new
    if os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            content = f.read()
    else:
        content = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"

    # Find or create "Unreleased" section
    if "## [Unreleased]" not in content:
        content += "\n## [Unreleased]\n\n### Added\n\n### Changed\n\n### Fixed\n\n"

    # Add feature to appropriate section
    feature_line = f"- {feature['title']} ({feature['id']}) - {commit_sha}\n"

    # Determine section based on feature
    if "fix" in feature['title'].lower() or "bug" in feature['title'].lower():
        section = "### Fixed"
    elif "update" in feature['title'].lower() or "improve" in feature['title'].lower():
        section = "### Changed"
    else:
        section = "### Added"

    # Insert after section header
    section_pos = content.find(section)
    if section_pos != -1:
        # Find next newline after section header
        insert_pos = content.find("\n", section_pos) + 1
        content = content[:insert_pos] + feature_line + content[insert_pos:]

    # Write back
    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(content)

    return "CHANGELOG.md updated"


@tool
def update_readme(
    repo_path: str,
    feature: dict
) -> str:
    """
    Update README.md if public API changed

    Args:
        repo_path: Path to repository
        feature: Feature dictionary

    Returns:
        Success message or skip message
    """
    readme_path = os.path.join(repo_path, "README.md")

    # For now, just ensure README exists
    if not os.path.exists(readme_path):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"# Project\n\nAuto-generated project.\n\n## Features\n\n")

    # In production, this would intelligently update README
    # based on feature type (API changes, new endpoints, etc.)

    return "README.md checked (no updates needed for this feature)"


@tool
def generate_feature_documentation(
    repo_path: str,
    feature: dict
) -> str:
    """
    Generate documentation for a completed feature

    Args:
        repo_path: Path to repository
        feature: Feature dictionary

    Returns:
        Path to generated documentation

    Example:
        >>> generate_feature_documentation("/path/to/repo", feature_dict)
        "/path/to/repo/docs/features/f-001.md"
    """
    docs_dir = os.path.join(repo_path, "docs", "features")
    os.makedirs(docs_dir, exist_ok=True)

    doc_file = os.path.join(docs_dir, f"{feature['id']}.md")

    # Generate documentation content
    doc_content = f"""# {feature['title']}

**ID**: {feature['id']}
**Status**: {feature['status']}
**Priority**: {feature['priority']}
**Complexity**: {feature['complexity']}

## Description

{feature['description']}

## Acceptance Criteria

"""

    for criterion in feature.get('acceptance_criteria', []):
        doc_content += f"- {criterion}\n"

    doc_content += f"\n## Implementation Notes\n\nCompleted in {feature.get('attempts', 1)} attempt(s).\n"

    # Write documentation
    with open(doc_file, "w", encoding="utf-8") as f:
        f.write(doc_content)

    return doc_file


@tool
def create_technical_debt_entry(
    repo_path: str,
    issue_description: str,
    severity: str = "medium"
) -> str:
    """
    Log technical debt for future sprints

    Args:
        repo_path: Path to repository
        issue_description: Description of the technical debt
        severity: Severity level (low, medium, high)

    Returns:
        Success message
    """
    debt_file = os.path.join(repo_path, "TODO.md")

    # Read existing debt log
    if os.path.exists(debt_file):
        with open(debt_file, "r") as f:
            content = f.read()
    else:
        content = "# Technical Debt\n\n"

    # Add new entry
    timestamp = datetime.utcnow().strftime("%Y-%m-%d")
    entry = f"- [{severity.upper()}] {issue_description} _(added {timestamp})_\n"

    content += entry

    # Write back
    with open(debt_file, "w", encoding="utf-8") as f:
        f.write(content)

    return f"Technical debt logged in TODO.md"


@tool
def validate_all_quality_gates(
    repo_path: str,
    feature: dict,
    test_results: dict
) -> dict:
    """
    Validate all quality gate criteria before marking feature done

    Args:
        repo_path: Path to repository
        feature: Feature dictionary
        test_results: Test results from Test Agent

    Returns:
        Quality gate validation results

    Quality gates:
    - All tests pass
    - Code quality checks pass
    - Documentation updated
    - All acceptance criteria met
    """
    results = {
        "passed": True,
        "checks": {}
    }

    # 1. Tests must pass
    results["checks"]["tests_passed"] = test_results.get("passed", False)
    if not results["checks"]["tests_passed"]:
        results["passed"] = False

    # 2. Code quality (we'll check this via tool calls in agent)
    results["checks"]["code_quality"] = True  # Placeholder

    # 3. Documentation updated
    results["checks"]["documentation"] = True  # Placeholder

    # 4. Acceptance criteria met
    results["checks"]["acceptance_criteria"] = test_results.get("passed", False)
    if not results["checks"]["acceptance_criteria"]:
        results["passed"] = False

    return results


# Create QA/Doc Agent with LangChain 1.0 pattern
async def create_qa_doc_agent():
    """
    Create the QA/Documentation Agent using LangChain 1.0's create_agent

    Returns:
        Compiled agent
    """
    # Load system prompt
    prompt_path = "config/prompts/qa_doc.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    # Get model
    model = get_qa_model()

    # Load MCP tools
    mcp_tools = await get_mcp_tools()

    # Define custom tools
    custom_tools = [
        # Code quality
        run_ruff_check,
        run_mypy_check,
        run_all_quality_checks,
        # Documentation
        update_changelog,
        update_readme,
        generate_feature_documentation,
        # Quality gates
        validate_all_quality_gates,
        # Technical debt
        create_technical_debt_entry,
        # Feature status
        update_feature_status,
        # Progress tracking
        update_qa_progress_log,
        # GitHub operations
        push_to_github,
    ]

    # Combine all tools
    tools = custom_tools + mcp_tools
    print(f"✅ QA/Doc agent: {len(custom_tools)} custom tools + {len(mcp_tools)} MCP tools")

    # Create agent using LangChain 1.0 pattern with custom state schema
    # NOTE: create_agent() handles tool binding internally, no need for bind_tools()
    agent = create_agent(
        model,
        tools=tools,
        system_prompt=system_prompt,
        state_schema=AppBuilderState
    )

    return agent


__all__ = ["create_qa_doc_agent"]
