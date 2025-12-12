"""
Workflow routers for conditional edges in LangGraph 1.0

These functions determine the next node to execute based on current state.

Compatible with:
- LangGraph 1.0.4
"""

from src.state.schemas import AppBuilderState
from typing import Literal


def route_after_init(state: AppBuilderState) -> Literal["gitops", "coding", "END"]:
    """
    Route after initialization

    Decision logic:
    - If recovery mode -> go to gitops (RECOVERY mode)
    - If resume mode -> go to coding (skip gitops, project in progress)
    - If complete mode -> END (project already done)
    - If feature list generated -> go to gitops (INIT mode)
    - Otherwise -> END

    Args:
        state: Current application state

    Returns:
        Next node name or END
    """
    feature_list = state.get("feature_list", [])
    gitops_mode = state.get("gitops_mode", "")
    recovery_features = state.get("recovery_features", [])

    # RECOVERY MODE: Handle interrupted operations from previous run
    if gitops_mode == "recovery" and recovery_features:
        print(f"\n{'='*60}")
        print(f"[SYNC] RECOVERY: Found {len(recovery_features)} features needing commit/push")
        print(f"-> Routing to GitOps (RECOVERY mode)")
        print(f"{'='*60}\n")
        return "gitops"

    # RESUME MODE: Project in progress, skip gitops and go to coding
    if gitops_mode == "resume":
        pending = [f for f in feature_list if f.get("status") == "pending"]
        testing = [f for f in feature_list if f.get("status") == "testing"]
        print(f"\n{'='*60}")
        print(f"[SYNC] RESUME: Project in progress")
        print(f"   Pending: {len(pending)}, Testing/Retry: {len(testing)}")
        print(f"-> Routing directly to Coding (skipping GitOps)")
        print(f"{'='*60}\n")
        return "coding"

    # COMPLETE MODE: Project already done
    if gitops_mode == "complete":
        done = [f for f in feature_list if f.get("status") == "done"]
        print(f"\n{'='*60}")
        print(f"[OK] Project already complete ({len(done)} features done)")
        print(f"-> Nothing to do, ending workflow")
        print(f"{'='*60}\n")
        return "END"

    if feature_list and len(feature_list) > 0:
        print(f"[OK] Initialization complete. {len(feature_list)} features to implement.")
        print(f"-> Routing to GitOps (INIT mode)")
        return "gitops"

    print("[WARN]  No features generated. Ending workflow.")
    return "END"


def route_after_gitops(state: AppBuilderState) -> Literal["coding", "END"]:
    """
    Route after GitOps operations

    Decision logic:
    - If gitops_mode was "init" -> go to coding (start implementing features)
    - If gitops_mode was "recovery" -> check for pending features, then coding or END
    - If gitops_mode was "feature" and pending features exist -> go to coding (next feature)
    - Otherwise -> END (all done)

    Args:
        state: Current application state

    Returns:
        Next node name or END
    """
    gitops_mode = state.get("gitops_mode", "feature")

    # SYNC: Read feature_list from disk to get latest status
    import os
    import json
    repo_path = state.get("repo_path", "")
    feature_list_path = os.path.join(repo_path, "feature_list.json")

    try:
        with open(feature_list_path, "r", encoding="utf-8") as f:
            feature_list = json.load(f)
        print(f"[SYNC] Synced feature_list from disk ({len(feature_list)} features)")
    except Exception as e:
        print(f"[WARN] Could not read feature_list from disk: {e}")
        feature_list = state.get("feature_list", [])

    if gitops_mode == "init":
        print(f"\n{'='*60}")
        print(f"[OK] ROUTING: gitops (INIT) -> coding")
        print(f"   Ready to start implementing features")
        print(f"{'='*60}\n")
        return "coding"

    # After recovery or feature commit, check if more work to do
    pending_features = [f for f in feature_list if f.get("status") == "pending"]
    testing_features = [f for f in feature_list if f.get("status") == "testing"]
    in_progress_features = [f for f in feature_list if f.get("status") == "in_progress"]
    
    # If there are incomplete features, continue to coding
    if testing_features or pending_features or in_progress_features:
        mode_desc = "RECOVERY" if gitops_mode == "recovery" else "FEATURE"
        print(f"\n{'='*60}")
        print(f"[OK] ROUTING: gitops ({mode_desc}) -> coding")
        print(f"   Remaining pending: {len(pending_features)}")
        print(f"   Needing retry: {len(testing_features)}")
        print(f"   In progress: {len(in_progress_features)}")
        print(f"{'='*60}\n")
        return "coding"

    # All features processed
    done = [f for f in feature_list if f.get("status") == "done"]
    failed = [f for f in feature_list if f.get("status") == "failed"]

    print(f"\n{'='*60}")
    print(f"[COMPLETE] WORKFLOW COMPLETE!")
    print(f"   Total features: {len(feature_list)}")
    print(f"   [OK] Done: {len(done)}")
    print(f"   [FAIL] Failed: {len(failed)}")
    if len(feature_list) > 0:
        print(f"   Success rate: {len(done) / len(feature_list) * 100:.1f}%")
    print(f"{'='*60}\n")
    return "END"


