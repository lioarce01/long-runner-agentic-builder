"""
MCP (Model Context Protocol) client configuration

Integrates with LangChain 1.0 via langchain-mcp-adapters for:
- Filesystem operations
- Git operations
- GitHub operations (optional)

Compatible with:
- LangChain 1.1.0 (Nov 24, 2025)
- langchain-mcp-adapters 0.1.0+ (March 2025)
"""

from langchain_mcp_adapters.client import MultiServerMCPClient
import os
from typing import Any, Optional


async def create_mcp_client(project_path: Optional[str] = None) -> MultiServerMCPClient:
    """
    Create MCP client with filesystem, git, and optionally GitHub servers

    Uses the LangChain 1.0 MCP adapters pattern to integrate
    Model Context Protocol servers as LangChain tools.

    Args:
        project_path: Path to the project directory (defaults to OUTPUT_DIR env var)

    Returns:
        Configured MultiServerMCPClient instance

    Example:
        >>> client = await create_mcp_client("/path/to/project")
        >>> tools = await client.get_tools()
        >>> agent = create_agent(model, tools=tools)
    """
    if project_path is None:
        project_path = os.getenv("OUTPUT_DIR", "./output")

    github_token = os.getenv("GITHUB_TOKEN")

    config: dict[str, Any] = {}

    # Filesystem server (always enabled)
    # Uses stdio transport for local MCP server
    config["filesystem"] = {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", project_path],
        "transport": "stdio"
    }

    # Git server (always enabled)
    # Uses python -m to run mcp-server-git
    config["git"] = {
        "command": "python",
        "args": ["-m", "mcp_server_git", "--repository", project_path],
        "transport": "stdio"
    }

    # GitHub server (optional - requires token)
    # Uses streamable_http transport for remote MCP server
    if github_token:
        config["github"] = {
            "url": "https://api.githubcopilot.com/mcp/",
            "transport": "streamable_http",
            "headers": {"Authorization": f"Bearer {github_token}"}
        }
        print("✅ GitHub MCP server enabled")
    else:
        print("⚠️  GITHUB_TOKEN not set - GitHub MCP server disabled")

    try:
        client = MultiServerMCPClient(config)
        print(f"✅ MCP client initialized with {len(config)} servers")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize MCP client: {e}")
        # Fallback to filesystem only
        print("   Falling back to filesystem-only MCP client")
        return MultiServerMCPClient({
            "filesystem": config["filesystem"]
        })


async def get_mcp_tools(project_path: Optional[str] = None) -> list:
    """
    Get all tools from MCP servers as LangChain tools

    Returns tools compatible with LangChain 1.0's create_agent function.

    Args:
        project_path: Optional project path for MCP servers

    Returns:
        List of LangChain-compatible tools (empty list if MCP fails or disabled)

    Example:
        >>> tools = await get_mcp_tools()
        >>> agent = create_agent(model, tools=tools)
    """
    # Check if MCP is disabled via environment variable
    if os.getenv("DISABLE_MCP", "false").lower() == "true":
        print("⚠️  MCP disabled via DISABLE_MCP env var")
        print("   Using custom tools only...")
        return []

    try:
        client = await create_mcp_client(project_path)
        tools = await client.get_tools()
        print(f"📦 Loaded {len(tools)} tools from MCP servers")
        return tools
    except Exception as e:
        print(f"⚠️  MCP tools failed to load: {type(e).__name__}")
        print(f"   Continuing with custom tools only...")
        return []


__all__ = [
    "create_mcp_client",
    "get_mcp_tools",
]
