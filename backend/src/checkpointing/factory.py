"""
Checkpointer factory for PostgreSQL-based persistence

Compatible with:
- LangGraph 1.0.4 (Nov 25, 2025)
- langgraph-checkpoint-postgres 3.0.1

This module provides a singleton factory for creating and managing
AsyncPostgresSaver instances for durable state persistence.
"""

import os
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from typing import Optional
from contextlib import asynccontextmanager


class CheckpointerFactory:
    """
    Singleton factory for PostgreSQL checkpointer

    Manages connection pooling and checkpointer lifecycle for
    LangGraph 1.0 durable execution.
    """

    _instance: Optional[AsyncPostgresSaver] = None
    _pool: Optional[AsyncConnectionPool] = None

    @classmethod
    async def get_checkpointer(cls, force_new: bool = False) -> AsyncPostgresSaver:
        """
        Get or create checkpointer instance

        Args:
            force_new: Force creation of new instance

        Returns:
            AsyncPostgresSaver instance

        Raises:
            ValueError: If DATABASE_URL not set
        """
        if cls._instance is None or force_new:
            await cls._initialize()

        return cls._instance  # type: ignore

    @classmethod
    async def _initialize(cls) -> None:
        """Initialize checkpointer with connection pool"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError(
                "DATABASE_URL environment variable must be set. "
                "Format: postgresql://user:pass@host:port/dbname"
            )

        print(f"📦 Connecting to PostgreSQL...")

        # Create connection pool with psycopg (required by LangGraph)
        # Use configure to set autocommit for CREATE INDEX CONCURRENTLY
        from psycopg import AsyncConnection

        async def configure_conn(conn: AsyncConnection):
            await conn.set_autocommit(True)

        cls._pool = AsyncConnectionPool(
            conninfo=database_url,
            min_size=2,
            max_size=10,
            timeout=60,
            configure=configure_conn,
            open=False  # Don't open in constructor (avoid deprecation warning)
        )

        # Open the pool explicitly
        await cls._pool.open()

        # Create checkpointer (LangGraph 1.0 pattern)
        cls._instance = AsyncPostgresSaver(cls._pool)

        # Setup tables (idempotent operation)
        await cls._instance.setup()

        print(f"✅ Checkpointer initialized with connection pool")

    @classmethod
    async def close(cls) -> None:
        """Close connection pool gracefully"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            cls._instance = None
            print("✅ Checkpointer connection pool closed")

    @classmethod
    def get_thread_id(
        cls,
        project_name: str,
        feature_id: Optional[str] = None
    ) -> str:
        """
        Generate thread ID for checkpointing

        Thread IDs are scoped per project and optionally per feature
        for granular state management in LangGraph 1.0.

        Args:
            project_name: Name of the project being built
            feature_id: Optional feature ID for feature-scoped threads

        Returns:
            Thread ID string

        Examples:
            >>> get_thread_id("chatbot-clone")
            "chatbot-clone::project"
            >>> get_thread_id("chatbot-clone", "f-001")
            "chatbot-clone::f-001"
        """
        if feature_id:
            return f"{project_name}::{feature_id}"
        return f"{project_name}::project"


# Convenience functions
async def get_checkpointer() -> AsyncPostgresSaver:
    """
    Get the checkpointer instance

    Returns:
        AsyncPostgresSaver for LangGraph 1.0

    Example:
        >>> checkpointer = await get_checkpointer()
        >>> app = workflow.compile(checkpointer=checkpointer)
    """
    return await CheckpointerFactory.get_checkpointer()


@asynccontextmanager
async def checkpointer_context():
    """
    Context manager for checkpointer lifecycle

    Ensures proper cleanup of PostgreSQL connections.

    Example:
        >>> async with checkpointer_context() as checkpointer:
        ...     app = workflow.compile(checkpointer=checkpointer)
        ...     result = await app.ainvoke(state, config)
    """
    try:
        checkpointer = await get_checkpointer()
        yield checkpointer
    finally:
        await CheckpointerFactory.close()


__all__ = [
    "CheckpointerFactory",
    "get_checkpointer",
    "checkpointer_context",
]