def route_after_coding(state: AppBuilderState) -> Literal["testing", "END"]:
    """
    Route after coding

    Decision logic:
    - If features in "testing" status -> route to testing
    - Otherwise -> END (indicates error or completion)

    NOTE: Coding agent MUST set feature to "testing" before completing.
    State is synced from feature_list.json by orchestrator wrapper.

    Args:
        state: Current application state

    Returns:
        Next node name or END
    """
    # SYNC: Read feature_list from disk to get latest status
    import os
    import json
    repo_path = state.get("repo_path", "")
    feature_list_path = os.path.join(repo_path, "feature_list.json")

    try:
        with open(feature_list_path, "r", encoding="utf-8") as f:
            feature_list = json.load(f)
        print(f"[SYNC] Synced feature_list from disk ({len(feature_list)} features)")
    except Exception as e:
        print(f"[WARN] Could not read feature_list from disk: {e}")
        feature_list = state.get("feature_list", [])

    # Check for features ready for testing
    testing_features = [f for f in feature_list if f.get("status") == "testing"]

    if testing_features:
        print(f"\n{'='*60}")
        print(f"[OK] ROUTING: coding -> testing")
        print(f"   Features ready for testing: {[f['id'] for f in testing_features]}")
        print(f"{'='*60}\n")
        return "testing"

    # No features in testing - check if all done
    pending = [f for f in feature_list if f.get("status") == "pending"]
    in_progress = [f for f in feature_list if f.get("status") == "in_progress"]
    done = [f for f in feature_list if f.get("status") == "done"]
    failed = [f for f in feature_list if f.get("status") == "failed"]

    print(f"\n{'='*60}")
    print(f"[WARN]  ROUTING: coding -> END")
    print(f"   Status Summary:")
    print(f"   - Pending: {len(pending)}")
    print(f"   - In Progress: {len(in_progress)}")
    print(f"   - Testing: 0")
    print(f"   - Done: {len(done)}")
    print(f"   - Failed: {len(failed)}")

    if pending or in_progress:
        print(f"   [WARN]  WARNING: Pending/in-progress features exist but none in testing!")
        print(f"   This indicates coding agent didn't properly update feature status.")

    print(f"{'='*60}\n")
    return "END"


def route_after_testing(state: AppBuilderState) -> Literal["qa_doc", "coding"]:
    """
    Route after testing - implements retry logic

    Decision logic:
    - If tests passed -> go to qa_doc
    - If tests failed and attempts < 3 -> retry coding
    - If tests failed and attempts >= 3 -> mark as failed, go to coding (next feature)

    Args:
        state: Current application state

    Returns:
        Next node name (qa_doc or coding)
    """
    import os
    import json

    test_context = state.get("test_context", {})
    test_result = test_context.get("last_result")
    current_feature = state.get("current_feature")
    repo_path = state.get("repo_path", "")

    if not current_feature:
        print("[WARN]  No current feature in testing phase")
        return "coding"

    feature_id = current_feature.get("id", "unknown")

    # SYNC: Read feature_list from disk to get latest status for current feature
    feature_list_path = os.path.join(repo_path, "feature_list.json")
    try:
        with open(feature_list_path, "r", encoding="utf-8") as f:
            feature_list = json.load(f)
        # Find current feature in synced list
        for feature in feature_list:
            if feature.get("id") == feature_id:
                current_feature = feature
                print(f"[SYNC] Synced current feature {feature_id} from disk (status={feature.get('status')})")
                break
    except Exception as e:
        print(f"[WARN] Could not sync feature from disk: {e}, using state data")
    
    # If feature is marked as "done", tests passed - go to QA
    if current_feature.get("status") == "done":
        print(f"[OK] Feature {feature_id} marked as done. Moving to QA.")
        return "qa_doc"

    # Check test_result if available
    if test_result and test_result.get("passed"):
        print(f"[OK] Tests passed for {feature_id}. Moving to QA.")
        return "qa_doc"

    # If test_result is None or tests failed - check status and retry count
    # If feature is still in "testing" status, it means tests haven't passed yet
    if current_feature.get("status") == "testing":
        attempts = current_feature.get("attempts", 0)

        if attempts >= 3:
            # Max retries reached - persist status to disk
            print(f"[FAIL] Feature {feature_id} failed after {attempts} attempts. Marking as failed.")
            _persist_feature_update(repo_path, feature_id, "failed", attempts)
            return "coding"

        # Retry - increment attempts and persist to disk
        new_attempts = attempts + 1
        print(f"[WARN]  Tests failed for {feature_id}. Retry attempt {new_attempts}/3.")
        _persist_feature_update(repo_path, feature_id, "testing", new_attempts)
        return "coding"
    
    # Default: move to coding to select next feature
    print(f"[WARN]  Unexpected state for {feature_id}. Moving to coding.")
    return "coding"


