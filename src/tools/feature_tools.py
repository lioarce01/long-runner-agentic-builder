"""
Feature management tools for the multi-agent system

Provides tools for:
- Dynamic feature list generation
- Feature selection and status updates
- Feature validation

Compatible with LangChain 1.0 create_agent pattern
"""

from langchain_core.tools import tool
from typing import Optional
import json
import os


@tool
def generate_feature_list_from_description(
    project_description: str,
    project_type: str,
    domain: str,
    estimated_count: int = 25
) -> list[dict]:
    """
    Generate a comprehensive feature list tailored to ANY software project

    This tool uses LLM reasoning to dynamically create features based on
    the project description, adapting to chatbots, e-commerce, APIs, etc.

    Args:
        project_description: Detailed description of what to build
        project_type: Type (web_app, rest_api, cli_tool, etc.)
        domain: Domain (e-commerce, chat, blog, dashboard, etc.)
        estimated_count: Approximate number of features to generate

    Returns:
        List of feature dictionaries in standard format

    Note:
        This is a placeholder. In production, this would call an LLM
        to generate context-specific features.
    """
    # TODO: Implement LLM-powered feature generation
    # For now, return a basic template
    features = []

    # Core features (MVP)
    features.append({
        "id": "f-001",
        "title": f"Initialize {project_type} project structure",
        "description": f"Create basic project structure for {domain} application",
        "acceptance_criteria": [
            "Project directory created",
            "Git repository initialized",
            "Basic configuration files present"
        ],
        "status": "pending",
        "priority": 1,
        "complexity": "low",
        "attempts": 0,
        "tech_stack": {
            "backend": ["python"],
            "frontend": None,
            "database": None,
            "testing": ["pytest"],
            "deployment": ["docker"]
        }
    })

    return features


@tool
def select_next_feature(feature_list: list[dict]) -> Optional[dict]:
    """
    Select the next highest-priority pending feature

    Args:
        feature_list: List of all features

    Returns:
        Next feature to implement, or None if all done

    Selection logic:
    1. Filter for "pending" status
    2. Sort by priority (1 = highest)
    3. Return first feature
    """
    pending_features = [
        f for f in feature_list
        if f.get("status") == "pending"
    ]

    if not pending_features:
        return None

    # Sort by priority (1 is highest)
    pending_features.sort(key=lambda f: f.get("priority", 999))

    return pending_features[0]


@tool
def update_feature_status(
    feature_id: str,
    new_status: str,
    feature_list_path: str
) -> str:
    """
    Update feature status in feature_list.json

    Args:
        feature_id: Feature ID (e.g., "f-001")
        new_status: New status (pending, in_progress, testing, done, failed)
        feature_list_path: Path to feature_list.json

    Returns:
        Success message

    Valid statuses:
    - pending: Not started
    - in_progress: Currently being worked on
    - testing: Implementation done, in testing
    - done: Completed and tested
    - failed: Failed after max retries
    """
    valid_statuses = ["pending", "in_progress", "testing", "done", "failed"]

    if new_status not in valid_statuses:
        return f"Error: Invalid status '{new_status}'. Must be one of: {valid_statuses}"

    try:
        with open(feature_list_path, "r") as f:
            features = json.load(f)

        # Find and update feature
        updated = False
        for feature in features:
            if feature["id"] == feature_id:
                feature["status"] = new_status
                updated = True
                break

        if not updated:
            return f"Error: Feature '{feature_id}' not found"

        # Write back
        with open(feature_list_path, "w", encoding="utf-8") as f:
            json.dump(features, f, indent=2)

        return f"Feature '{feature_id}' status updated to '{new_status}'"

    except FileNotFoundError:
        return f"Error: Feature list file not found: {feature_list_path}"
    except Exception as e:
        return f"Error updating feature status: {e}"


@tool
def get_feature_by_id(feature_id: str, feature_list: list[dict]) -> Optional[dict]:
    """
    Get a specific feature by ID

    Args:
        feature_id: Feature ID to find
        feature_list: List of all features

    Returns:
        Feature dict or None if not found
    """
    for feature in feature_list:
        if feature.get("id") == feature_id:
            return feature
    return None


@tool
def count_features_by_status(feature_list: list[dict]) -> dict:
    """
    Count features by status for progress tracking

    Args:
        feature_list: List of all features

    Returns:
        Dictionary with counts per status
    """
    counts = {
        "pending": 0,
        "in_progress": 0,
        "testing": 0,
        "done": 0,
        "failed": 0
    }

    for feature in feature_list:
        status = feature.get("status", "pending")
        if status in counts:
            counts[status] += 1

    counts["total"] = len(feature_list)
    counts["completion_percentage"] = (
        (counts["done"] / len(feature_list) * 100) if feature_list else 0
    )

    return counts


__all__ = [
    "generate_feature_list_from_description",
    "select_next_feature",
    "update_feature_status",
    "get_feature_by_id",
    "count_features_by_status",
]
