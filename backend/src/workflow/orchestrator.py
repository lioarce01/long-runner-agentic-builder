"""
Workflow orchestrator using LangGraph 1.0 StateGraph

Creates the multi-agent workflow that coordinates:
- Initializer -> GitOps -> Coding -> Testing -> QA/Doc -> GitOps -> (loop or END)

GitOps Agent handles all Git/GitHub operations:
- After Initializer: Create repo, initial commit, push
- After QA: Review changes, create feature commit, push

Compatible with:
- LangGraph 1.0.4 (Nov 25, 2025)
"""

import os
import json
from datetime import datetime
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from src.state.schemas import AppBuilderState
from src.tools.memory_tools import cleanup_tool_messages, create_feature_context_message
from src.tools.recovery_tools import (
    mark_pending,
    clear_all_pending,
    check_recovery_needed,
    get_recovery_features
)
from src.agents.initializer import create_initializer_agent
from src.agents.gitops import create_gitops_agent
from src.agents.coding import create_coding_agent
from src.agents.testing import create_test_agent
from src.agents.qa_doc import create_qa_doc_agent
from src.workflow.routers import (
    route_after_init,
    route_after_gitops,
    route_after_coding,
    route_after_testing,
    route_after_qa
)


def log_progress(repo_path: str, agent: str, feature_id: str, action: str, notes: str = "") -> None:
    """
    Automatically log progress to progress_log.json

    Args:
        repo_path: Path to project repository
        agent: Agent name (coding, testing, qa_doc, gitops)
        feature_id: Feature ID being worked on
        action: Action performed (e.g., "implemented", "tested", "documented")
        notes: Optional additional notes
    """
    log_path = os.path.join(repo_path, "progress_log.json")

    # Read existing log
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    else:
        logs = []

    # Create new entry
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent": agent,
        "feature_id": feature_id,
        "action": action,
        "notes": notes
    }

    # Append and save
    logs.append(entry)

    try:
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
        print(f"[PROGRESS] [{agent}] {feature_id} - {action}")
    except Exception as e:
        print(f"[WARNING] Failed to log progress: {e}")


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
            print(f"[SYNC] Loaded {len(features)} features from disk")

            # Count by status
            status_counts = {}
            for f in features:
                status = f.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1

            print(f"   Status breakdown: {status_counts}")
            print(f"{'='*60}\n")

        except Exception as e:
            print(f"[WARNING] Failed to sync feature_list from disk: {e}")
    else:
        print(f"[WARNING] feature_list.json not found at {feature_list_path}")

    return state


def startup_recovery_check(state: AppBuilderState) -> AppBuilderState:
    """
    Check for pending operations that need recovery on startup.
    
    This runs at the beginning of the workflow to detect:
    - Features marked "done" locally but not committed to git
    - Explicit pending operations from previous crashed runs
    
    If recovery is needed, sets gitops_mode="recovery" to trigger
    recovery processing before normal workflow continues.
    
    Args:
        state: Current state
        
    Returns:
        State with recovery_features set if recovery needed
    """
    repo_path = state.get("repo_path", "")
    feature_list = state.get("feature_list", [])
    
    if not repo_path or not os.path.exists(repo_path):
        return state
    
    # Check if recovery is needed
    recovery_needed = check_recovery_needed(repo_path, feature_list)
    
    needs_commit = recovery_needed.get("needs_commit", [])
    needs_push = recovery_needed.get("needs_push", [])
    
    if needs_commit or needs_push:
        # Get full feature objects for recovery
        recovery_features = get_recovery_features(repo_path, feature_list)
        
        print(f"\n{'='*60}")
        print(f"[RECOVERY] Found {len(recovery_features)} features needing recovery")
        for f in recovery_features:
            print(f"   - {f['id']}: {f['title']}")
        print(f"{'='*60}\n")
        
        # Set recovery mode
        state["gitops_mode"] = "recovery"
        state["recovery_features"] = recovery_features
        state["recovery_needed"] = recovery_needed
    
    return state


