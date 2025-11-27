"""
Utility to inspect checkpoints in PostgreSQL

Usage:
    python scripts/inspect_checkpoints.py list
    python scripts/inspect_checkpoints.py state <thread_id>
"""

import asyncio
import asyncpg
import os
import sys
from dotenv import load_dotenv

load_dotenv(".env.development")


async def list_threads():
    """List all checkpoint threads"""
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))

    query = """
        SELECT DISTINCT
            config->>'thread_id' as thread_id,
            COUNT(*) as checkpoint_count,
            MAX(checkpoint_id) as latest_checkpoint,
            MAX(checkpoint->'ts') as last_updated
        FROM checkpoints
        GROUP BY config->>'thread_id'
        ORDER BY last_updated DESC
    """

    rows = await conn.fetch(query)

    print("\n📊 Checkpoint Threads:")
    print("=" * 80)

    if not rows:
        print("No checkpoints found.")
    else:
        for row in rows:
            print(f"Thread: {row['thread_id']}")
            print(f"  Checkpoints: {row['checkpoint_count']}")
            print(f"  Latest ID: {row['latest_checkpoint']}")
            print(f"  Last Updated: {row['last_updated']}")
            print()

    await conn.close()


async def get_thread_state(thread_id: str):
    """Get latest state for a thread"""
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))

    query = """
        SELECT checkpoint
        FROM checkpoints
        WHERE config->>'thread_id' = $1
        ORDER BY checkpoint_id DESC
        LIMIT 1
    """

    row = await conn.fetchrow(query, thread_id)

    if row:
        print(f"\n📝 Latest state for '{thread_id}':")
        print("=" * 80)
        import json
        print(json.dumps(row['checkpoint'], indent=2))
    else:
        print(f"No checkpoints found for thread '{thread_id}'")

    await conn.close()


async def delete_thread(thread_id: str):
    """Delete all checkpoints for a thread"""
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))

    query = """
        DELETE FROM checkpoints
        WHERE config->>'thread_id' = $1
    """

    result = await conn.execute(query, thread_id)

    print(f"✅ Deleted checkpoints for thread '{thread_id}': {result}")

    await conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/inspect_checkpoints.py list")
        print("  python scripts/inspect_checkpoints.py state <thread_id>")
        print("  python scripts/inspect_checkpoints.py delete <thread_id>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        asyncio.run(list_threads())
    elif command == "state" and len(sys.argv) == 3:
        asyncio.run(get_thread_state(sys.argv[2]))
    elif command == "delete" and len(sys.argv) == 3:
        asyncio.run(delete_thread(sys.argv[2]))
    else:
        print("Invalid command")
        sys.exit(1)