def _persist_feature_update(repo_path: str, feature_id: str, status: str, attempts: int) -> None:
    """
    Helper to persist feature status and attempts to feature_list.json
    """
    import os
    import json
    
    feature_list_path = os.path.join(repo_path, "feature_list.json")
    
    if not os.path.exists(feature_list_path):
        print(f"[WARN]  Cannot persist: {feature_list_path} not found")
        return
    
    try:
        with open(feature_list_path, "r", encoding="utf-8") as f:
            features = json.load(f)
        
        for feature in features:
            if feature.get("id") == feature_id:
                feature["status"] = status
                feature["attempts"] = attempts
                print(f"   [persist] {feature_id}: status={status}, attempts={attempts}")
                break
        
        with open(feature_list_path, "w", encoding="utf-8") as f:
            json.dump(features, f, indent=2)
            
    except Exception as e:
        print(f"[WARN]  Error persisting feature update: {e}")


def route_after_qa(state: AppBuilderState) -> Literal["gitops", "END"]:
    """
    Route after QA - go to GitOps for commit/push

    Decision logic:
    - Always go to gitops (FEATURE mode) to commit and push changes
    - GitOps will then decide if more features remain or END

    Args:
        state: Current application state

    Returns:
        Next node name
    """
    print(f"\n{'='*60}")
    print(f"[OK] ROUTING: qa_doc -> gitops (FEATURE mode)")
    print(f"   Will commit and push feature changes")
    print(f"{'='*60}\n")
    return "gitops"


def validate_feature_list_sync(state: AppBuilderState) -> dict:
    """
    Validate that state's feature_list matches disk file

    Used for debugging state synchronization issues.

    Args:
        state: Current application state

    Returns:
        dict with validation results

    Example:
        >>> result = validate_feature_list_sync(state)
        >>> if not result["synced"]:
        >>>     print(f"Sync issue: {result['reason']}")
    """
    import os
    import json

    repo_path = state.get("repo_path", "")
    feature_list_path = os.path.join(repo_path, "feature_list.json")

    if not os.path.exists(feature_list_path):
        return {
            "synced": False,
            "reason": "feature_list.json not found on disk"
        }

    try:
        with open(feature_list_path, "r", encoding="utf-8") as f:
            disk_features = json.load(f)

        state_features = state.get("feature_list", [])

        # Compare counts
        if len(disk_features) != len(state_features):
            return {
                "synced": False,
                "reason": f"Count mismatch: disk={len(disk_features)}, state={len(state_features)}"
            }

        # Compare statuses
        for i, (disk_f, state_f) in enumerate(zip(disk_features, state_features)):
            if disk_f.get("status") != state_f.get("status"):
                return {
                    "synced": False,
                    "reason": f"Status mismatch for {disk_f['id']}: disk={disk_f['status']}, state={state_f['status']}"
                }

        return {"synced": True, "reason": "State and disk are in sync"}

    except Exception as e:
        return {"synced": False, "reason": f"Error: {e}"}


__all__ = [
    "route_after_init",
    "route_after_gitops",
    "route_after_coding",
    "route_after_testing",
    "route_after_qa",
    "validate_feature_list_sync",
]
