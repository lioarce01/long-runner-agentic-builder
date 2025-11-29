"""
Memory management tools for the multi-agent workflow.

Phase 1: Message cleanup between features to prevent token overflow.
Phase 2: Persistent memory (decisions, patterns, lessons) in JSON files.

Uses LangGraph Command pattern and InjectedState for state access.

Compatible with:
- LangChain 1.1.0 (Nov 24, 2025)
- LangGraph 1.0.4 (Nov 25, 2025)
"""

from langgraph.types import Command
from langchain_core.tools import tool, InjectedToolCallId
from langchain.tools import InjectedState
from langchain_core.messages import HumanMessage, ToolMessage
from typing_extensions import Annotated
from typing import Optional
from datetime import datetime
import os
import json


# =============================================================================
# SELECTIVE CLEANUP: Remove ToolMessages, keep AIMessages
# =============================================================================

def cleanup_tool_messages(messages: list, keep_last_n_tools: int = 2) -> list:
    """
    Remove ToolMessages except the last N (for immediate context).
    Keep all AIMessages and HumanMessages.
    
    This reduces tokens by 60-70% while preserving agent decisions.
    
    Args:
        messages: List of LangChain messages
        keep_last_n_tools: Number of recent ToolMessages to keep (default 2)
    
    Returns:
        Cleaned messages list
    """
    cleaned = []
    tool_messages = []
    
    for msg in messages:
        msg_type = msg.__class__.__name__
        if msg_type == "ToolMessage":
            tool_messages.append(msg)
        else:
            cleaned.append(msg)
    
    # Keep only last N tool messages for immediate context
    if keep_last_n_tools > 0 and tool_messages:
        cleaned.extend(tool_messages[-keep_last_n_tools:])
    
    return cleaned


def create_feature_context_message(state: dict) -> str:
    """
    Create a compact context summary for the current feature.
    Extracts metadata from disk (no LLM calls needed).
    
    Returns ~200-300 tokens of structured context.
    
    Args:
        state: Current workflow state
    
    Returns:
        Formatted context string
    """
    import subprocess
    import glob
    
    feature = state.get("current_feature", {})
    repo_path = state.get("repo_path", "")
    
    if not feature or not repo_path:
        return "No feature context available."
    
    feature_id = feature.get("id", "unknown")
    feature_title = feature.get("title", "Unknown Feature")
    feature_status = feature.get("status", "unknown")
    
    context_parts = [
        f"FEATURE: {feature_id} - {feature_title}",
        f"STATUS: {feature_status}"
    ]
    
    # Get modified files from git status (compact)
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5
        )
        if result.stdout.strip():
            files = [line.split()[-1] for line in result.stdout.strip().split("\n")[:10]]
            context_parts.append(f"FILES MODIFIED: {', '.join(files)}")
    except Exception:
        pass
    
    # Get test results from disk (compact)
    try:
        test_results_dir = os.path.join(repo_path, "test-results")
        if os.path.exists(test_results_dir):
            pattern = os.path.join(test_results_dir, f"{feature_id}_*.json")
            test_files = sorted(glob.glob(pattern), reverse=True)
            if test_files:
                with open(test_files[0], "r", encoding="utf-8") as f:
                    test_data = json.load(f)
                    passed = test_data.get("passed_tests", 0)
                    total = test_data.get("total_tests", 0)
                    result_str = "PASSED" if test_data.get("passed") else "FAILED"
                    context_parts.append(f"TESTS: {passed}/{total} {result_str}")
    except Exception:
        pass
    
    # Get acceptance criteria from feature
    criteria = feature.get("acceptance_criteria", [])
    if criteria:
        context_parts.append(f"CRITERIA: {len(criteria)} items")
    
    return "\n".join(context_parts)


# =============================================================================
# PHASE 2: Persistent Memory Tools (JSON files)
# =============================================================================

# Maximum entries to keep per memory type (prevents unbounded growth)
MAX_DECISIONS = 20
MAX_PATTERNS = 15
MAX_LESSONS = 10

# Maximum characters per read_memory response (~500 tokens)
MAX_MEMORY_CHARS = 2000


def _get_memory_dir(repo_path: str) -> str:
    """Get or create memory directory in project."""
    memory_dir = os.path.join(repo_path, "memory")
    os.makedirs(memory_dir, exist_ok=True)
    return memory_dir


