"""
Path utilities for resolving project-relative paths

This module provides utilities to resolve paths relative to the project root,
ensuring the application works correctly regardless of where it's executed from.
"""

from pathlib import Path


# Project root is the backend directory (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent.parent


def get_prompt_path(prompt_name: str) -> Path:
    """
    Get absolute path to a prompt file

    Args:
        prompt_name: Name of the prompt file (e.g., "gitops.txt")

    Returns:
        Absolute path to the prompt file

    Examples:
        >>> get_prompt_path("gitops.txt")
        Path('/path/to/backend/config/prompts/gitops.txt')
    """
    return PROJECT_ROOT / "config" / "prompts" / prompt_name


def get_config_path(config_name: str) -> Path:
    """
    Get absolute path to a config file

    Args:
        config_name: Name of the config file

    Returns:
        Absolute path to the config file

    Examples:
        >>> get_config_path("settings.json")
        Path('/path/to/backend/config/settings.json')
    """
    return PROJECT_ROOT / "config" / config_name