async def create_workflow() -> StateGraph:
    """
    Create the multi-agent workflow using LangGraph 1.0's StateGraph

    This function is async because agents need to load tools from MCP servers.

    Workflow:
    ```
    START -> Initializer -> GitOps -> Coding -> Testing -> QA/Doc -> GitOps -> (back to Coding or END)
                                                                    
                        INIT mode                              FEATURE mode
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
    print("[WORKFLOW] Creating agents...")
    initializer_graph = await create_initializer_agent()
    gitops_graph = await create_gitops_agent()
    coding_graph = await create_coding_agent()
    test_graph = await create_test_agent()
    qa_doc_graph = await create_qa_doc_agent()
    print("[WORKFLOW] All agents created")

    # Create wrapper functions to properly integrate agent graphs
    async def initializer_node(state: AppBuilderState) -> AppBuilderState:
        """Wrapper for initializer agent graph"""
        # Debug logging
        messages = state.get('messages', [])
        first_message = messages[0].content if messages else 'N/A'
        repo_path = state.get("repo_path", "")

        print(f"\n{'='*60}")
        print(f"[DEBUG] INITIALIZER AGENT DEBUG INFO:")
        print(f"   First message: {first_message[:150]}...")
        print(f"   Repo path: {repo_path}")
        print(f"   Total messages: {len(messages)}")
        print(f"{'='*60}\n")

        # EARLY RECOVERY CHECK: Before running initializer, check if this is a resume
        # If feature_list.json exists and has done features without commits, skip initializer
        feature_list_path = os.path.join(repo_path, "feature_list.json")
        if os.path.exists(feature_list_path):
            try:
                with open(feature_list_path, "r", encoding="utf-8") as f:
                    existing_features = json.load(f)
                
                if existing_features:
                    print(f"[EMOJI] Found existing project with {len(existing_features)} features")
                    
                    # Create a temporary state to check for recovery
                    temp_state = dict(state)
                    temp_state["feature_list"] = existing_features
                    temp_state = startup_recovery_check(temp_state)
                    
                    # If recovery is needed, skip initializer entirely
                    if temp_state.get("gitops_mode") == "recovery":
                        print(f"[RESUME] Recovery mode - skipping initializer agent")
                        return temp_state
                    
                    # Project exists but no recovery needed - check status
                    done = [f for f in existing_features if f.get("status") == "done"]
                    pending = [f for f in existing_features if f.get("status") == "pending"]
                    testing = [f for f in existing_features if f.get("status") == "testing"]
                    in_progress = [f for f in existing_features if f.get("status") == "in_progress"]
                    failed = [f for f in existing_features if f.get("status") == "failed"]
                    
                    # Project complete only if ALL features are done (none pending/testing/in_progress)
                    # Failed features are considered "complete" (gave up after retries)
                    if (done or failed) and not pending and not testing and not in_progress:
                        total_done = len(done) + len(failed)
                        print(f"[OK] Project already complete ({len(done)} done, {len(failed)} failed)")
                        temp_state["gitops_mode"] = "complete"
                        return temp_state
                    
                    # Project in progress - skip to coding directly
                    print(f"[STATS] Project in progress:")
                    print(f"   Done: {len(done)}, Pending: {len(pending)}, Testing: {len(testing)}")
                    print(f"   In Progress: {len(in_progress)}, Failed: {len(failed)}")
                    print(f"-> Will skip initializer and gitops, go straight to coding")
                    temp_state["gitops_mode"] = "resume"
                    return temp_state
                    
            except Exception as e:
                print(f"[WARN]  Error checking existing project: {e}")
                # Continue with normal initialization

        # No existing project - run initializer agent
        result = await initializer_graph.ainvoke(state)

        # Debug: Print agent output with error handling
        try:
            print(f"\n{'='*60}")
            print(f"[DEBUG] INITIALIZER AGENT OUTPUT:")
            messages = result.get('messages', [])
            print(f"   Messages returned: {len(messages)}")

            if messages:
                last_msg = messages[-1]
                print(f"   Last message type: {type(last_msg).__name__}")

                # Safely get content
                try:
                    content = str(last_msg.content) if hasattr(last_msg, 'content') else 'N/A'
                    print(f"   Last message content: {content[:500]}...")
                except Exception as e:
                    print(f"   [WARN] Error getting content: {e}")

                # Check for tool calls
                if hasattr(last_msg, 'tool_calls'):
                    print(f"   Tool calls: {last_msg.tool_calls if last_msg.tool_calls else 'None'}")

                # Print all message types
                print(f"   Message types: {[type(m).__name__ for m in messages]}")

                # Print ALL tool calls made during the session
                print(f"\n   [QA] ALL TOOL CALLS IN SESSION:")
                for i, msg in enumerate(messages):
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tc in msg.tool_calls:
                            print(f"      {i}. {tc.get('name', 'unknown')}({list(tc.get('args', {}).keys())})")
                    elif type(msg).__name__ == 'ToolMessage':
                        print(f"      {i}. ToolMessage: {msg.name if hasattr(msg, 'name') else 'unknown'}")
            else:
                print(f"   [WARN] No messages in result!")

            print(f"{'='*60}\n")
        except Exception as e:
            print(f"[WARN] Error printing agent output: {e}")
            import traceback
            traceback.print_exc()

        # CRITICAL: Read feature_list.json and update state
        # The agent saves the file but can't modify state directly
        # NOTE: repo_path already defined at the top of the function
        feature_list_path = os.path.join(repo_path, "feature_list.json")

        print(f"[DEBUG] Checking for feature_list.json at: {feature_list_path}")
        print(f"   File exists: {os.path.exists(feature_list_path)}")

        if os.path.exists(feature_list_path):
            try:
                with open(feature_list_path, "r", encoding="utf-8") as f:
                    features = json.load(f)
                result["feature_list"] = features
                print(f"[OK] Loaded {len(features)} features into state")
                # NOTE: Recovery check already done at the beginning of this function
            except Exception as e:
                print(f"[WARN]  Failed to load feature_list.json: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[WARN]  feature_list.json not found, state will have empty feature_list")

        # Set gitops_mode to "init" for GitOps agent
        result["gitops_mode"] = "init"

        return result

    async def gitops_node(state: AppBuilderState) -> AppBuilderState:
        """Wrapper for gitops agent graph"""
        gitops_mode = state.get("gitops_mode", "feature")
        project_name = state.get("project_name", "")
        repo_path = state.get("repo_path", "")
        current_feature = state.get("current_feature")
        recovery_features = state.get("recovery_features", [])
        
        print(f"\n{'='*60}")
        print(f"[GITOPS] GITOPS AGENT STARTING (MODE: {gitops_mode})")
        print(f"{'='*60}\n")

        # Handle RECOVERY mode - process features that didn't get committed/pushed
        if gitops_mode == "recovery" and recovery_features:
            feature_ids = [f.get("id", "unknown") for f in recovery_features]

            print(f"[RESUME] RECOVERY MODE: Processing {len(recovery_features)} pending features")
            
            instruction = SystemMessage(content=f"""GITOPS RECOVERY: Commit/push {len(recovery_features)} features: {', '.join(feature_ids)}
