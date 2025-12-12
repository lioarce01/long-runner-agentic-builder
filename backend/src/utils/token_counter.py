"""
Token Counter - Phase 4.4
Tracks token usage across agents and features for optimization decisions
"""

import json
import os
from datetime import datetime
from typing import List


def count_tokens(text: str) -> int:
    """
    Count tokens using tiktoken (cl100k_base for GPT-4/Claude).
    Falls back to estimation if tiktoken not available.

    Args:
        text: Text to count tokens for

    Returns:
        Approximate token count
    """
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except ImportError:
        # Fallback: rough estimation (1 token ≈ 4 characters)
        return len(text) // 4
    except Exception:
        # Fallback for any other error
        return len(text) // 4


def count_messages_tokens(messages: List) -> int:
    """
    Count total tokens in a list of messages.

    Args:
        messages: List of LangChain messages

    Returns:
        Total token count
    """
    total = 0
    for msg in messages:
        if hasattr(msg, 'content'):
            content = str(msg.content)
            total += count_tokens(content)
    return total


def log_token_usage(
    agent_name: str,
    feature_id: str,
    token_count: int,
    repo_path: str,
    message_count: int = 0
):
    """
    Log token usage to token_usage.json for analysis.

    Args:
        agent_name: Name of the agent (coding, testing, qa_doc, gitops)
        feature_id: ID of current feature (or "init", "recovery")
        token_count: Number of tokens in conversation
        repo_path: Path to project repository
        message_count: Number of messages in conversation
    """
    log_file = os.path.join(repo_path, "token_usage.json")

    # Load existing logs
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    else:
        logs = []

    # Append new log entry
    logs.append({
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "feature_id": feature_id,
        "token_count": token_count,
        "message_count": message_count
    })

    # Save updated logs
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"⚠️  Failed to write token_usage.json: {e}")

    # Print summary
    print(f"📊 TOKEN USAGE [{agent_name}] {feature_id}: {token_count:,} tokens ({message_count} messages)")


def get_token_stats(repo_path: str) -> dict:
    """
    Get token usage statistics for the project.

    Args:
        repo_path: Path to project repository

    Returns:
        Dictionary with token statistics
    """
    log_file = os.path.join(repo_path, "token_usage.json")

    if not os.path.exists(log_file):
        return {
            "total_tokens": 0,
            "by_agent": {},
            "by_feature": {},
            "entries": 0
        }

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            logs = json.load(f)
    except Exception:
        return {"total_tokens": 0, "by_agent": {}, "by_feature": {}, "entries": 0}

    total_tokens = 0
    by_agent = {}
    by_feature = {}

    for entry in logs:
        tokens = entry.get("token_count", 0)
        agent = entry.get("agent", "unknown")
        feature = entry.get("feature_id", "unknown")

        total_tokens += tokens

        if agent not in by_agent:
            by_agent[agent] = 0
        by_agent[agent] += tokens

        if feature not in by_feature:
            by_feature[feature] = 0
        by_feature[feature] += tokens

    return {
        "total_tokens": total_tokens,
        "by_agent": by_agent,
        "by_feature": by_feature,
        "entries": len(logs)
    }