def _load_json(file_path: str) -> list | dict:
    """Load JSON file, return empty list/dict if not exists."""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def _save_json(file_path: str, data: list | dict) -> None:
    """Save data to JSON file."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@tool
def save_decision(
    decision_type: str,
    description: str,
    rationale: str,
    state: Annotated[dict, InjectedState]
) -> str:
    """
    Save an architecture or implementation decision for future reference.
    Call this when you make an important decision that future features should follow.
    
    Args:
        decision_type: Type of decision (architecture, library, pattern, config, api, database)
        description: What was decided (short, <100 chars)
        rationale: Why this decision was made (brief explanation)
    
    Returns:
        Confirmation message
    
    Examples:
        - decision_type: "architecture", description: "Using FastAPI + SQLAlchemy async", rationale: "Better performance for async operations"
        - decision_type: "database", description: "PostgreSQL with UUID primary keys", rationale: "Scalability and distributed systems support"
        - decision_type: "pattern", description: "Repository pattern for data access", rationale: "Separation of concerns, easier testing"
    """
    repo_path = state.get("repo_path", "")
    current_feature = state.get("current_feature", {})
    feature_id = current_feature.get("id", "unknown") if current_feature else "init"
    
    if not repo_path:
        return "Error: repo_path not found in state"
    
    memory_dir = _get_memory_dir(repo_path)
    decisions_file = os.path.join(memory_dir, "decisions.json")
    
    decisions = _load_json(decisions_file)
    if not isinstance(decisions, list):
        decisions = []
    
    # Add new decision
    decisions.append({
        "timestamp": datetime.now().isoformat(),
        "feature_id": feature_id,
        "type": decision_type,
        "description": description[:200],  # Limit size
        "rationale": rationale[:300]
    })
    
    # Keep only last N decisions
    if len(decisions) > MAX_DECISIONS:
        decisions = decisions[-MAX_DECISIONS:]
    
    _save_json(decisions_file, decisions)
    
    print(f"MEMORY: Saved decision [{decision_type}] - {description[:50]}...")
    return f"Decision saved: [{decision_type}] {description}"


@tool
def save_pattern(
    pattern_name: str,
    code_example: str,
    usage_context: str,
    state: Annotated[dict, InjectedState]
) -> str:
    """
    Save a code pattern for reuse across features.
    Call this when you create a reusable pattern that should be consistent across the project.
    
    Args:
        pattern_name: Short name for the pattern (e.g., "error_handler", "api_response", "db_transaction")
        code_example: Brief code snippet or pseudocode showing the pattern
        usage_context: When to use this pattern
    
    Returns:
        Confirmation message
    
    Examples:
        - pattern_name: "error_handler", code_example: "try/except with HTTPException", usage_context: "All API endpoints"
        - pattern_name: "pydantic_model", code_example: "BaseModel with Config.from_attributes=True", usage_context: "All data models"
    """
    repo_path = state.get("repo_path", "")
    
    if not repo_path:
        return "Error: repo_path not found in state"
    
    memory_dir = _get_memory_dir(repo_path)
    patterns_file = os.path.join(memory_dir, "patterns.json")
    
    patterns = _load_json(patterns_file)
    if not isinstance(patterns, dict):
        patterns = {}
    
    # Add or update pattern
    patterns[pattern_name] = {
        "code": code_example[:500],  # Limit size
        "context": usage_context[:200],
        "updated": datetime.now().isoformat()
    }
    
    # Keep only last N patterns (by update time)
    if len(patterns) > MAX_PATTERNS:
        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1].get("updated", ""), reverse=True)
        patterns = dict(sorted_patterns[:MAX_PATTERNS])
    
    _save_json(patterns_file, patterns)
    
    print(f"MEMORY: Saved pattern [{pattern_name}]")
    return f"Pattern saved: {pattern_name}"


@tool
def save_lesson(
    problem: str,
    solution: str,
    state: Annotated[dict, InjectedState]
) -> str:
    """
    Save a lesson learned from an error or challenge encountered.
    Call this when you solve a problem that might occur again in future features.
    
    Args:
        problem: What went wrong or the challenge faced (brief description)
        solution: How it was resolved
    
    Returns:
        Confirmation message
    
    Examples:
        - problem: "Import circular error between models", solution: "Use lazy imports or TYPE_CHECKING"
        - problem: "Pydantic validation error with datetime", solution: "Use datetime.fromisoformat() or add validator"
        - problem: "Test fixtures not found", solution: "Add conftest.py in tests/ directory"
    """
    repo_path = state.get("repo_path", "")
    current_feature = state.get("current_feature", {})
    feature_id = current_feature.get("id", "unknown") if current_feature else "init"
    
    if not repo_path:
        return "Error: repo_path not found in state"
    
    memory_dir = _get_memory_dir(repo_path)
    lessons_file = os.path.join(memory_dir, "lessons.json")
    
    lessons = _load_json(lessons_file)
    if not isinstance(lessons, list):
        lessons = []
    
    # Add new lesson
    lessons.append({
        "timestamp": datetime.now().isoformat(),
        "feature_id": feature_id,
        "problem": problem[:200],
        "solution": solution[:300]
    })
    
    # Keep only last N lessons
    if len(lessons) > MAX_LESSONS:
        lessons = lessons[-MAX_LESSONS:]
    
    _save_json(lessons_file, lessons)
    
    print(f"MEMORY: Saved lesson - {problem[:40]}...")
    return f"Lesson saved: {problem[:50]}..."


@tool
def read_memory(
    state: Annotated[dict, InjectedState]
) -> str:
    """
    Read all persistent memory (decisions, patterns, lessons).
    Call this at the START of implementing a feature to understand previous decisions and avoid repeating mistakes.
    
    Returns:
        Formatted memory content with previous decisions, patterns, and lessons.
        Returns "No memory stored yet" if this is the first feature.
    """
    repo_path = state.get("repo_path", "")
    
    if not repo_path:
        return "Error: repo_path not found in state"
    
    memory_dir = os.path.join(repo_path, "memory")
    
    if not os.path.exists(memory_dir):
        return "No memory stored yet. This is the first feature - make good decisions!"
    
    output = []
    current_chars = 0
    
    # Read decisions (most recent first, limit 5)
    decisions_file = os.path.join(memory_dir, "decisions.json")
    if os.path.exists(decisions_file):
        decisions = _load_json(decisions_file)
        if decisions and isinstance(decisions, list):
            output.append("PREVIOUS DECISIONS:")
            for d in decisions[-5:]:
                line = f"  - [{d.get('type', 'general')}] {d.get('description', '')}"
                if current_chars + len(line) < MAX_MEMORY_CHARS:
                    output.append(line)
                    current_chars += len(line)
    
    # Read patterns (limit 5)
    patterns_file = os.path.join(memory_dir, "patterns.json")
    if os.path.exists(patterns_file):
        patterns = _load_json(patterns_file)
        if patterns and isinstance(patterns, dict):
            output.append("\nCODE PATTERNS:")
            for name, p in list(patterns.items())[-5:]:
                line = f"  - {name}: {p.get('context', '')}"
                if current_chars + len(line) < MAX_MEMORY_CHARS:
                    output.append(line)
                    current_chars += len(line)
    
    # Read lessons (limit 3)
    lessons_file = os.path.join(memory_dir, "lessons.json")
    if os.path.exists(lessons_file):
        lessons = _load_json(lessons_file)
        if lessons and isinstance(lessons, list):
            output.append("\nLESSONS LEARNED:")
            for l in lessons[-3:]:
                problem = l.get('problem', '')[:60]
                solution = l.get('solution', '')[:60]
                line = f"  - {problem}... -> {solution}..."
                if current_chars + len(line) < MAX_MEMORY_CHARS:
                    output.append(line)
                    current_chars += len(line)
    
    if not output:
        return "No memory stored yet. This is the first feature - make good decisions!"
    
    result = "\n".join(output)
    print(f"MEMORY: Read {len(result)} chars of context")
    return result


@tool
def cleanup_messages_for_next_feature(
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """
    Clean conversation history after completing a feature.
    Resets messages to only the original project description.
    
    Call this as the LAST step after committing and pushing a feature.
    This prevents token overflow by removing accumulated conversation history.
    
    The workflow state (feature_list, progress_log, etc.) is preserved.
    Only the messages array is reset.
    
    Returns:
        Command to update state with clean messages
    """
    original_prompt = state.get("original_prompt", "")
    current_feature = state.get("current_feature", {})
    feature_id = current_feature.get("id", "unknown") if current_feature else "unknown"
    
    # Count current messages for logging
    current_messages = state.get("messages", [])
    message_count = len(current_messages)
    
    print(f"\n{'='*50}")
    print(f"MEMORY CLEANUP")
    print(f"{'='*50}")
    print(f"Feature completed: {feature_id}")
    print(f"Messages before cleanup: {message_count}")
    print(f"Messages after cleanup: 2 (tool response + original prompt)")
    print(f"{'='*50}\n")
    
    # Return Command to update state
    # IMPORTANT: Must include ToolMessage for the tool call, then the new messages
    # LangGraph requires every tool call to have a corresponding ToolMessage
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"Memory cleanup complete. Cleared {message_count} messages. Ready for next feature.",
                    tool_call_id=tool_call_id
                ),
                HumanMessage(content=original_prompt)
            ],
        }
    )


# =============================================================================
# PHASE 1: Message Cleanup Tool (already implemented above)
# =============================================================================
# cleanup_messages_for_next_feature is defined above


# Export all tools
__all__ = [
    # Selective cleanup (inter-agent)
    "cleanup_tool_messages",
    "create_feature_context_message",
    # Phase 1: Full message cleanup (after feature)
    "cleanup_messages_for_next_feature",
    # Phase 2: Persistent memory
    "save_decision",
    "save_pattern", 
    "save_lesson",
    "read_memory",
]