REPO: {repo_path}
STEPS: get_git_status -> commit if needed -> push_to_github""")
            # NOTE: Don't mark_pending here - they're already pending (that's why we're in recovery)

        # Handle INIT mode
        elif gitops_mode == "init":
            instruction = SystemMessage(content=f"""GITOPS INIT: Project "{project_name}" at {repo_path}
STEPS: create_git_repo -> commit "chore: Initialize" -> create_github_repo -> add_remote -> push""")
        # Handle FEATURE mode (normal per-feature commit)
        else:
            # Verify we have a valid current_feature
            if not current_feature:
                print(f"[WARN]  GITOPS WARNING: No current_feature in FEATURE mode!")
                print(f"   This indicates a bug in workflow - skipping gitops")
                # Return state unchanged to avoid corrupting pending_ops
                return state
            
            feature_id = current_feature.get("id", "unknown")
            feature_title = current_feature.get("title", "Feature")
            
            # Additional validation
            if feature_id == "unknown":
                print(f"[WARN]  GITOPS WARNING: current_feature has no valid ID!")
                return state
            
            # Mark this feature's operations as pending BEFORE executing
            mark_pending(repo_path, "commit", feature_id)
            mark_pending(repo_path, "push", feature_id)
            
            # Get compact context from previous agents
            feature_context = create_feature_context_message(state)
            
            instruction = SystemMessage(content=f"""GITOPS FEATURE: {feature_context}
