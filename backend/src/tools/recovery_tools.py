"""
Recovery tools for handling interrupted operations

When the workflow crashes or is interrupted, pending operations are tracked
in pending_ops.json. On restart, these operations are processed first.

This ensures:
- Features marked "done" get their commits/pushes
- No work is lost due to connection errors
- Consistent state between local and remote
"""

import os
import json
from typing import List, Dict, Any
from datetime import datetime
import subprocess


def get_pending_ops_path(repo_path: str) -> str:
    """Get path to pending_ops.json file"""
    return os.path.join(repo_path, "pending_ops.json")


def load_pending_ops(repo_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load pending operations from disk
    
    Returns:
        Dict with pending operations by type:
        {
            "commits": [{"feature_id": "f-001", "timestamp": "..."}],
            "pushes": [{"feature_id": "f-001", "timestamp": "..."}],
            "docs": [{"feature_id": "f-001", "timestamp": "..."}]
        }
    """
    path = get_pending_ops_path(repo_path)
    
    default = {
        "commits": [],
        "pushes": [],
        "docs": []
    }
    
    if not os.path.exists(path):
        return default
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all keys exist
            for key in default:
                if key not in data:
                    data[key] = []
            return data
    except Exception as e:
        print(f"[WARN]  Failed to load pending_ops.json: {e}")
        return default


def save_pending_ops(repo_path: str, ops: Dict[str, List[Dict[str, Any]]]) -> None:
    """Save pending operations to disk"""
    path = get_pending_ops_path(repo_path)
    
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ops, f, indent=2, default=str)
        
        # Ensure pending_ops.json is in .gitignore (we don't want to commit this)
        _ensure_gitignore_entry(repo_path, "pending_ops.json")
        
    except Exception as e:
        print(f"[WARN]  Failed to save pending_ops.json: {e}")


# Mapping from singular to plural for operation types
_OP_TYPE_PLURAL = {
    "commit": "commits",
    "push": "pushes",
    "doc": "docs",
    # Also accept plural forms directly
    "commits": "commits",
    "pushes": "pushes",
    "docs": "docs",
}


def _normalize_op_type(op_type: str) -> str:
    """Convert operation type to its plural form (the key used in pending_ops.json)"""
    return _OP_TYPE_PLURAL.get(op_type, op_type + "s")


def _ensure_gitignore_entry(repo_path: str, entry: str) -> None:
    """Add an entry to .gitignore if not already present"""
    gitignore_path = os.path.join(repo_path, ".gitignore")
    
    try:
        # Read existing content
        existing = ""
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r", encoding="utf-8") as f:
                existing = f.read()
        
        # Check if entry already exists
        entries = [line.strip() for line in existing.splitlines()]
        if entry not in entries:
            # Add entry
            with open(gitignore_path, "a", encoding="utf-8") as f:
                if existing and not existing.endswith("\n"):
                    f.write("\n")
                f.write(f"{entry}\n")
    except Exception:
        pass  # Silent fail - not critical


def mark_pending(repo_path: str, op_type: str, feature_id: str) -> None:
    """
    Mark an operation as pending (about to execute)
    
    Call this BEFORE executing the operation.
    If the operation crashes, this will be used for recovery.
    
    Args:
        repo_path: Path to repository
        op_type: Type of operation ("commit", "push", "doc")
        feature_id: Feature ID this operation is for
    """
    ops = load_pending_ops(repo_path)
    op_key = _normalize_op_type(op_type)
    
    # Check if already pending
    existing = [o for o in ops[op_key] if o.get("feature_id") == feature_id]
    if existing:
        return  # Already pending
    
    ops[op_key].append({
        "feature_id": feature_id,
        "timestamp": datetime.now().isoformat()
    })
    
    save_pending_ops(repo_path, ops)
    print(f"[LOG] Marked pending: {op_type} for {feature_id}")


def clear_pending(repo_path: str, op_type: str, feature_id: str) -> None:
    """
    Clear a pending operation (successfully completed)
    
    Call this AFTER the operation succeeds.
    
    Args:
        repo_path: Path to repository
        op_type: Type of operation ("commit", "push", "doc")
        feature_id: Feature ID this operation was for
    """
    ops = load_pending_ops(repo_path)
    op_key = _normalize_op_type(op_type)
    
    # Remove this feature from pending
    ops[op_key] = [o for o in ops[op_key] if o.get("feature_id") != feature_id]
    
    save_pending_ops(repo_path, ops)
    print(f"[OK] Cleared pending: {op_type} for {feature_id}")


def clear_all_pending(repo_path: str, feature_id: str) -> None:
    """Clear all pending operations for a feature"""
    ops = load_pending_ops(repo_path)
    
    for op_key in ["commits", "pushes", "docs"]:
        ops[op_key] = [o for o in ops[op_key] if o.get("feature_id") != feature_id]
    
    save_pending_ops(repo_path, ops)
    print(f"[OK] Cleared all pending ops for {feature_id}")


def get_committed_features(repo_path: str) -> List[str]:
    """
    Get list of feature IDs that have commits in git history
    
    Searches git log for commits with pattern 'feat(f-XXX)'
    
    Returns:
        List of feature IDs that have been committed
    """
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--all"],
            cwd=repo_path,
            capture_output=True,
            encoding="utf-8",
            errors="replace"
        )
        
        if result.returncode != 0:
            return []
        
        # Parse commit messages for feature IDs
        committed = []
        for line in result.stdout.splitlines():
            # Look for feat(f-XXX) pattern
            if "feat(f-" in line:
                # Extract feature ID: find "feat(" then extract until ")"
                feat_start = line.find("feat(")
                if feat_start == -1:
                    continue
                    
                # Start after "feat(" (5 chars)
                id_start = feat_start + 5
                # Find closing parenthesis
                id_end = line.find(")", id_start)
                
                if id_end > id_start:
                    feature_id = line[id_start:id_end]  # e.g., "f-001"
                    if feature_id.startswith("f-"):  # Validate it's a feature ID
                        committed.append(feature_id)
        
        return list(set(committed))  # Unique IDs
        
    except Exception as e:
        print(f"[WARN]  Failed to get git history: {e}")
        return []


def check_recovery_needed(repo_path: str, feature_list: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Check if any features need recovery (done but not committed/pushed)
    
    Compares feature_list.json (local state) with git history (committed state)
    
    Args:
        repo_path: Path to repository
        feature_list: List of features from feature_list.json
        
    Returns:
        Dict with features needing recovery:
        {
            "needs_commit": ["f-003", "f-004"],
            "needs_push": ["f-003"]
        }
    """
    # Get features already committed
    committed_features = get_committed_features(repo_path)
    
    # Get features marked as done locally
    done_features = [f["id"] for f in feature_list if f.get("status") == "done"]
    
    # Find features that are done but not committed
    needs_commit = [fid for fid in done_features if fid not in committed_features]
    
    # Also check pending_ops.json for explicit pending ops
    pending_ops = load_pending_ops(repo_path)
    pending_commits = [o["feature_id"] for o in pending_ops.get("commits", [])]
    pending_pushes = [o["feature_id"] for o in pending_ops.get("pushes", [])]
    
    # Merge explicit pending with detected missing
    needs_commit = list(set(needs_commit + pending_commits))
    needs_push = list(set(pending_pushes))
    
    result = {
        "needs_commit": needs_commit,
        "needs_push": needs_push
    }
    
    if needs_commit or needs_push:
        print(f"\n{'='*60}")
        print(f"[SYNC] RECOVERY CHECK: Found pending operations")
        print(f"   Features needing commit: {needs_commit}")
        print(f"   Features needing push: {needs_push}")
        print(f"{'='*60}\n")
    
    return result


def get_recovery_features(repo_path: str, feature_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Get list of features that need recovery operations
    
    Returns feature objects (not just IDs) for features needing commit/push
    Also cleans up orphaned entries in pending_ops.json
    """
    recovery = check_recovery_needed(repo_path, feature_list)
    
    feature_ids_needing_recovery = set(recovery["needs_commit"] + recovery["needs_push"])
    
    # Get valid feature IDs from feature_list
    valid_feature_ids = {f["id"] for f in feature_list}
    
    # Clean up orphaned pending ops (features that no longer exist)
    orphaned_ids = feature_ids_needing_recovery - valid_feature_ids
    if orphaned_ids:
        print(f"[WARN]  Cleaning up orphaned pending ops: {orphaned_ids}")
        for orphan_id in orphaned_ids:
            clear_all_pending(repo_path, orphan_id)
    
    # Return only features that exist in feature_list
    return [f for f in feature_list if f["id"] in feature_ids_needing_recovery]


__all__ = [
    "load_pending_ops",
    "save_pending_ops",
    "mark_pending",
    "clear_pending",
    "clear_all_pending",
    "get_committed_features",
    "check_recovery_needed",
    "get_recovery_features"
]

