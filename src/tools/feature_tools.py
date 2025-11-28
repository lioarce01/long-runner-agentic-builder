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

    This tool generates features based on project type and domain,
    adapting to REST APIs, web apps, CLIs, etc.

    Args:
        project_description: Detailed description of what to build
        project_type: Type (web_app, rest_api, cli_tool, etc.)
        domain: Domain (e-commerce, chat, blog, dashboard, etc.)
        estimated_count: Approximate number of features to generate

    Returns:
        List of feature dictionaries in standard format
    """
    features = []

    # Determine tech stack based on project type
    if project_type == "rest_api":
        backend = ["python", "fastapi"]
        frontend = None
        database = None if "simple" in project_description.lower() else ["postgresql"]
        testing = ["pytest", "httpx"]
        deployment = ["docker"]
    elif project_type == "web_app":
        backend = ["python", "fastapi"]
        frontend = ["react", "typescript"]
        database = ["postgresql"]
        testing = ["pytest", "playwright"]
        deployment = ["docker"]
    elif project_type == "cli_tool":
        backend = ["python", "click"]
        frontend = None
        database = None
        testing = ["pytest"]
        deployment = None
    else:
        # Default
        backend = ["python"]
        frontend = None
        database = None
        testing = ["pytest"]
        deployment = ["docker"]

    # Feature ID counter
    feature_count = 1

    def add_feature(title: str, description: str, criteria: list, priority: int, complexity: str):
        nonlocal feature_count
        features.append({
            "id": f"f-{feature_count:03d}",
            "title": title,
            "description": description,
            "acceptance_criteria": criteria,
            "status": "pending",
            "priority": priority,
            "complexity": complexity,
            "attempts": 0,
            "tech_stack": {
                "backend": backend,
                "frontend": frontend,
                "database": database,
                "testing": testing,
                "deployment": deployment
            }
        })
        feature_count += 1

    # === CORE SETUP FEATURES (Priority 1) ===
    add_feature(
        "Project structure initialization",
        "Create basic project directory structure with all necessary folders",
        [
            "Project directory created",
            "Source code folder created",
            "Tests folder created"
        ],
        priority=1,
        complexity="low"
    )

    add_feature(
        "Dependencies configuration",
        "Create requirements.txt with all necessary Python dependencies",
        [
            "requirements.txt file created",
            "All core dependencies listed",
            "Version pinning configured"
        ],
        priority=1,
        complexity="low"
    )

    add_feature(
        "Git configuration",
        "Initialize git repository and create .gitignore",
        [
            "Git repository initialized",
            ".gitignore file created",
            "Python-specific ignores configured"
        ],
        priority=1,
        complexity="low"
    )

    # === REST API SPECIFIC FEATURES ===
    if project_type == "rest_api":
        add_feature(
            "FastAPI application initialization",
            "Create main FastAPI application with basic configuration",
            [
                "FastAPI app instance created",
                "Main application file created",
                "CORS middleware configured"
            ],
            priority=1,
            complexity="low"
        )

        add_feature(
            "Health check endpoint",
            "Implement GET /health endpoint for monitoring",
            [
                "Endpoint returns 200 status",
                "Response includes timestamp",
                "Endpoint documented in OpenAPI"
            ],
            priority=1,
            complexity="low"
        )

        # Check if user wants custom endpoint (parse description)
        if "endpoint" in project_description.lower() or "GET" in project_description:
            add_feature(
                "Custom GET endpoint implementation",
                "Implement the main GET endpoint as per requirements",
                [
                    "Endpoint created and functional",
                    "Returns expected response",
                    "Proper HTTP status codes"
                ],
                priority=1,
                complexity="medium"
            )

        add_feature(
            "Environment variables setup",
            "Configure environment variables and .env file",
            [
                ".env.example file created",
                "Environment variables loaded",
                "Configuration validated"
            ],
            priority=2,
            complexity="low"
        )

        add_feature(
            "Logging configuration",
            "Set up structured logging for the application",
            [
                "Logger configured",
                "Log levels defined",
                "Request/response logging works"
            ],
            priority=2,
            complexity="low"
        )

        add_feature(
            "Error handling middleware",
            "Implement global error handling middleware",
            [
                "Custom exception handlers created",
                "Proper error responses returned",
                "500 errors logged"
            ],
            priority=2,
            complexity="medium"
        )

        add_feature(
            "API documentation (OpenAPI/Swagger)",
            "Ensure Swagger UI is accessible and documented",
            [
                "Swagger UI accessible at /docs",
                "All endpoints documented",
                "Request/response schemas defined"
            ],
            priority=2,
            complexity="low"
        )

        add_feature(
            "Request validation",
            "Implement Pydantic models for request validation",
            [
                "Pydantic models created",
                "Validation errors handled properly",
                "Type hints used"
            ],
            priority=2,
            complexity="medium"
        )

        add_feature(
            "Unit tests for endpoints",
            "Write unit tests for all API endpoints",
            [
                "Test file created",
                "All endpoints have tests",
                "Tests pass successfully"
            ],
            priority=2,
            complexity="medium"
        )

        add_feature(
            "Pytest configuration",
            "Configure pytest with coverage and fixtures",
            [
                "pytest.ini created",
                "Test fixtures defined",
                "Coverage threshold set"
            ],
            priority=2,
            complexity="low"
        )

        add_feature(
            "Docker configuration",
            "Create Dockerfile and docker-compose.yml",
            [
                "Dockerfile created",
                "docker-compose.yml created",
                "Application runs in container"
            ],
            priority=3,
            complexity="medium"
        )

        add_feature(
            "README documentation",
            "Write comprehensive README with setup instructions",
            [
                "README.md created",
                "Setup instructions included",
                "API endpoints documented"
            ],
            priority=3,
            complexity="low"
        )

    # === WEB APP SPECIFIC FEATURES ===
    elif project_type == "web_app":
        add_feature(
            "Frontend project setup",
            "Initialize React/TypeScript frontend project",
            [
                "Frontend directory created",
                "React app initialized",
                "TypeScript configured"
            ],
            priority=1,
            complexity="medium"
        )

        add_feature(
            "Backend API initialization",
            "Set up FastAPI backend with database",
            [
                "FastAPI app created",
                "Database connection configured",
                "API routes defined"
            ],
            priority=1,
            complexity="medium"
        )

    # === CLI TOOL SPECIFIC FEATURES ===
    elif project_type == "cli_tool":
        add_feature(
            "CLI framework setup",
            "Initialize Click-based CLI application",
            [
                "Click installed",
                "Main CLI group created",
                "Entry point configured"
            ],
            priority=1,
            complexity="low"
        )

    return features


@tool
def select_next_feature(runtime) -> Optional[dict]:
    """
    Select the next highest-priority pending feature

    Reads feature_list.json from repo_path and returns the highest-priority
    pending feature.

    Args:
        runtime: ToolRuntime for accessing state (repo_path)

    Returns:
        Next feature to implement, or None if all done

    Selection logic:
    1. Read feature_list.json from repo_path
    2. Filter for "pending" status
    3. Sort by priority (1 = highest)
    4. Return first feature

    Example:
        >>> select_next_feature(runtime)
        {"id": "f-001", "title": "...", "status": "pending", ...}
    """
    repo_path = runtime.state.get("repo_path", "")
    feature_list_path = os.path.join(repo_path, "feature_list.json")

    if not os.path.exists(feature_list_path):
        return None

    with open(feature_list_path, "r", encoding="utf-8") as f:
        feature_list = json.load(f)

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
    runtime
) -> str:
    """
    Update feature status in feature_list.json

    Automatically reads feature_list.json from repo_path in state.

    Args:
        feature_id: Feature ID (e.g., "f-001")
        new_status: New status (pending, in_progress, testing, done, failed)
        runtime: ToolRuntime for accessing state (repo_path)

    Returns:
        Success message

    Valid statuses:
    - pending: Not started
    - in_progress: Currently being worked on
    - testing: Implementation done, in testing
    - done: Completed and tested
    - failed: Failed after max retries

    Example:
        >>> update_feature_status("f-001", "testing", runtime)
        "Feature f-001 status updated to testing"
    """
    valid_statuses = ["pending", "in_progress", "testing", "done", "failed"]

    if new_status not in valid_statuses:
        return f"Error: Invalid status '{new_status}'. Must be one of: {valid_statuses}"

    repo_path = runtime.state.get("repo_path", "")
    feature_list_path = os.path.join(repo_path, "feature_list.json")

    if not os.path.exists(feature_list_path):
        return f"Error: feature_list.json not found at {feature_list_path}"

    try:
        with open(feature_list_path, "r", encoding="utf-8") as f:
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
def get_feature_by_id(feature_id: str, runtime) -> Optional[dict]:
    """
    Get a specific feature by ID from feature_list.json

    Args:
        feature_id: Feature ID to find (e.g., "f-001")
        runtime: ToolRuntime for accessing state (repo_path)

    Returns:
        Feature dict or None if not found

    Example:
        >>> get_feature_by_id("f-001", runtime)
        {"id": "f-001", "title": "...", "status": "pending", ...}
    """
    repo_path = runtime.state.get("repo_path", "")
    feature_list_path = os.path.join(repo_path, "feature_list.json")

    if not os.path.exists(feature_list_path):
        return None

    with open(feature_list_path, "r", encoding="utf-8") as f:
        feature_list = json.load(f)

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