REPO: {repo_path}
STEPS: get_git_status -> commit {feature_id} -> push_to_github""")
        
        # Add instruction to messages
        modified_state = dict(state)
        modified_state["messages"] = list(state.get("messages", [])) + [instruction]

        # Execute gitops agent with modified state
        result = await gitops_graph.ainvoke(modified_state)

        # Log progress based on mode
        if gitops_mode == "init":
            log_progress(repo_path, "gitops", "project", "initialized", f"Created repo and initial commit for {project_name}")
        elif gitops_mode == "recovery" and recovery_features:
            feature_ids = [f.get("id", "unknown") for f in recovery_features]
            log_progress(repo_path, "gitops", "recovery", "recovered", f"Committed/pushed {len(recovery_features)} features: {', '.join(feature_ids)}")
        elif gitops_mode == "feature" and current_feature:
            feature_id = current_feature.get("id", "unknown")
            log_progress(repo_path, "gitops", feature_id, "committed", f"Committed and pushed {current_feature.get('title', 'feature')}")

        # CLEAR PENDING OPS after successful execution
        if gitops_mode == "recovery" and recovery_features:
            # Clear all recovery features' pending ops
            for f in recovery_features:
                fid = f.get("id", "unknown")
                clear_all_pending(repo_path, fid)
            
            # Clear recovery state
            result["recovery_features"] = []
            result["recovery_needed"] = {}
            result["gitops_mode"] = "feature"  # Reset to normal mode
            
            print(f"\n{'='*50}")
            print(f"[OK] RECOVERY COMPLETE: {len(recovery_features)} features committed/pushed")
            print(f"{'='*50}\n")
            
        elif gitops_mode == "feature":
            feature_id = current_feature.get("id", "unknown") if current_feature else "unknown"
            
            # Clear pending ops for this feature (successful completion)
            clear_all_pending(repo_path, feature_id)

        # AUTOMATIC MEMORY CLEANUP (don't rely on LLM to call the tool)
        # This runs after FEATURE or RECOVERY mode to prevent token overflow
        if gitops_mode in ["feature", "recovery"]:
            original_prompt = state.get("original_prompt", "")
            current_messages = result.get("messages", [])
            message_count = len(current_messages)
            
            # Get feature description for logging
            if gitops_mode == "recovery":
                feature_desc = f"recovery ({len(recovery_features)} features)"
            elif current_feature:
                feature_desc = current_feature.get("id", "unknown")
            else:
                feature_desc = "unknown"
            
            print(f"\n{'='*50}")
            print(f"MEMORY CLEANUP (automatic)")
            print(f"{'='*50}")
            print(f"Completed: {feature_desc}")
            print(f"Messages before cleanup: {message_count}")
            print(f"Messages after cleanup: 1 (original prompt)")
            print(f"{'='*50}\n")
            
            # Reset messages to just the original prompt
            # This prevents token accumulation across features
            result["messages"] = [HumanMessage(content=original_prompt)]

        return result

    async def coding_node(state: AppBuilderState) -> AppBuilderState:
        """Wrapper for coding agent graph"""
        import subprocess
        import platform
        
        repo_path = state.get("repo_path", "")
        feature_list = state.get("feature_list", [])
        current_feature = state.get("current_feature")
        
        # AUTO-SETUP: Create project venv and install dependencies (once)
        # This runs when requirements.txt exists but .venv doesn't
        requirements_file = os.path.join(repo_path, "requirements.txt")
        venv_path = os.path.join(repo_path, ".venv")
        is_windows = platform.system() == "Windows"
        
        if os.path.exists(requirements_file) and not os.path.exists(venv_path):
            print(f"\n{'='*50}")
            print(f"[SETUP] AUTO-SETUP: Creating project environment")
            print(f"{'='*50}")
            
            # Step 1: Create venv
            print(f"   Creating venv at {venv_path}...")
            subprocess.run(
                ["python", "-m", "venv", ".venv"],
                cwd=repo_path,
                capture_output=True,
                encoding="utf-8"
            )
            print(f"   [OK] Venv created")
            
            # Step 2: Install dependencies using project's pip
            if is_windows:
                pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
            else:
                pip_path = os.path.join(venv_path, "bin", "pip")
            
            print(f"   Installing dependencies from requirements.txt...")
            install_result = subprocess.run(
                [pip_path, "install", "-r", "requirements.txt", "-q"],
                cwd=repo_path,
                capture_output=True,
                encoding="utf-8",
                errors="replace"
            )
            
            if install_result.returncode == 0:
                print(f"   [OK] Dependencies installed successfully")
            else:
                print(f"   [WARN]  Some dependencies may have failed:")
                if install_result.stderr:
                    print(f"   {install_result.stderr[:200]}")
            
            print(f"{'='*50}\n")
        
        # Count features by status
        pending = [f for f in feature_list if f.get("status") == "pending"]
        testing = [f for f in feature_list if f.get("status") == "testing"]

        print(f"\n{'='*60}")
        print(f"[DEBUG] CODING AGENT STARTING")
        print(f"   Features total: {len(feature_list)}")
        print(f"   Testing (retry): {len(testing)}")
        print(f"   Pending: {len(pending)}")
        print(f"   Current feature: {current_feature.get('id') if current_feature else 'None'}")
        print(f"   Repo: {repo_path}")
        print(f"{'='*60}\n")

        # Build instruction based on whether this is a retry or new feature
        if testing:
            # RETRY MODE: A feature failed tests, fix it
            retry_feature = testing[0]
            retry_id = retry_feature.get("id", "unknown")
            retry_title = retry_feature.get("title", "Feature")
            retry_attempts = retry_feature.get("attempts", 0)
            
            instruction = SystemMessage(content=f"""CODING RETRY: Fix {retry_id} - {retry_title} (attempt {retry_attempts}/3)
