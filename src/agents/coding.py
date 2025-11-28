"""
Coding Agent - Implements features incrementally

This agent selects features, implements them with clean code,
runs tests, and creates commits.

Compatible with:
- LangChain 1.1.0 (create_agent pattern)
- LangGraph 1.0.4
"""

from langchain.agents import create_agent
from langchain_core.tools import tool
from src.utils.model import get_coding_model
from src.state.schemas import AppBuilderState
from src.mcp_config.client import get_mcp_tools
from src.tools.feature_tools import (
    select_next_feature,
    update_feature_status,
    get_feature_by_id
)
from src.tools.filesystem_tools import (
    create_directory,
    write_file,
    read_file,
    list_directory,
    file_exists,
    get_file_info
)
from src.tools.test_tools import run_pytest_tests
import os
import json
import subprocess
from datetime import datetime


@tool
def run_init_script(repo_path: str) -> str:
    """
    Run the init.sh script to start development servers

    Args:
        repo_path: Path to repository

    Returns:
        Output message

    Example:
        >>> run_init_script("/path/to/repo")
        "Development servers started"
    """
    init_script = os.path.join(repo_path, "init.sh")

    if not os.path.exists(init_script):
        return f"init.sh not found at {init_script}"

    try:
        # Run in background (don't wait for completion)
        subprocess.Popen(
            ["/bin/bash", init_script],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return "Development servers starting in background..."
    except Exception as e:
        return f"Error running init script: {e}"


@tool
def read_progress_log(repo_path: str) -> list[dict]:
    """
    Read progress log to understand project state

    Args:
        repo_path: Path to repository

    Returns:
        List of progress log entries

    Example:
        >>> read_progress_log("/path/to/repo")
        [{"timestamp": "...", "agent": "initializer", ...}]
    """
    log_path = os.path.join(repo_path, "progress_log.json")

    if not os.path.exists(log_path):
        return []

    try:
        with open(log_path, "r") as f:
            return json.load(f)
    except Exception as e:
        return [{"error": f"Failed to read progress log: {e}"}]


@tool
def update_progress_log_entry(
    repo_path: str,
    agent: str,
    feature_id: str,
    action: str,
    commit_sha: str = None,
    notes: str = ""
) -> str:
    """
    Add entry to progress log

    Args:
        repo_path: Path to repository
        agent: Agent name
        feature_id: Feature ID
        action: Action taken
        commit_sha: Optional commit SHA
        notes: Optional notes

    Returns:
        Success message
    """
    log_path = os.path.join(repo_path, "progress_log.json")

    # Read existing log
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            log = json.load(f)
    else:
        log = []

    # Add new entry
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent": agent,
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
    print(f"   Agent: {agent}")
    print(f"   Feature: {feature_id}")
    print(f"   Action: {action}")
    print(f"{'='*60}\n")

    return f"Progress log updated with {action} for {feature_id}"


@tool
def read_feature_list(repo_path: str) -> list[dict]:
    """
    Read feature list from repository

    Args:
        repo_path: Path to repository

    Returns:
        List of features
    """
    feature_path = os.path.join(repo_path, "feature_list.json")

    if not os.path.exists(feature_path):
        return []

    try:
        with open(feature_path, "r") as f:
            return json.load(f)
    except Exception as e:
        return [{"error": f"Failed to read feature list: {e}"}]


# Create Coding Agent with LangChain 1.0 pattern
async def create_coding_agent():
    """
    Create the Coding Agent using LangChain 1.0's create_agent

    Returns:
        Compiled agent
    """
    # Load system prompt
    prompt_path = "config/prompts/coding.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    # Get model
    model = get_coding_model()

    # Load MCP tools
    mcp_tools = await get_mcp_tools()

    # Define custom tools
    # NOTE: Git operations removed - GitOps Agent handles all Git/GitHub
    custom_tools = [
        # Feature management
        read_feature_list,
        select_next_feature,
        get_feature_by_id,
        update_feature_status,
        # Filesystem operations
        create_directory,
        write_file,
        read_file,
        list_directory,
        file_exists,
        get_file_info,
        # Progress tracking
        read_progress_log,
        update_progress_log_entry,
        # Development workflow
        run_init_script,
        run_pytest_tests,
    ]

    # Combine all tools
    tools = custom_tools + mcp_tools
    print(f"✅ Coding agent: {len(custom_tools)} custom tools + {len(mcp_tools)} MCP tools")

    # Create agent using LangChain 1.0 pattern with custom state schema
    # NOTE: create_agent() handles tool binding internally, no need for bind_tools()
    agent = create_agent(
        model,
        tools=tools,
        system_prompt=system_prompt,
        state_schema=AppBuilderState
    )

    return agent


__all__ = ["create_coding_agent"]
