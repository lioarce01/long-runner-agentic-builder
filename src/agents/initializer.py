"""
Initializer Agent - Bootstraps ANY type of software project

This agent analyzes project requirements, infers tech stack, generates
features, and initializes the repository.

Compatible with:
- LangChain 1.1.0 (create_agent pattern)
- LangGraph 1.0.4
"""

from langchain.agents import create_agent
from langchain_core.tools import tool
from src.utils.model import get_initializer_model
from src.tools.feature_tools import (
    generate_feature_list_from_description,
    update_feature_status
)
from src.tools.git_tools import create_git_repo, create_git_commit
import os
import json
from datetime import datetime
from typing import Optional


# Additional tools specific to Initializer Agent

@tool
def create_init_script(repo_path: str, tech_stack: dict) -> str:
    """
    Create init.sh script tailored to the inferred tech stack

    Args:
        repo_path: Path to repository
        tech_stack: Inferred technology stack

    Returns:
        Path to created init.sh script

    Example:
        >>> create_init_script("/path/to/repo", {"backend": ["python", "fastapi"]})
        "/path/to/repo/init.sh"
    """
    backend = tech_stack.get("backend", [])
    frontend = tech_stack.get("frontend")
    database = tech_stack.get("database")

    script_lines = ["#!/bin/bash", "", "# Auto-generated init script", ""]

    # Backend setup
    if "python" in backend:
        script_lines.extend([
            "echo '📦 Setting up Python backend...'",
            "python -m venv .venv",
            "source .venv/bin/activate || .venv\\Scripts\\activate",
            "pip install -r requirements.txt",
            ""
        ])

        if "fastapi" in backend:
            script_lines.extend([
                "echo '🚀 Starting FastAPI server...'",
                "uvicorn main:app --reload &",
                ""
            ])
        elif "django" in backend:
            script_lines.extend([
                "echo '🚀 Starting Django server...'",
                "python manage.py migrate",
                "python manage.py runserver &",
                ""
            ])

    elif "node" in backend or "javascript" in backend:
        script_lines.extend([
            "echo '📦 Setting up Node.js backend...'",
            "npm install",
            ""
        ])

        if "express" in backend:
            script_lines.extend([
                "echo '🚀 Starting Express server...'",
                "npm run dev &",
                ""
            ])

    # Frontend setup
    if frontend and "react" in frontend:
        script_lines.extend([
            "echo '📦 Setting up React frontend...'",
            "cd frontend",
            "npm install",
            "npm start &",
            "cd ..",
            ""
        ])
    elif frontend and "vue" in frontend:
        script_lines.extend([
            "echo '📦 Setting up Vue frontend...'",
            "cd frontend",
            "npm install",
            "npm run serve &",
            "cd ..",
            ""
        ])

    # Database setup
    if database and "postgresql" in database:
        script_lines.extend([
            "echo '🗄️ Checking PostgreSQL...'",
            "docker-compose up -d postgres",
            ""
        ])
    elif database and "mongodb" in database:
        script_lines.extend([
            "echo '🗄️ Checking MongoDB...'",
            "docker-compose up -d mongodb",
            ""
        ])

    script_lines.extend([
        "echo '✅ Development environment ready!'",
        "echo 'Press Ctrl+C to stop all services'",
        "wait"
    ])

    script_content = "\n".join(script_lines)

    init_path = os.path.join(repo_path, "init.sh")
    os.makedirs(repo_path, exist_ok=True)

    with open(init_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    # Make executable
    os.chmod(init_path, 0o755)

    return init_path


@tool
def initialize_progress_log(repo_path: str, project_metadata: dict) -> str:
    """
    Create initial progress_log.json file

    Args:
        repo_path: Path to repository
        project_metadata: Project metadata dict

    Returns:
        Path to created progress_log.json
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent": "initializer",
        "feature_id": None,
        "action": "initialized",
        "project_type": project_metadata.get("type", "unknown"),
        "domain": project_metadata.get("domain", "unknown"),
        "commit_sha": None,
        "notes": f"Initialized {project_metadata.get('type')} project in {project_metadata.get('domain')} domain"
    }

    log_path = os.path.join(repo_path, "progress_log.json")
    os.makedirs(repo_path, exist_ok=True)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump([log_entry], f, indent=2)

    return log_path


@tool
def save_feature_list(repo_path: str, features: list[dict]) -> str:
    """
    Save feature list to feature_list.json

    Args:
        repo_path: Path to repository
        features: List of feature dictionaries

    Returns:
        Path to created feature_list.json
    """
    feature_path = os.path.join(repo_path, "feature_list.json")
    os.makedirs(repo_path, exist_ok=True)

    with open(feature_path, "w", encoding="utf-8") as f:
        json.dump(features, f, indent=2)

    return feature_path


@tool
def analyze_project_requirements(project_description: str) -> dict:
    """
    Analyze project description and extract metadata

    Args:
        project_description: User's project description

    Returns:
        Project metadata dictionary

    This is a placeholder - in production, this would use LLM reasoning
    to deeply analyze the requirements.
    """
    # TODO: Use LLM to analyze project description
    # For now, simple keyword-based inference

    description_lower = project_description.lower()

    # Infer project type
    if "api" in description_lower or "backend" in description_lower:
        project_type = "rest_api"
    elif "cli" in description_lower or "command" in description_lower:
        project_type = "cli_tool"
    elif "chat" in description_lower or "messaging" in description_lower:
        project_type = "web_app"
        domain = "chat"
    elif "ecommerce" in description_lower or "shop" in description_lower:
        project_type = "web_app"
        domain = "e-commerce"
    elif "blog" in description_lower:
        project_type = "web_app"
        domain = "blog"
    else:
        project_type = "web_app"
        domain = "general"

    # Infer domain if not already set
    if "domain" not in locals():
        if "finance" in description_lower:
            domain = "finance"
        elif "health" in description_lower:
            domain = "healthcare"
        elif "dashboard" in description_lower:
            domain = "dashboard"
        else:
            domain = "general"

    return {
        "type": project_type,
        "domain": domain,
        "description": project_description
    }


# Create Initializer Agent with LangChain 1.0 pattern
def create_initializer_agent():
    """
    Create the Initializer Agent using LangChain 1.0's create_agent

    Returns:
        Compiled agent
    """
    # Load system prompt
    prompt_path = "config/prompts/initializer.txt"
    with open(prompt_path, "r") as f:
        system_prompt = f.read()

    # Get model
    model = get_initializer_model()

    # Define tools
    tools = [
        analyze_project_requirements,
        generate_feature_list_from_description,
        create_git_repo,
        create_init_script,
        initialize_progress_log,
        save_feature_list,
        create_git_commit,
    ]

    # Create agent using LangChain 1.0 pattern
    agent = create_agent(
        model,
        tools=tools,
        system_prompt=system_prompt
    )

    return agent


__all__ = ["create_initializer_agent"]
