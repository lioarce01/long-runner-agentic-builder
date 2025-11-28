"""
Unit tests for workflow routers

Tests all routing logic and edge cases to ensure
proper workflow transitions.
"""

import pytest
from src.workflow.routers import (
    route_after_init,
    route_after_coding,
    route_after_testing,
    route_after_qa,
    validate_feature_list_sync,
)
from src.state.schemas import AppBuilderState
from langchain_core.messages import HumanMessage


def create_test_state(**overrides) -> AppBuilderState:
    """Helper to create minimal test state"""
    base_state = {
        "messages": [HumanMessage(content="Test message")],
        "project_metadata": {
            "name": "test-project",
            "type": "rest_api",
            "domain": "test",
            "tech_stack": {
                "backend": ["python"],
                "frontend": None,
                "database": None,
                "testing": ["pytest"],
                "deployment": None,
            },
            "estimated_features": 0,
        },
        "repo_path": "/test/repo",
        "project_name": "test-project",
        "feature_list": [],
        "current_feature": None,
        "git_context": {
            "current_branch": "main",
            "last_commit_sha": "",
            "uncommitted_changes": False,
            "snapshot_tag": None,
        },
        "test_context": {
            "last_run_timestamp": "",
            "passed_tests": 0,
            "failed_tests": 0,
            "coverage_percentage": 0.0,
            "failure_details": None,
            "last_result": {},
        },
        "phase": "init",
        "retry_count": 0,
        "max_retries": 3,
        "init_script_path": None,
        "progress_log": [],
    }
    base_state.update(overrides)
    return base_state


class TestRouteAfterInit:
    """Tests for route_after_init"""

    def test_with_features_routes_to_coding(self):
        """When features exist, should route to coding"""
        state = create_test_state(
            feature_list=[
                {"id": "f-001", "status": "pending", "title": "Test"}
            ]
        )
        result = route_after_init(state)
        assert result == "coding"

    def test_with_multiple_features_routes_to_coding(self):
        """When multiple features exist, should route to coding"""
        state = create_test_state(
            feature_list=[
                {"id": "f-001", "status": "pending", "title": "Test 1"},
                {"id": "f-002", "status": "pending", "title": "Test 2"},
                {"id": "f-003", "status": "pending", "title": "Test 3"},
            ]
        )
        result = route_after_init(state)
        assert result == "coding"

    def test_without_features_routes_to_end(self):
        """When no features, should route to END"""
        state = create_test_state(feature_list=[])
        result = route_after_init(state)
        assert result == "END"


class TestRouteAfterCoding:
    """Tests for route_after_coding"""

    def test_with_testing_feature_routes_to_testing(self):
        """When feature is in 'testing' status, route to testing agent"""
        state = create_test_state(
            feature_list=[
                {"id": "f-001", "status": "testing", "title": "Test"}
            ]
        )
        result = route_after_coding(state)
        assert result == "testing"

    def test_with_multiple_testing_features_routes_to_testing(self):
        """When multiple features in testing, route to testing"""
        state = create_test_state(
            feature_list=[
                {"id": "f-001", "status": "testing", "title": "Test 1"},
                {"id": "f-002", "status": "testing", "title": "Test 2"},
                {"id": "f-003", "status": "pending", "title": "Test 3"},
            ]
        )
        result = route_after_coding(state)
        assert result == "testing"

    def test_without_testing_features_routes_to_end(self):
        """
        CRITICAL BUG FIX TEST:
        If coding completes but no features are in testing,
        we should END (this indicates an error).
        """
        state = create_test_state(
            feature_list=[
                {"id": "f-001", "status": "pending", "title": "Test"},
                {"id": "f-002", "status": "in_progress", "title": "Test 2"},
            ]
        )
        result = route_after_coding(state)
        assert result == "END"

    def test_all_done_routes_to_end(self):
        """When all features done, route to END"""
        state = create_test_state(
            feature_list=[
                {"id": "f-001", "status": "done", "title": "Test 1"},
                {"id": "f-002", "status": "done", "title": "Test 2"},
            ]
        )
        result = route_after_coding(state)
        assert result == "END"

    def test_empty_feature_list_routes_to_end(self):
        """When no features, route to END"""
        state = create_test_state(feature_list=[])
        result = route_after_coding(state)
        assert result == "END"

    def test_mixed_statuses_with_testing_routes_to_testing(self):
        """When mixed statuses but some testing, route to testing"""
        state = create_test_state(
            feature_list=[
                {"id": "f-001", "status": "done", "title": "Test 1"},
                {"id": "f-002", "status": "testing", "title": "Test 2"},
                {"id": "f-003", "status": "pending", "title": "Test 3"},
            ]
        )
        result = route_after_coding(state)
        assert result == "testing"


