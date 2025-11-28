"""
Filesystem tools for file and directory operations

These tools replace MCP filesystem server for Windows compatibility
and direct control over file operations.
"""

from langchain_core.tools import tool
from langchain.tools import ToolRuntime
import os
import json
from pathlib import Path
from typing import Optional, List


def resolve_path(path: str, repo_path: str) -> str:
    """
    Resolve a path relative to repo_path, avoiding double nesting

    Args:
        path: Path to resolve (can be absolute, relative, or already containing repo_path)
        repo_path: Base repository path

    Returns:
        Resolved absolute path

    Example:
        >>> resolve_path("src/main.py", "./output/api-test")
        "./output/api-test/src/main.py"

        >>> resolve_path("./output/api-test/src/main.py", "./output/api-test")
        "./output/api-test/src/main.py"  # NOT ./output/api-test/output/api-test/src/main.py
    """
    # Normalize paths for comparison
    normalized_repo = os.path.normpath(repo_path)
    normalized_path = os.path.normpath(path)

    # Check if path already contains repo_path (avoid double nesting)
    if normalized_path.startswith(normalized_repo):
        # Path already includes repo_path
        return normalized_path
    elif not os.path.isabs(path):
        # Relative path - join with repo_path
        return os.path.join(repo_path, path)
    else:
        # Absolute path - use as is
        return path


@tool
def create_directory(path: str, runtime: ToolRuntime) -> str:
    """
    Create a directory and all parent directories if needed

    Args:
        path: Absolute or relative path to directory
        runtime: Tool runtime for state access

    Returns:
        Success message with created path

    Example:
        >>> create_directory("src/components")
        "Created directory: src/components"
    """
    repo_path = runtime.state.get("repo_path", "")
    full_path = resolve_path(path, repo_path)

    try:
        os.makedirs(full_path, exist_ok=True)
        return f"Created directory: {full_path}"
    except Exception as e:
        return f"Error creating directory {full_path}: {e}"


@tool
def write_file(
    path: str,
    content: str,
    runtime: ToolRuntime,
    create_dirs: bool = True
) -> str:
    """
    Write content to a file, creating parent directories if needed

    Args:
        path: File path (absolute or relative)
        content: File content
        runtime: Tool runtime for state access
        create_dirs: Create parent directories if they don't exist

    Returns:
        Success message

    Example:
        >>> write_file("main.py", "print('hello')")
        "Wrote 13 bytes to main.py"
    """
    repo_path = runtime.state.get("repo_path", "")
    full_path = resolve_path(path, repo_path)

    try:
        # Create parent directories if needed
        if create_dirs:
            parent_dir = os.path.dirname(full_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

        # Write file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        size = len(content.encode('utf-8'))
        return f"Wrote {size} bytes to {full_path}"
    except Exception as e:
        return f"Error writing file {full_path}: {e}"


@tool
def read_file(path: str, runtime: ToolRuntime) -> str:
    """
    Read content from a file

    Args:
        path: File path (absolute or relative)
        runtime: Tool runtime for state access

    Returns:
        File content or error message

    Example:
        >>> read_file("README.md")
        "# My Project\\n..."
    """
    repo_path = runtime.state.get("repo_path", "")
    full_path = resolve_path(path, repo_path)

    try:
        if not os.path.exists(full_path):
            return f"File not found: {full_path}"

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        return content
    except Exception as e:
        return f"Error reading file {full_path}: {e}"


@tool
def list_directory(path: str, runtime: ToolRuntime, recursive: bool = False) -> str:
    """
    List files and directories in a path

    Args:
        path: Directory path (absolute or relative)
        runtime: Tool runtime for state access
        recursive: List recursively (default: False)

    Returns:
        JSON string with directory listing

    Example:
        >>> list_directory(".")
        '["file1.py", "dir1/", "file2.txt"]'
    """
    repo_path = runtime.state.get("repo_path", "")
    full_path = resolve_path(path, repo_path)

    try:
        if not os.path.exists(full_path):
            return f"Directory not found: {full_path}"

        if not os.path.isdir(full_path):
            return f"Not a directory: {full_path}"

        if recursive:
            # Recursive listing
            items = []
            for root, dirs, files in os.walk(full_path):
                rel_root = os.path.relpath(root, full_path)
                if rel_root == ".":
                    rel_root = ""

                for d in dirs:
                    item_path = os.path.join(rel_root, d) if rel_root else d
                    items.append(item_path + "/")

                for f in files:
                    item_path = os.path.join(rel_root, f) if rel_root else f
                    items.append(item_path)
            return json.dumps(sorted(items), indent=2)
        else:
            # Non-recursive listing
            items = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                if os.path.isdir(item_path):
                    items.append(item + "/")
                else:
                    items.append(item)
            return json.dumps(sorted(items), indent=2)

    except Exception as e:
        return f"Error listing directory {full_path}: {e}"


@tool
def file_exists(path: str, runtime: ToolRuntime) -> str:
    """
    Check if a file or directory exists

    Args:
        path: Path to check (absolute or relative)
        runtime: Tool runtime for state access

    Returns:
        JSON with exists flag and type (file/directory)

    Example:
        >>> file_exists("README.md")
        '{"exists": true, "type": "file"}'
    """
    repo_path = runtime.state.get("repo_path", "")
    full_path = resolve_path(path, repo_path)

    result = {
        "exists": os.path.exists(full_path),
        "type": None
    }

    if result["exists"]:
        if os.path.isfile(full_path):
            result["type"] = "file"
        elif os.path.isdir(full_path):
            result["type"] = "directory"

    return json.dumps(result)


@tool
def delete_file(path: str, runtime: ToolRuntime) -> str:
    """
    Delete a file

    Args:
        path: File path (absolute or relative)
        runtime: Tool runtime for state access

    Returns:
        Success message

    Example:
        >>> delete_file("temp.txt")
        "Deleted file: temp.txt"
    """
    repo_path = runtime.state.get("repo_path", "")
    full_path = resolve_path(path, repo_path)

    try:
        if not os.path.exists(full_path):
            return f"File not found: {full_path}"

        if os.path.isdir(full_path):
            return f"Cannot delete directory with delete_file: {full_path}"

        os.remove(full_path)
        return f"Deleted file: {full_path}"
    except Exception as e:
        return f"Error deleting file {full_path}: {e}"


@tool
def get_file_info(path: str, runtime: ToolRuntime) -> str:
    """
    Get information about a file or directory

    Args:
        path: Path to inspect (absolute or relative)
        runtime: Tool runtime for state access

    Returns:
        JSON with file information

    Example:
        >>> get_file_info("README.md")
        '{"size": 1234, "modified": "2025-11-27T...", "type": "file"}'
    """
    repo_path = runtime.state.get("repo_path", "")
    full_path = resolve_path(path, repo_path)

    try:
        if not os.path.exists(full_path):
            return json.dumps({"error": f"Path not found: {full_path}"})

        stat = os.stat(full_path)
        info = {
            "path": full_path,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "type": "directory" if os.path.isdir(full_path) else "file",
            "readable": os.access(full_path, os.R_OK),
            "writable": os.access(full_path, os.W_OK)
        }

        return json.dumps(info, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error getting file info: {e}"})


__all__ = [
    "create_directory",
    "write_file",
    "read_file",
    "list_directory",
    "file_exists",
    "delete_file",
    "get_file_info",
]
