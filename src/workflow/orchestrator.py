"""
Workflow orchestrator using LangGraph 1.0 StateGraph

Creates the multi-agent workflow that coordinates:
- Initializer → Coding → Testing → QA/Doc → (loop or END)

Compatible with:
- LangGraph 1.0.4 (Nov 25, 2025)
"""

import os
import json
from langgraph.graph import StateGraph, START, END
from src.state.schemas import AppBuilderState
from src.agents.initializer import create_initializer_agent
from src.agents.coding import create_coding_agent
from src.agents.testing import create_test_agent
from src.agents.qa_doc import create_qa_doc_agent
from src.workflow.routers import (
    route_after_init,
    route_after_coding,
    route_after_testing,
    route_after_qa
)


def sync_feature_list_from_disk(state: AppBuilderState, repo_path: str) -> AppBuilderState:
    """
    Sync feature_list from disk into state

    This ensures that changes made by tools (which write to feature_list.json)
    are reflected in the state that routers use for decision making.

    Args:
        state: Current state
        repo_path: Repository path

    Returns:
        State with updated feature_list

    Example:
        >>> result = sync_feature_list_from_disk(state, "/path/to/repo")
        >>> print(f"Features in state: {len(result['feature_list'])}")
    """
    feature_list_path = os.path.join(repo_path, "feature_list.json")

    if os.path.exists(feature_list_path):
        try:
            with open(feature_list_path, "r", encoding="utf-8") as f:
                features = json.load(f)

            # Update state with fresh feature list
            state["feature_list"] = features

            print(f"\n{'='*60}")
            print(f"🔄 STATE SYNC: Loaded {len(features)} features from disk")

            # Count by status
            status_counts = {}
            for f in features:
                status = f.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1

            print(f"   Status breakdown: {status_counts}")
            print(f"{'='*60}\n")

        except Exception as e:
            print(f"⚠️  Failed to sync feature_list from disk: {e}")
    else:
        print(f"⚠️  feature_list.json not found at {feature_list_path}")

    return state


async def create_workflow() -> StateGraph:
    """
    Create the multi-agent workflow using LangGraph 1.0's StateGraph

    This function is async because agents need to load tools from MCP servers.

    Workflow:
    ```
    START → Initializer → Coding → Testing → QA/Doc → (back to Coding or END)
                               ↑         ↓
                               └─ retry ─┘
    ```

    Returns:
        StateGraph instance (not yet compiled)

    Example:
        >>> workflow = await create_workflow()
        >>> app = workflow.compile(checkpointer=checkpointer)
        >>> result = await app.ainvoke(initial_state, config)
    """
    # Create the StateGraph with our state schema
    workflow = StateGraph(AppBuilderState)

    # Create all agents (these return CompiledStateGraph)
    # NOTE: These are async because they load tools from MCP servers
    print("🤖 Creating agents...")
    initializer_graph = await create_initializer_agent()
    coding_graph = await create_coding_agent()
    test_graph = await create_test_agent()
    qa_doc_graph = await create_qa_doc_agent()
    print("✅ All agents created")

    # Create wrapper functions to properly integrate agent graphs
    async def initializer_node(state: AppBuilderState) -> AppBuilderState:
        """Wrapper for initializer agent graph"""
        # Debug logging
        messages = state.get('messages', [])
        first_message = messages[0].content if messages else 'N/A'

        print(f"\n{'='*60}")
        print(f"🔍 INITIALIZER AGENT DEBUG INFO:")
        print(f"   First message: {first_message[:150]}...")
        print(f"   Repo path: {state.get('repo_path', 'N/A')}")
        print(f"   Total messages: {len(messages)}")
        print(f"{'='*60}\n")

        result = await initializer_graph.ainvoke(state)

        # CRITICAL: Read feature_list.json and update state
        # The agent saves the file but can't modify state directly
        import os
        import json

        repo_path = state.get("repo_path", "")
        feature_list_path = os.path.join(repo_path, "feature_list.json")

        print(f"🔍 Checking for feature_list.json at: {feature_list_path}")
        print(f"   File exists: {os.path.exists(feature_list_path)}")

        if os.path.exists(feature_list_path):
            try:
                with open(feature_list_path, "r", encoding="utf-8") as f:
                    features = json.load(f)
                result["feature_list"] = features
                print(f"✅ Loaded {len(features)} features into state")
            except Exception as e:
                print(f"⚠️  Failed to load feature_list.json: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"⚠️  feature_list.json not found, state will have empty feature_list")

        return result

    async def coding_node(state: AppBuilderState) -> AppBuilderState:
        """Wrapper for coding agent graph"""
        repo_path = state.get("repo_path", "")
        feature_list = state.get("feature_list", [])
        current_feature = state.get("current_feature")

        print(f"\n{'='*60}")
        print(f"🔍 CODING AGENT STARTING")
        print(f"   Features total: {len(feature_list)}")
        print(f"   Current feature: {current_feature.get('id') if current_feature else 'None'}")
        print(f"   Repo: {repo_path}")
        print(f"{'='*60}\n")

        # Execute coding agent
        result = await coding_graph.ainvoke(state)

        # CRITICAL: Sync feature_list from disk after agent execution
        # Coding agent calls update_feature_status tool which writes to disk
        result = sync_feature_list_from_disk(result, repo_path)

        return result

    async def testing_node(state: AppBuilderState) -> AppBuilderState:
        """Wrapper for testing agent graph"""
        repo_path = state.get("repo_path", "")

        print(f"\n{'='*60}")
        print(f"🧪 TESTING AGENT STARTING")
        print(f"{'='*60}\n")

        # Execute testing agent
        result = await test_graph.ainvoke(state)

        # Sync feature_list from disk
        result = sync_feature_list_from_disk(result, repo_path)

        return result

    async def qa_doc_node(state: AppBuilderState) -> AppBuilderState:
        """Wrapper for QA/Doc agent graph"""
        repo_path = state.get("repo_path", "")

        print(f"\n{'='*60}")
        print(f"📋 QA/DOC AGENT STARTING")
        print(f"{'='*60}\n")

        # Execute QA/Doc agent
        result = await qa_doc_graph.ainvoke(state)

        # CRITICAL: Sync feature_list from disk after agent execution
        # QA agent calls update_feature_status to mark feature as "done"
        result = sync_feature_list_from_disk(result, repo_path)

        return result

    # Add agent nodes to the graph
    workflow.add_node("initializer", initializer_node)
    workflow.add_node("coding", coding_node)
    workflow.add_node("testing", testing_node)
    workflow.add_node("qa_doc", qa_doc_node)

    # Define workflow edges
    # START always goes to initializer
    workflow.add_edge(START, "initializer")

    # Conditional routing after each agent
    workflow.add_conditional_edges(
        "initializer",
        route_after_init,
        {
            "coding": "coding",
            "END": END
        }
    )

    workflow.add_conditional_edges(
        "coding",
        route_after_coding,
        {
            "testing": "testing",
            "END": END
        }
    )

    workflow.add_conditional_edges(
        "testing",
        route_after_testing,
        {
            "qa_doc": "qa_doc",
            "coding": "coding"  # Retry on failure
        }
    )

    workflow.add_conditional_edges(
        "qa_doc",
        route_after_qa,
        {
            "coding": "coding",  # Next feature
            "END": END
        }
    )

    return workflow


__all__ = ["create_workflow"]