class TestRouteAfterTesting:
    """Tests for route_after_testing"""

    def test_passed_tests_routes_to_qa(self):
        """When tests pass, route to QA"""
        state = create_test_state(
            current_feature={"id": "f-001", "status": "testing", "attempts": 1},
            test_context={
                "last_result": {"passed": True},
                "passed_tests": 5,
                "failed_tests": 0,
            }
        )
        result = route_after_testing(state)
        assert result == "qa_doc"

    def test_failed_tests_with_retries_routes_to_coding(self):
        """When tests fail and retries available, route back to coding"""
        state = create_test_state(
            current_feature={"id": "f-001", "status": "testing", "attempts": 1},
            test_context={
                "last_result": {"passed": False},
                "passed_tests": 3,
                "failed_tests": 2,
            }
        )
        result = route_after_testing(state)
        assert result == "coding"

    def test_failed_tests_max_retries_routes_to_coding(self):
        """When tests fail at max retries, mark as failed and route to coding"""
        state = create_test_state(
            current_feature={"id": "f-001", "status": "testing", "attempts": 3},
            test_context={
                "last_result": {"passed": False},
                "passed_tests": 0,
                "failed_tests": 5,
            }
        )
        result = route_after_testing(state)
        assert result == "coding"
        assert state["current_feature"]["status"] == "failed"

    def test_no_current_feature_routes_to_coding(self):
        """When no current feature, route to coding"""
        state = create_test_state(
            current_feature=None,
            test_context={"last_result": {"passed": False}}
        )
        result = route_after_testing(state)
        assert result == "coding"


class TestRouteAfterQA:
    """Tests for route_after_qa"""

    def test_with_pending_features_loops_to_coding(self):
        """
        CRITICAL LOOP-BACK TEST:
        When pending features exist, loop back to coding for next feature
        """
        state = create_test_state(
            feature_list=[
                {"id": "f-001", "status": "done", "title": "Test 1"},
                {"id": "f-002", "status": "pending", "title": "Test 2"},
                {"id": "f-003", "status": "pending", "title": "Test 3"},
            ]
        )
        result = route_after_qa(state)
        assert result == "coding"

    def test_with_one_pending_loops_to_coding(self):
        """When one pending feature remains, loop to coding"""
        state = create_test_state(
            feature_list=[
                {"id": "f-001", "status": "done", "title": "Test 1"},
                {"id": "f-002", "status": "pending", "title": "Test 2"},
            ]
        )
        result = route_after_qa(state)
        assert result == "coding"

    def test_all_done_routes_to_end(self):
        """When all features done, route to END"""
        state = create_test_state(
            feature_list=[
                {"id": "f-001", "status": "done", "title": "Test 1"},
                {"id": "f-002", "status": "done", "title": "Test 2"},
            ]
        )
        result = route_after_qa(state)
        assert result == "END"

    def test_with_failed_and_done_routes_to_end(self):
        """When all features done or failed, route to END"""
        state = create_test_state(
            feature_list=[
                {"id": "f-001", "status": "done", "title": "Test 1"},
                {"id": "f-002", "status": "failed", "title": "Test 2"},
                {"id": "f-003", "status": "done", "title": "Test 3"},
            ]
        )
        result = route_after_qa(state)
        assert result == "END"

    def test_empty_feature_list_routes_to_end(self):
        """When no features, route to END"""
        state = create_test_state(feature_list=[])
        result = route_after_qa(state)
        assert result == "END"


class TestValidateFeatureListSync:
    """Tests for validate_feature_list_sync"""

    def test_no_repo_path_returns_not_synced(self):
        """When repo_path is empty, validation fails"""
        state = create_test_state(repo_path="")
        result = validate_feature_list_sync(state)
        assert result["synced"] is False

    def test_nonexistent_file_returns_not_synced(self):
        """When feature_list.json doesn't exist, validation fails"""
        state = create_test_state(repo_path="/nonexistent/path")
        result = validate_feature_list_sync(state)
        assert result["synced"] is False
        assert "not found" in result["reason"]


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
