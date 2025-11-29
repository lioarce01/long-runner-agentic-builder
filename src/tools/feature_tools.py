"""
Feature management tools for the multi-agent system

Provides tools for:
- Dynamic feature list generation
- Feature selection and status updates
- Feature validation

Compatible with LangChain 1.0 create_agent pattern
"""

from langchain_core.tools import tool
from langchain.tools import InjectedState
from typing import Optional
from typing_extensions import Annotated
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
    description_lower = project_description.lower()
    
    # CRITICAL: Detect project complexity from description
    complexity = "medium"  # default
    max_features = estimated_count
    
    if "simple" in description_lower or "basic" in description_lower:
        complexity = "simple"
        max_features = min(6, estimated_count)
    elif "mvp" in description_lower or "minimal" in description_lower:
        complexity = "mvp"
        max_features = min(12, estimated_count)
    elif "full" in description_lower or "complete" in description_lower:
        complexity = "full"
        max_features = max(20, estimated_count)

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
    # Only add setup features if not too simple
    if complexity != "simple" or feature_count == 1:
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
    
    # Only add Git config for non-simple projects (Git is already initialized by Initializer)
    if complexity != "simple":
        add_feature(
            "Git configuration",
            "Initialize git repository and create .gitignore",
            [
                "Git repository initialized",
                ".gitignore file created",
                "Python-specific ignores configured"
            ],
            priority=3,
            complexity="low"
        )

    # === REST API SPECIFIC FEATURES ===
    if project_type == "rest_api":
        
        # SPECIAL CASE: Calculator project - parse specific endpoints
        if "calculator" in description_lower:
            # Add Pydantic models feature
            add_feature(
                "Pydantic models for calculator",
                "Create request and response models for calculator operations",
                [
                    "CalculatorRequest model created with a, b fields",
                    "CalculatorResponse model created with result, operation fields",
                    "Type hints and validation configured"
                ],
                priority=1,
                complexity="low"
            )
            
            # Parse specific operations mentioned
            if "/add" in description_lower or "add" in description_lower or "addition" in description_lower:
                add_feature(
                    "POST /calculate/add endpoint",
                    "Implement addition endpoint with proper validation",
                    [
                        "Endpoint accepts POST requests",
                        "Adds two numbers correctly",
                        "Returns proper JSON response",
                        "Validates input using Pydantic"
                    ],
                    priority=1,
                    complexity="low"
                )
            
            if "/subtract" in description_lower or "subtract" in description_lower or "subtraction" in description_lower:
                add_feature(
                    "POST /calculate/subtract endpoint",
                    "Implement subtraction endpoint with proper validation",
                    [
                        "Endpoint accepts POST requests",
                        "Subtracts two numbers correctly",
                        "Returns proper JSON response",
                        "Validates input using Pydantic"
                    ],
                    priority=1,
                    complexity="low"
                )
            
            if "/multiply" in description_lower or "multiply" in description_lower or "multiplication" in description_lower:
                add_feature(
                    "POST /calculate/multiply endpoint",
                    "Implement multiplication endpoint with proper validation",
                    [
                        "Endpoint accepts POST requests",
                        "Multiplies two numbers correctly",
                        "Returns proper JSON response",
                        "Validates input using Pydantic"
                    ],
                    priority=1,
                    complexity="low"
                )
            
            if "/divide" in description_lower or "divide" in description_lower or "division" in description_lower:
                add_feature(
                    "POST /calculate/divide endpoint",
                    "Implement division endpoint with proper validation and error handling",
                    [
                        "Endpoint accepts POST requests",
                        "Divides two numbers correctly",
                        "Returns proper JSON response",
                        "Handles division by zero error"
                    ],
                    priority=1,
                    complexity="medium"
                )
            
            # Add Swagger documentation
            if "swagger" in description_lower or "documentation" in description_lower or complexity != "simple":
                add_feature(
                    "Swagger documentation",
                    "Ensure Swagger UI is accessible and all endpoints are documented",
                    [
                        "Swagger UI accessible at /docs",
                        "All endpoints documented with examples",
                        "Request/response schemas properly defined"
                    ],
                    priority=2,
                    complexity="low"
                )
            
            # Add tests for simple projects
            if complexity == "simple":
                add_feature(
                    "Unit tests for calculator endpoints",
                    "Write comprehensive tests for all calculator operations",
                    [
                        "Test file created in tests/ directory",
                        "Tests for all calculator endpoints",
                        "Tests for edge cases (negative numbers, zero, decimals)",
                        "All tests pass successfully"
                    ],
                    priority=2,
                    complexity="medium"
                )
        
        # GENERAL REST API (not calculator)
        else:
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
            if "endpoint" in description_lower or "GET" in description_lower:
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

            # Only add these for non-simple, non-calculator projects
            if complexity != "simple" and "calculator" not in description_lower:
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

            # Only add Docker/README for MVP or full projects
            if complexity in ["mvp", "full"]:
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
    elif project_type == "web_app" and complexity != "simple":
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

    # Limit features to max_features
    if len(features) > max_features:
        features = features[:max_features]
    
    return features


