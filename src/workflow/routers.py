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
    - If current_feature exists → go to testing
    - Otherwise (no more features) → END

    Args:
        state: Current application state

    Returns:
        Next node name or END
    """
    current_feature = state.get("current_feature")

    if current_feature:
        print(f"✅ Feature {current_feature['id']} implemented. Moving to testing.")
        return "testing"

    # No more pending features
    print("✅ All features implemented! Workflow complete.")
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
    Route after QA - continue or finish

    Decision logic:
    - Count pending features
    - If pending features exist → go to coding
    - Otherwise → END

    Args:
        state: Current application state

    Returns:
        Next node name or END
    """
    feature_list = state.get("feature_list", [])

    # Count remaining pending features
    pending_features = [
        f for f in feature_list
        if f.get("status") == "pending"
    ]

    if pending_features:
        print(f"📋 {len(pending_features)} features remaining. Continuing...")
        return "coding"

    # Calculate final stats
    done_features = [f for f in feature_list if f.get("status") == "done"]
    failed_features = [f for f in feature_list if f.get("status") == "failed"]

    print(f"\n{'='*60}")
    print(f"🎉 ALL FEATURES COMPLETED!")
    print(f"   Total: {len(feature_list)}")
    print(f"   ✅ Done: {len(done_features)}")
    print(f"   ❌ Failed: {len(failed_features)}")
    print(f"{'='*60}\n")

    return "END"


__all__ = [
    "route_after_init",
    "route_after_coding",
    "route_after_testing",
    "route_after_qa",
]