TASK: select_next_feature -> read test results -> fix code -> update_feature_status("testing")
Call select_next_feature ONCE only.""")
        else:
            # NORMAL MODE: Implement next pending feature
            instruction = SystemMessage(content=f"""CODING NEW: {len(pending)} pending features
TASK: select_next_feature ONCE -> implement code -> update_feature_status("testing")""")
        
        # Add instruction to messages
        modified_state = dict(state)
        modified_state["messages"] = list(state.get("messages", [])) + [instruction]

        # Execute coding agent with modified state
        result = await coding_graph.ainvoke(modified_state)

        # CRITICAL: Sync feature_list from disk after agent execution
        # Coding agent calls update_feature_status tool which writes to disk
        result = sync_feature_list_from_disk(result, repo_path)

        # Log progress - find which feature was worked on
        feature_list = result.get("feature_list", [])
        testing_features = [f for f in feature_list if f.get("status") == "testing"]
        if testing_features:
            worked_feature = testing_features[0]
            attempts = worked_feature.get("attempts", 0)
            action = "retry" if attempts > 0 else "implemented"
            log_progress(repo_path, "coding", worked_feature.get("id", "unknown"), action,
                        f"{worked_feature.get('title', 'feature')} (attempt {attempts + 1})")

        # PHASE 4.1: Trim conversation history to max 4000 tokens
        from src.tools.message_trimmer import trim_conversation_history
        result["messages"] = trim_conversation_history(result["messages"], max_tokens=4000)

        # CRITICAL: Sync current_feature - find the feature that was just worked on
        # The agent should have set a feature to "testing" status
        feature_list = result.get("feature_list", [])
        
        # Get the feature ID from messages if possible (the agent should mention it)
        # Otherwise, find the most recently changed feature
        testing_features = [f for f in feature_list if f.get("status") == "testing"]
        
        if testing_features:
            # If there's only one testing feature, use it
            if len(testing_features) == 1:
                result["current_feature"] = testing_features[0]
                print(f"[OK] Set current_feature to: {testing_features[0]['id']}")
            else:
                # Multiple testing features - use the one with lowest priority (worked first)
                # or the one with most attempts (being retried)
                testing_features.sort(key=lambda f: (-f.get("attempts", 0), f.get("priority", 999)))
                result["current_feature"] = testing_features[0]
                print(f"[OK] Set current_feature to: {testing_features[0]['id']} (from {len(testing_features)} testing features)")
        else:
            # Check for in_progress features
            in_progress = [f for f in feature_list if f.get("status") == "in_progress"]
            if in_progress:
                result["current_feature"] = in_progress[0]
                print(f"[OK] Set current_feature to in_progress: {in_progress[0]['id']}")
            else:
                print(f"[WARN]  No feature in testing or in_progress state")

        # SELECTIVE CLEANUP: Remove ToolMessages to reduce tokens
        # Keep last 1 tool message for immediate context (Phase 3.3 optimization)
        messages_before = len(result.get("messages", []))
        result["messages"] = cleanup_tool_messages(result["messages"], keep_last_n_tools=1)
        messages_after = len(result.get("messages", []))
        print(f"[CLEANUP] SELECTIVE CLEANUP (coding): {messages_before} -> {messages_after} messages")

        # PHASE 4.4: Track token usage for optimization insights
        from src.utils.token_counter import count_messages_tokens, log_token_usage
        token_count = count_messages_tokens(result.get("messages", []))
        current_feature_id = result.get("current_feature", {}).get("id", "unknown")
        log_token_usage("coding", current_feature_id, token_count, repo_path, len(result.get("messages", [])))

        return result

    async def testing_node(state: AppBuilderState) -> AppBuilderState:
        """Wrapper for testing agent graph"""
        repo_path = state.get("repo_path", "")
        current_feature = state.get("current_feature")
        feature_id = current_feature.get("id", "unknown") if current_feature else "unknown"
        feature_title = current_feature.get("title", "Feature") if current_feature else "Feature"

        print(f"\n{'='*60}")
        print(f"[TEST] TESTING AGENT STARTING")
        print(f"   Feature: {feature_id} - {feature_title}")
        print(f"{'='*60}\n")

        # Get compact context from previous agent
        feature_context = create_feature_context_message(state)

        # Add instruction message with injected context
        instruction = SystemMessage(content=f"""TESTING: {feature_context}
