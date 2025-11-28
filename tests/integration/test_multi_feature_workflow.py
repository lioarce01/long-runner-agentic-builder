"""
Integration test for multi-feature workflow

Tests that the workflow processes multiple features sequentially
and properly loops back from QA to Coding for the next feature.
"""

import pytest
import asyncio
import tempfile
import shutil
import os
import json
from pathlib import Path


class TestMultiFeatureWorkflow:
    """Integration tests for multi-feature workflow"""

    @pytest.mark.asyncio
    async def test_workflow_state_sync_simulation(self):
        """
        Test state synchronization logic without running full workflow

        This test simulates the workflow by:
        1. Creating feature_list.json with 3 features
        2. Simulating coding agent updating a feature to "testing"
        3. Verifying sync_feature_list_from_disk loads the change
        4. Simulating QA agent updating to "done"
        5. Verifying router sees correct state for next feature
        """
        from src.workflow.orchestrator import sync_feature_list_from_disk
        from src.workflow.routers import route_after_coding, route_after_qa
        from langchain_core.messages import HumanMessage

        # Create temporary directory for test repo
        test_repo = tempfile.mkdtemp(prefix="test_workflow_")

        try:
            # Create feature_list.json with 3 simple features
            feature_list = [
                {
                    "id": "f-001",
                    "title": "Create main.py",
                    "description": "Create basic main.py file",
                    "acceptance_criteria": ["main.py exists"],
                    "status": "pending",
                    "priority": 1,
                    "complexity": "low",
                    "attempts": 0,
                },
                {
                    "id": "f-002",
                    "title": "Create README.md",
                    "description": "Create README documentation",
                    "acceptance_criteria": ["README.md exists"],
                    "status": "pending",
                    "priority": 1,
                    "complexity": "low",
                    "attempts": 0,
                },
                {
                    "id": "f-003",
                    "title": "Create requirements.txt",
                    "description": "Create requirements file",
                    "acceptance_criteria": ["requirements.txt exists"],
                    "status": "pending",
                    "priority": 1,
                    "complexity": "low",
                    "attempts": 0,
                },
            ]

            # Write feature list to disk
            feature_path = os.path.join(test_repo, "feature_list.json")
            with open(feature_path, "w", encoding="utf-8") as f:
                json.dump(feature_list, f, indent=2)

            # === STEP 1: Simulate Coding Agent ===
            # Initial state (as if coding just started)
            state = {
                "messages": [HumanMessage(content="Create a simple Python project")],
                "repo_path": test_repo,
                "feature_list": feature_list,  # Initial state
                "current_feature": None,
            }

            # Coding agent "updates" f-001 to "testing" on disk
            with open(feature_path, "r", encoding="utf-8") as f:
                disk_features = json.load(f)
            disk_features[0]["status"] = "testing"  # Simulate coding agent updating
            with open(feature_path, "w", encoding="utf-8") as f:
                json.dump(disk_features, f, indent=2)

            # Sync state from disk (this is what orchestrator does)
            state = sync_feature_list_from_disk(state, test_repo)

            # Verify state is synced
            assert len(state["feature_list"]) == 3
            assert state["feature_list"][0]["status"] == "testing"

            # Router should see "testing" feature and route to testing agent
            route = route_after_coding(state)
            assert route == "testing", f"Expected 'testing', got '{route}'"

            # === STEP 2: Simulate QA Agent ===
            # QA agent marks f-001 as "done"
            with open(feature_path, "r", encoding="utf-8") as f:
                disk_features = json.load(f)
            disk_features[0]["status"] = "done"  # Simulate QA approval
            with open(feature_path, "w", encoding="utf-8") as f:
                json.dump(disk_features, f, indent=2)

            # Sync state from disk again
            state = sync_feature_list_from_disk(state, test_repo)

            # Verify state shows f-001 as done, f-002 and f-003 still pending
            assert state["feature_list"][0]["status"] == "done"
            assert state["feature_list"][1]["status"] == "pending"
            assert state["feature_list"][2]["status"] == "pending"

            # Router should loop back to coding for next pending feature
            route = route_after_qa(state)
            assert route == "coding", f"Expected 'coding' (loop back), got '{route}'"

            # === STEP 3: Process remaining features ===
            # Simulate completing f-002
            with open(feature_path, "r", encoding="utf-8") as f:
                disk_features = json.load(f)
            disk_features[1]["status"] = "done"
            with open(feature_path, "w", encoding="utf-8") as f:
                json.dump(disk_features, f, indent=2)

            state = sync_feature_list_from_disk(state, test_repo)

            # Still one pending, should loop back
            route = route_after_qa(state)
            assert route == "coding", f"Expected 'coding', got '{route}'"

            # === STEP 4: Complete all features ===
            # Simulate completing f-003
            with open(feature_path, "r", encoding="utf-8") as f:
                disk_features = json.load(f)
            disk_features[2]["status"] = "done"
            with open(feature_path, "w", encoding="utf-8") as f:
                json.dump(disk_features, f, indent=2)

            state = sync_feature_list_from_disk(state, test_repo)

            # All done, should END
            route = route_after_qa(state)
            assert route == "END", f"Expected 'END', got '{route}'"

            print("\n✅ Integration test passed!")
            print(f"   Successfully processed {len(feature_list)} features")
            print(f"   State sync worked correctly")
            print(f"   Loop-back functionality verified")

        finally:
            # Cleanup temp directory
            shutil.rmtree(test_repo, ignore_errors=True)

    def test_feature_list_sync_accuracy(self):
        """Test that sync_feature_list_from_disk accurately syncs all statuses"""
        from src.workflow.orchestrator import sync_feature_list_from_disk

        test_repo = tempfile.mkdtemp(prefix="test_sync_")

        try:
            # Create feature list with various statuses
            feature_list = [
                {"id": "f-001", "status": "done", "title": "Feature 1"},
                {"id": "f-002", "status": "testing", "title": "Feature 2"},
                {"id": "f-003", "status": "pending", "title": "Feature 3"},
                {"id": "f-004", "status": "failed", "title": "Feature 4"},
            ]

            feature_path = os.path.join(test_repo, "feature_list.json")
            with open(feature_path, "w", encoding="utf-8") as f:
                json.dump(feature_list, f, indent=2)

            # Create state with different statuses (simulating stale state)
            stale_state = {
                "repo_path": test_repo,
                "feature_list": [
                    {"id": "f-001", "status": "pending", "title": "Feature 1"},
                    {"id": "f-002", "status": "pending", "title": "Feature 2"},
                    {"id": "f-003", "status": "pending", "title": "Feature 3"},
                    {"id": "f-004", "status": "pending", "title": "Feature 4"},
                ],
            }

            # Sync from disk
            synced_state = sync_feature_list_from_disk(stale_state, test_repo)

            # Verify all statuses are updated
            assert synced_state["feature_list"][0]["status"] == "done"
            assert synced_state["feature_list"][1]["status"] == "testing"
            assert synced_state["feature_list"][2]["status"] == "pending"
            assert synced_state["feature_list"][3]["status"] == "failed"

            print("\n✅ Sync accuracy test passed!")

        finally:
            shutil.rmtree(test_repo, ignore_errors=True)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
