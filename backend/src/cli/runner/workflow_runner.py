"""
Background Workflow Runner for CLI

Runs the multi-agent workflow in background asyncio task with pause/resume support.
"""

import asyncio
import os
import logging
from typing import Optional
from src.workflow.orchestrator import create_workflow
from src.checkpointing.factory import CheckpointerFactory
from src.state.schemas import AppBuilderState
from langchain_core.messages import HumanMessage

# Configure logging
logger = logging.getLogger(__name__)


class WorkflowRunner:
    """
    Background workflow runner for CLI.

    Runs workflow in asyncio task, allows pause/resume.
    Does NOT modify orchestrator logic.
    """

    _pause_flag = asyncio.Event()
    _running = False
    _task: Optional[asyncio.Task] = None
    _error: Optional[Exception] = None
    _should_stop = False

    def __init__(self, project_name: str, description: str, screen):
        self.project_name = project_name
        self.description = description
        self.screen = screen  # MainScreen reference for callbacks
        WorkflowRunner._pause_flag.set()  # Not paused initially
        WorkflowRunner._should_stop = False

    async def start(self):
        """Start workflow in background task"""
        WorkflowRunner._task = asyncio.create_task(self._run())

    async def _run(self):
        """
        Run workflow (identical to main.py logic) with error handling
        """
        WorkflowRunner._running = True
        WorkflowRunner._error = None

        try:
            # Create workflow (same as main.py)
            # Try PostgreSQL first, fall back to NO checkpointer for testing
            try:
                checkpointer = await CheckpointerFactory.get_checkpointer()
                logger.info("[OK] Using PostgreSQL checkpointer")
            except Exception as e:
                logger.warning(f"[WARN] PostgreSQL not available, running WITHOUT checkpointing")
                logger.warning(f"   (State won't persist between runs)")
                checkpointer = None  # Run without checkpointer

            workflow = await create_workflow()

            if checkpointer:
                app = workflow.compile(checkpointer=checkpointer)
            else:
                app = workflow.compile()  # No checkpointer

            # Initialize state (same as main.py)
            repo_path = os.path.join(os.getenv("OUTPUT_DIR", "./output"), self.project_name)

            # Config with or without checkpointing
            if checkpointer:
                thread_id = CheckpointerFactory.get_thread_id(self.project_name)
                config = {
                    "configurable": {"thread_id": thread_id},
                    "recursion_limit": 150
                }
            else:
                config = {
                    "recursion_limit": 150
                }

            # Create repo directory if it doesn't exist
            os.makedirs(repo_path, exist_ok=True)

            # Initialize state (same structure as main.py)
            initial_state: AppBuilderState = {
                "messages": [HumanMessage(content=self.description)],
                "project_metadata": {
                    "name": self.project_name,
                    "type": "unknown",  # Will be inferred by initializer
                    "domain": "unknown",
                    "tech_stack": {},
                    "estimated_features": 0
                },
                "repo_path": repo_path,
                "project_name": self.project_name,
                "feature_list": [],
                "current_feature": None,
                "git_context": {
                    "current_branch": "main",
                    "last_commit_sha": None,
                    "uncommitted_changes": False,
                    "snapshot_tag": None
                },
                "test_context": {
                    "last_run_timestamp": None,
                    "passed_tests": 0,
                    "failed_tests": 0,
                    "coverage_percentage": None,
                    "failure_details": [],
                    "last_result": None
                },
                "phase": "init",
                "retry_count": 0,
                "max_retries": 3,
                "gitops_mode": None,
                "recovery_features": None,
                "recovery_needed": None,
                "original_prompt": self.description,
                "progress_log": []
            }

            # Stream workflow execution
            logger.info(f"[START] Starting workflow stream...")
            chunk_count = 0

            async for chunk in app.astream(initial_state, config):
                chunk_count += 1
                logger.info(f"[CHUNK] Chunk {chunk_count}: {list(chunk.keys())}")

                # Check if stop requested
                if WorkflowRunner._should_stop:
                    logger.info("Workflow stop requested, exiting gracefully")
                    break

                # Check pause flag
                await WorkflowRunner._pause_flag.wait()

                # Chunks automatically update disk files
                # CLI polls files for UI updates (decoupled)

            logger.info(f"[OK] Workflow completed successfully ({chunk_count} chunks processed)")

        except asyncio.CancelledError:
            logger.info("Workflow task cancelled, shutting down gracefully")
            WorkflowRunner._error = None
        except Exception as e:
            logger.error(f"Workflow error: {e}", exc_info=True)
            WorkflowRunner._error = e
        finally:
            WorkflowRunner._running = False

    @classmethod
    def pause(cls):
        """Pause workflow execution"""
        cls._pause_flag.clear()
        logger.info("Workflow paused")

    @classmethod
    def resume(cls):
        """Resume workflow execution"""
        cls._pause_flag.set()
        logger.info("Workflow resumed")

    @classmethod
    def is_running(cls) -> bool:
        """Check if workflow is running"""
        return cls._running

    @classmethod
    def get_error(cls) -> Optional[Exception]:
        """Get the last error that occurred"""
        return cls._error

    @classmethod
    async def stop(cls):
        """
        Stop workflow gracefully

        Signals the workflow to stop and waits for it to finish.
        """
        logger.info("Requesting workflow stop")
        cls._should_stop = True

        if cls._task and not cls._task.done():
            try:
                # Give workflow 5 seconds to stop gracefully
                await asyncio.wait_for(cls._task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Workflow didn't stop gracefully, cancelling task")
                cls._task.cancel()
                try:
                    await cls._task
                except asyncio.CancelledError:
                    pass

        cls._running = False
        logger.info("Workflow stopped")

    @classmethod
    def reset(cls):
        """Reset workflow runner state"""
        cls._running = False
        cls._task = None
        cls._error = None
        cls._should_stop = False
        cls._pause_flag.set()
