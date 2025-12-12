"""
Interactive CLI for Multi-Agent Builder

Usage:
    python cli_main.py

Launches a TUI with live feature board, logs, and token usage.
"""

import asyncio
import sys

# CRITICAL: Set Windows event loop policy BEFORE any other imports
# This fixes PostgreSQL psycopg async compatibility on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from pathlib import Path
from dotenv import load_dotenv
from src.cli.app import BuilderApp


def main():
    """Run the interactive CLI"""
    # Load environment variables from .env file
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)

    app = BuilderApp()
    app.run()


if __name__ == "__main__":
    main()