REPO: {repo_path}
STEPS: run_pytest_tests -> update_feature_status (done if pass, testing if fail)""")
        
        # Add instruction to messages
        modified_state = dict(state)
        modified_state["messages"] = list(state.get("messages", [])) + [instruction]

        # Execute testing agent with modified state
        result = await test_graph.ainvoke(modified_state)

        # Sync feature_list from disk
        result = sync_feature_list_from_disk(result, repo_path)

        # Log progress - check test result
        feature_list = result.get("feature_list", [])
        if current_feature:
            # Find updated feature status
            for f in feature_list:
                if f.get("id") == feature_id:
                    status = f.get("status")
                    if status == "done":
                        log_progress(repo_path, "testing", feature_id, "passed",
                                   f"Tests passed for {f.get('title', 'feature')}")
                    else:
                        log_progress(repo_path, "testing", feature_id, "failed",
                                   f"Tests failed for {f.get('title', 'feature')} (attempt {f.get('attempts', 0)})")
                    break

        # PHASE 4.1: Trim conversation history to max 4000 tokens
        from src.tools.message_trimmer import trim_conversation_history
        result["messages"] = trim_conversation_history(result["messages"], max_tokens=4000)

        # CRITICAL: Keep the current_feature we were testing
        # The feature status may have changed to "done" or stayed as "testing"
        feature_list = result.get("feature_list", [])
        
        # Find the feature we were testing (by ID from original current_feature)
        if current_feature:
            for f in feature_list:
                if f.get("id") == feature_id:
                    result["current_feature"] = f
                    new_status = f.get("status", "unknown")
                    attempts = f.get("attempts", 0)
                    if new_status == "done":
                        print(f"[OK] Feature {feature_id} passed tests -> done")
                    else:
                        print(f"[WARN]  Feature {feature_id} still in {new_status} (attempts: {attempts})")
                    break
        else:
            # Fallback: find any done feature that doesn't have QA yet
            done_features = [f for f in feature_list if f.get("status") == "done"]
            if done_features:
                result["current_feature"] = done_features[0]
                print(f"[OK] Set current_feature to done: {done_features[0]['id']}")

        # SELECTIVE CLEANUP: Remove ToolMessages to reduce tokens (Phase 3.3)
        messages_before = len(result.get("messages", []))
        result["messages"] = cleanup_tool_messages(result["messages"], keep_last_n_tools=1)
        messages_after = len(result.get("messages", []))
        print(f"[CLEANUP] SELECTIVE CLEANUP (testing): {messages_before} -> {messages_after} messages")

        # PHASE 4.4: Track token usage for optimization insights
        from src.utils.token_counter import count_messages_tokens, log_token_usage
        token_count = count_messages_tokens(result.get("messages", []))
        current_feature_id = result.get("current_feature", {}).get("id", "unknown")
        log_token_usage("testing", current_feature_id, token_count, repo_path, len(result.get("messages", [])))

        return result

    async def qa_doc_node(state: AppBuilderState) -> AppBuilderState:
        """Wrapper for QA/Doc agent graph"""
        repo_path = state.get("repo_path", "")
        current_feature = state.get("current_feature")
        feature_id = current_feature.get("id", "unknown") if current_feature else "unknown"
        feature_title = current_feature.get("title", "Feature") if current_feature else "Feature"

        print(f"\n{'='*60}")
        print(f"[QA] QA/DOC AGENT STARTING")
        print(f"   Feature: {feature_id} - {feature_title}")
        print(f"{'='*60}\n")

        # Get compact context from previous agents
        feature_context = create_feature_context_message(state)

        # Add instruction message with injected context
        instruction = SystemMessage(content=f"""QA/DOC: {feature_context}
