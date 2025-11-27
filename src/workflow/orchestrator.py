"""
Workflow orchestrator using LangGraph 1.0 StateGraph

Creates the multi-agent workflow that coordinates:
- Initializer → Coding → Testing → QA/Doc → (loop or END)

Compatible with:
- LangGraph 1.0.4 (Nov 25, 2025)
"""

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


def create_workflow() -> StateGraph:
    """
    Create the multi-agent workflow using LangGraph 1.0's StateGraph

    Workflow:
    ```
    START → Initializer → Coding → Testing → QA/Doc → (back to Coding or END)
                               ↑         ↓
                               └─ retry ─┘
    ```

    Returns:
        StateGraph instance (not yet compiled)

    Example:
        >>> workflow = create_workflow()
        >>> app = workflow.compile(checkpointer=checkpointer)
        >>> result = await app.ainvoke(initial_state, config)
    """
    # Create the StateGraph with our state schema
    workflow = StateGraph(AppBuilderState)

    # Create all agents
    print("🤖 Creating agents...")
    initializer_agent = create_initializer_agent()
    coding_agent = create_coding_agent()
    test_agent = create_test_agent()
    qa_doc_agent = create_qa_doc_agent()
    print("✅ All agents created")

    # Add agent nodes to the graph
    workflow.add_node("initializer", initializer_agent)
    workflow.add_node("coding", coding_agent)
    workflow.add_node("testing", test_agent)
    workflow.add_node("qa_doc", qa_doc_agent)

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
