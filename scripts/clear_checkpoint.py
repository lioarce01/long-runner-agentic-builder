"""
Clear LangGraph checkpoint for a specific project thread

Usage:
    python scripts/clear_checkpoint.py <project_name>

Example:
    python scripts/clear_checkpoint.py fastapi-test
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from dotenv import load_dotenv
from psycopg_pool import AsyncConnectionPool

# Load environment
env_file = PROJECT_ROOT / "backend" / ".env"
load_dotenv(env_file)


async def clear_checkpoint(project_name: str):
    """Clear all checkpoint data for a specific project thread"""

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set in .env")
        return

    thread_id = f"{project_name}::project"

    print(f"🗑️  Clearing checkpoint for thread: {thread_id}")

    # Create connection pool
    pool = AsyncConnectionPool(
        conninfo=database_url,
        min_size=1,
        max_size=2,
        open=False
    )

    try:
        await pool.open()

        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                # Delete from checkpoints table
                await cur.execute(
                    "DELETE FROM checkpoints WHERE thread_id = %s",
                    (thread_id,)
                )
                checkpoints_deleted = cur.rowcount

                # Delete from checkpoint_writes table
                await cur.execute(
                    "DELETE FROM checkpoint_writes WHERE thread_id = %s",
                    (thread_id,)
                )
                writes_deleted = cur.rowcount

                await conn.commit()

                print(f"✅ Deleted {checkpoints_deleted} checkpoint(s)")
                print(f"✅ Deleted {writes_deleted} checkpoint write(s)")
                print(f"✅ Thread '{thread_id}' cleared successfully")

    except Exception as e:
        print(f"❌ Error clearing checkpoint: {e}")

    finally:
        await pool.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/clear_checkpoint.py <project_name>")
        print("Example: python scripts/clear_checkpoint.py fastapi-test")
        sys.exit(1)

    project_name = sys.argv[1]

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(clear_checkpoint(project_name))