REPO: {repo_path}
STEPS: run_all_quality_checks -> update_changelog -> generate_feature_documentation -> update_qa_progress_log""")
        
        # Add instruction to messages
        modified_state = dict(state)
        modified_state["messages"] = list(state.get("messages", [])) + [instruction]

        # Execute QA/Doc agent with modified state
        result = await qa_doc_graph.ainvoke(modified_state)

        # CRITICAL: Sync feature_list from disk after agent execution
        # QA agent calls update_feature_status to mark feature as "done"
        result = sync_feature_list_from_disk(result, repo_path)

        # Log progress
        if current_feature:
            log_progress(repo_path, "qa_doc", feature_id, "documented",
                        f"QA and documentation completed for {current_feature.get('title', 'feature')}")

        # PHASE 4.1: Trim conversation history to max 4000 tokens
        from src.tools.message_trimmer import trim_conversation_history
        result["messages"] = trim_conversation_history(result["messages"], max_tokens=4000)

        # Set gitops_mode to "feature" for next GitOps run
        result["gitops_mode"] = "feature"

        # SELECTIVE CLEANUP: Remove ToolMessages to reduce tokens (Phase 3.3)
        messages_before = len(result.get("messages", []))
        result["messages"] = cleanup_tool_messages(result["messages"], keep_last_n_tools=1)
        messages_after = len(result.get("messages", []))
        print(f"[CLEANUP] SELECTIVE CLEANUP (qa_doc): {messages_before} -> {messages_after} messages")

        # PHASE 4.4: Track token usage for optimization insights
        from src.utils.token_counter import count_messages_tokens, log_token_usage
        token_count = count_messages_tokens(result.get("messages", []))
        current_feature_id = result.get("current_feature", {}).get("id", "unknown")
        log_token_usage("qa_doc", current_feature_id, token_count, repo_path, len(result.get("messages", [])))

        return result

    # Add agent nodes to the graph
    workflow.add_node("initializer", initializer_node)
    workflow.add_node("gitops", gitops_node)
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
            "gitops": "gitops",
            "coding": "coding",  # For resume mode (project in progress)
            "END": END
        }
    )

    workflow.add_conditional_edges(
        "gitops",
        route_after_gitops,
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
            "gitops": "gitops",  # Go to GitOps after QA
            "END": END
        }
    )

    return workflow


__all__ = ["create_workflow"]
