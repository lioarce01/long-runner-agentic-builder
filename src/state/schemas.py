"""
State schemas for the multi-agent workflow
Uses TypedDict as required by LangChain 1.0 (Pydantic not supported)

CRITICAL: These schemas are GENERIC and work for ANY project type
Compatible with: LangChain 1.1.0, LangGraph 1.0.4 (November 2025)
"""

from typing import TypedDict, Annotated, Literal, Optional, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


# Tech stack definition
class TechStack(TypedDict):
    """Inferred technology stack for the project"""
    backend: list[str]  # e.g., ["python", "fastapi"] or ["node", "express"]
    frontend: Optional[list[str]]  # e.g., ["react", "typescript"] or None for APIs
    database: Optional[list[str]]  # e.g., ["postgresql"] or None for stateless
    testing: list[str]  # e.g., ["pytest", "playwright"] or ["jest", "cypress"]
    deployment: Optional[list[str]]  # e.g., ["docker", "kubernetes"] or None


# Project metadata
class ProjectMetadata(TypedDict):
    """Metadata about the project being built"""
    name: str  # Project name (e.g., "chatbot-clone", "ecommerce-mvp")
    type: str  # Project type: "web_app", "rest_api", "cli_tool", "desktop_app", etc.
    domain: str  # Domain: "e-commerce", "chat", "blog", "dashboard", "finance", etc.
    tech_stack: TechStack
    estimated_features: int  # Estimated number of features to implement


# Feature definition
class Feature(TypedDict):
    """Individual feature to be implemented (generic for any project type)"""
    id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    status: Literal["pending", "in_progress", "testing", "done", "failed"]
    priority: int  # 1 = highest (critical MVP), 5 = lowest (nice-to-have)
    complexity: Literal["low", "medium", "high"]
    attempts: int  # Number of implementation attempts
    tech_stack: TechStack  # Which parts of the stack this feature touches


# Git context
class GitContext(TypedDict):
    """Git repository state"""
    current_branch: str
    last_commit_sha: str
    uncommitted_changes: bool
    snapshot_tag: Optional[str]


# Test context
class TestContext(TypedDict):
    """Testing state and results"""
    last_run_timestamp: str
    passed_tests: int
    failed_tests: int
    coverage_percentage: float
    failure_details: Optional[list[dict]]
    last_result: Optional[dict]  # Detailed result of last test run


# Progress log entry
class ProgressLogEntry(TypedDict):
    """Individual progress log entry"""
    timestamp: str
    agent: str
    feature_id: Optional[str]
    action: str
    project_type: Optional[str]
    domain: Optional[str]
    commit_sha: Optional[str]
    notes: str


# Main state (compatible with LangChain 1.0 and LangGraph 1.0)
class AppBuilderState(TypedDict):
    """
    GENERIC state for building ANY type of application

    This state is persisted in PostgreSQL checkpoints and survives
    across sessions. Each agent can read and update this state.

    Works for: chatbots, e-commerce, REST APIs, blogs, dashboards, CLIs, etc.

    Compatible with:
    - LangChain 1.1.0 (Nov 24, 2025)
    - LangGraph 1.0.4 (Nov 25, 2025)
    - langgraph-checkpoint-postgres 3.0.1
    """
    # Core messaging (LangGraph 1.0 pattern - compatible with AgentState)
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Project information (dynamically inferred)
    project_metadata: ProjectMetadata
    repo_path: str
    project_name: str  # Added for easier reference

    # Feature management
    feature_list: list[Feature]
    current_feature: Optional[Feature]

    # Context objects
    git_context: GitContext
    test_context: TestContext

    # Workflow control
    phase: Literal["init", "coding", "testing", "qa", "complete"]
    retry_count: int
    max_retries: int

    # Scripts and paths
    init_script_path: Optional[str]

    # Progress tracking
    progress_log: list[ProgressLogEntry]


# Export all schemas
__all__ = [
    "TechStack",
    "ProjectMetadata",
    "Feature",
    "GitContext",
    "TestContext",
    "ProgressLogEntry",
    "AppBuilderState",
]