@tool
def select_next_feature(state: Annotated[dict, InjectedState]) -> Optional[dict]:
    """
    Select the next feature to work on

    Priority order:
    1. Features in "testing" status (need retry after test failure)
    2. Features in "pending" status (new features)

    Returns:
        Next feature to implement, or None if all done

    Selection logic:
    1. Read feature_list.json from repo_path
    2. FIRST: Check for "testing" features (need retry)
    3. THEN: Check for "pending" features (new work)
    4. Sort by priority (1 = highest)
    5. Return first feature

    Example:
        >>> select_next_feature(state)
        {"id": "f-001", "title": "...", "status": "pending", ...}
    """
    repo_path = state.get("repo_path", "")
    feature_list_path = os.path.join(repo_path, "feature_list.json")

    if not os.path.exists(feature_list_path):
        return None

    with open(feature_list_path, "r", encoding="utf-8") as f:
        feature_list = json.load(f)

    # Helper to safely get priority as int
    def get_priority(f):
        p = f.get("priority", 999)
        return int(p) if isinstance(p, (int, str)) and str(p).isdigit() else 999

    # PRIORITY 1: Features that need retry (status = "testing" means tests failed)
    # These should be fixed before starting new features
    testing_features = [
        f for f in feature_list
        if f.get("status") == "testing"
    ]
    
    if testing_features:
        # Sort by priority, then by attempts (fewer attempts first)
        testing_features.sort(key=lambda f: (get_priority(f), f.get("attempts", 0)))
        selected = testing_features[0]
        print(f"\n[select_next_feature] Retry feature: {selected['id']} (attempts: {selected.get('attempts', 0)})")
        return selected

    # PRIORITY 2: New pending features
    pending_features = [
        f for f in feature_list
        if f.get("status") == "pending"
    ]

    if not pending_features:
        return None

    # Sort by priority (1 is highest)
    pending_features.sort(key=lambda f: get_priority(f))
    selected = pending_features[0]
    print(f"\n[select_next_feature] New feature: {selected['id']}")
    return selected


@tool
def update_feature_status(
    feature_id: str,
    new_status: str,
    state: Annotated[dict, InjectedState],
    increment_attempts: bool = False
) -> str:
    """
    Update feature status in feature_list.json

    Automatically reads feature_list.json from repo_path in state.

    Args:
        feature_id: Feature ID (e.g., "f-001")
        new_status: New status (pending, in_progress, testing, done, failed)
        increment_attempts: If True, increment the attempts counter (for retries)

    Returns:
        Success message

    Valid statuses:
    - pending: Not started
    - in_progress: Currently being worked on
    - testing: Implementation done, in testing
    - done: Completed and tested
    - failed: Failed after max retries

    Example:
        >>> update_feature_status("f-001", "testing", state)
        "Feature f-001 status updated to testing"
    """
    valid_statuses = ["pending", "in_progress", "testing", "done", "failed"]

    if new_status not in valid_statuses:
        return f"Error: Invalid status '{new_status}'. Must be one of: {valid_statuses}"

    repo_path = state.get("repo_path", "")
    feature_list_path = os.path.join(repo_path, "feature_list.json")

    if not os.path.exists(feature_list_path):
        return f"Error: feature_list.json not found at {feature_list_path}"

    try:
        with open(feature_list_path, "r", encoding="utf-8") as f:
            features = json.load(f)

        # Find and update feature
        updated = False
        attempts = 0
        for feature in features:
            if feature["id"] == feature_id:
                old_status = feature.get("status", "unknown")
                feature["status"] = new_status
                
                # Handle attempts counter
                if increment_attempts:
                    feature["attempts"] = feature.get("attempts", 0) + 1
                    attempts = feature["attempts"]
                    print(f"[update_feature_status] {feature_id}: attempts incremented to {attempts}")
                
                # Reset attempts when feature is done
                if new_status == "done":
                    feature["attempts"] = 0
                
                updated = True
                print(f"[update_feature_status] {feature_id}: {old_status} -> {new_status}")
                break

        if not updated:
            return f"Error: Feature '{feature_id}' not found"

        # Write back
        with open(feature_list_path, "w", encoding="utf-8") as f:
            json.dump(features, f, indent=2)

        msg = f"Feature '{feature_id}' status updated to '{new_status}'"
        if increment_attempts:
            msg += f" (attempt {attempts})"
        return msg

    except FileNotFoundError:
        return f"Error: Feature list file not found: {feature_list_path}"
    except Exception as e:
        return f"Error updating feature status: {e}"


@tool
def increment_feature_attempts(
    feature_id: str,
    state: Annotated[dict, InjectedState]
) -> str:
    """
    Increment the attempts counter for a feature (used after test failure)

    Args:
        feature_id: Feature ID (e.g., "f-001")

    Returns:
        Success message with current attempt count
    """
    repo_path = state.get("repo_path", "")
    feature_list_path = os.path.join(repo_path, "feature_list.json")

    if not os.path.exists(feature_list_path):
        return f"Error: feature_list.json not found at {feature_list_path}"

    try:
        with open(feature_list_path, "r", encoding="utf-8") as f:
            features = json.load(f)

        for feature in features:
            if feature["id"] == feature_id:
                feature["attempts"] = feature.get("attempts", 0) + 1
                attempts = feature["attempts"]
                
                # Write back
                with open(feature_list_path, "w", encoding="utf-8") as f:
                    json.dump(features, f, indent=2)
                
                print(f"[increment_feature_attempts] {feature_id}: attempts = {attempts}")
                return f"Feature '{feature_id}' attempts incremented to {attempts}"

        return f"Error: Feature '{feature_id}' not found"

    except Exception as e:
        return f"Error incrementing attempts: {e}"


@tool
def get_feature_by_id(
    feature_id: str,
    state: Annotated[dict, InjectedState]
) -> Optional[dict]:
    """
    Get a specific feature by ID from feature_list.json

    Args:
        feature_id: Feature ID to find (e.g., "f-001")

    Returns:
        Feature dict or None if not found

    Example:
        >>> get_feature_by_id("f-001", state)
        {"id": "f-001", "title": "...", "status": "pending", ...}
    """
    repo_path = state.get("repo_path", "")
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
    "increment_feature_attempts",
    "get_feature_by_id",
    "count_features_by_status",
]
