"""
GitOps Agent - Handles all Git and GitHub operations

This agent is responsible for:
- Initializing Git repositories
- Creating commits with descriptive messages
- Creating GitHub repositories
- Pushing code to GitHub
- Managing branches and remotes

Compatible with:
- LangChain 1.1.0 (create_agent pattern)
- LangGraph 1.0.4
"""

from langchain.agents import create_agent
from src.utils.model import get_coding_model
from src.state.schemas import AppBuilderState
from src.mcp_config.client import get_mcp_tools
from src.tools.git_tools import (
    create_git_repo,
    create_git_commit,
    get_git_status,
    get_git_diff,
    get_git_log
)
from src.tools.github_tools import (
    create_github_repo,
    add_github_remote,
    push_to_github
)


# Create GitOps Agent with LangChain 1.0 pattern
async def create_gitops_agent():
    """
    Create the GitOps Agent using LangChain 1.0's create_agent
    
    This agent handles all Git/GitHub operations after other agents
    complete their work (Initializer, Coding, QA).
    
    Returns:
        Compiled agent
    """
    # Load system prompt
    prompt_path = "config/prompts/gitops.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()
    
    # Get model (reuse coding model for now)
    model = get_coding_model()
    
    # Load MCP tools (if any)
    mcp_tools = await get_mcp_tools()
    
    # Define custom tools - ONLY Git/GitHub operations
    custom_tools = [
        # Git operations
        create_git_repo,
        create_git_commit,
        get_git_status,
        get_git_diff,
        get_git_log,
        # GitHub operations
        create_github_repo,
        add_github_remote,
        push_to_github,
    ]
    
    # Combine all tools
    tools = custom_tools + mcp_tools
    print(f"✅ GitOps agent: {len(custom_tools)} custom tools + {len(mcp_tools)} MCP tools")
    
    # Create agent using LangChain 1.0 pattern with custom state schema
    agent = create_agent(
        model,
        tools=tools,
        system_prompt=system_prompt,
        state_schema=AppBuilderState
    )
    
    return agent


__all__ = ["create_gitops_agent"]

