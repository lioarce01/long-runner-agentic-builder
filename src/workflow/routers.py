"""
Workflow routers for conditional edges in LangGraph 1.0

These functions determine the next node to execute based on current state.

Compatible with:
- LangGraph 1.0.4
"""

from src.state.schemas import AppBuilderState
from typing import Literal


def route_after_init(state: AppBuilderState) -> Literal["coding", "END"]:
    """
    Route after initialization

    Decision logic:
    - If feature list generated → go to coding
    - Otherwise → END

    Args:
        state: Current application state

    Returns:
        Next node name or END
    """
    feature_list = state.get("feature_list", [])

    if feature_list and len(feature_list) > 0:
        print(f"✅ Initialization complete. {len(feature_list)} features to implement.")
        return "coding"

    print("⚠️  No features generated. Ending workflow.")
    return "END"


def route_after_coding(state: AppBuilderState) -> Literal["testing", "END"]:
    """
    Route after coding

    Decision logic:
    - If features in "testing" status → route to testing
    - Otherwise → END (indicates error or completion)

    NOTE: Coding agent MUST set feature to "testing" before completing.
    State is synced from feature_list.json by orchestrator wrapper.

    Args:
        state: Current application state

    Returns:
        Next node name or END
    """
    feature_list = state.get("feature_list", [])

    # Check for features ready for testing
    testing_features = [f for f in feature_list if f.get("status") == "testing"]

    if testing_features:
        print(f"\n{'='*60}")
        print(f"✅ ROUTING: coding → testing")
        print(f"   Features ready for testing: {[f['id'] for f in testing_features]}")
        print(f"{'='*60}\n")
        return "testing"

    # No features in testing - check if all done
    pending = [f for f in feature_list if f.get("status") == "pending"]
    in_progress = [f for f in feature_list if f.get("status") == "in_progress"]
    done = [f for f in feature_list if f.get("status") == "done"]
    failed = [f for f in feature_list if f.get("status") == "failed"]

    print(f"\n{'='*60}")
    print(f"⚠️  ROUTING: coding → END")
    print(f"   Status Summary:")
    print(f"   - Pending: {len(pending)}")
    print(f"   - In Progress: {len(in_progress)}")
    print(f"   - Testing: 0")
    print(f"   - Done: {len(done)}")
    print(f"   - Failed: {len(failed)}")

    if pending or in_progress:
        print(f"   ⚠️  WARNING: Pending/in-progress features exist but none in testing!")
        print(f"   This indicates coding agent didn't properly update feature status.")

    print(f"{'='*60}\n")
    return "END"


def route_after_testing(state: AppBuilderState) -> Literal["qa_doc", "coding"]:
    """
    Route after testing - implements retry logic

    Decision logic:
    - If tests passed → go to qa_doc
    - If tests failed and attempts < 3 → retry coding
    - If tests failed and attempts >= 3 → mark as failed, go to coding (next feature)

    Args:
        state: Current application state

    Returns:
        Next node name (qa_doc or coding)
    """
    test_context = state.get("test_context", {})
    test_result = test_context.get("last_result", {})
    current_feature = state.get("current_feature")

    if not current_feature:
        print("⚠️  No current feature in testing phase")
        return "coding"

    if test_result.get("passed"):
        print(f"✅ Tests passed for {current_feature['id']}. Moving to QA.")
        return "qa_doc"

    # Tests failed - check retry count
    attempts = current_feature.get("attempts", 0)

    if attempts >= 3:
        # Max retries reached
        print(f"❌ Feature {current_feature['id']} failed after {attempts} attempts. Marking as failed.")
        current_feature["status"] = "failed"
        # Will select next feature in coding phase
        return "coding"

    # Retry
    print(f"⚠️  Tests failed for {current_feature['id']}. Retry attempt {attempts + 1}/3.")
    current_feature["attempts"] = attempts + 1
    return "coding"


def route_after_qa(state: AppBuilderState) -> Literal["coding", "END"]:
    """
    Route after QA - continue to next feature or finish

    Decision logic:
    - If pending features exist → loop back to coding
    - Otherwise → END (all features done/failed)

    Args:
        state: Current application state

    Returns:
        Next node name or END
    """
    feature_list = state.get("feature_list", [])

    # Count remaining pending features
    pending_features = [f for f in feature_list if f.get("status") == "pending"]

    if pending_features:
        print(f"\n{'='*60}")
        print(f"✅ ROUTING: qa_doc → coding (next feature)")
        print(f"   Remaining pending: {len(pending_features)}")
        print(f"   Next features: {[f['id'] + ': ' + f['title'] for f in pending_features[:3]]}")
        if len(pending_features) > 3:
            print(f"   ... and {len(pending_features) - 3} more")
        print(f"{'='*60}\n")
        return "coding"

    # All features processed - calculate final stats
    done = [f for f in feature_list if f.get("status") == "done"]
    failed = [f for f in feature_list if f.get("status") == "failed"]
    in_progress = [f for f in feature_list if f.get("status") == "in_progress"]
    testing = [f for f in feature_list if f.get("status") == "testing"]

    print(f"\n{'='*60}")
    print(f"🎉 WORKFLOW COMPLETE!")
    print(f"   Total features: {len(feature_list)}")
    print(f"   ✅ Done: {len(done)}")
    print(f"   ❌ Failed: {len(failed)}")
    if in_progress:
        print(f"   ⚠️  Still in progress: {len(in_progress)} (unexpected!)")
    if testing:
        print(f"   ⚠️  Still in testing: {len(testing)} (unexpected!)")
    if len(feature_list) > 0:
        print(f"   Success rate: {len(done) / len(feature_list) * 100:.1f}%")
    print(f"{'='*60}\n")
    return "END"


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
    "route_after_coding",
    "route_after_testing",
    "route_after_qa",
    "validate_feature_list_sync",
]
