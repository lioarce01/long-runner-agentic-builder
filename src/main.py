"""
Multi-Agent Software Builder - Main Application

Entry point for the generic software builder that can create
ANY type of application using 4 specialized AI agents.

Compatible with:
- LangChain 1.1.0 (Nov 24, 2025)
- LangGraph 1.0.4 (Nov 25, 2025)
- langgraph-checkpoint-postgres 3.0.1

Usage:
    python src/main.py <project_name> <project_description>

Examples:
    python src/main.py chatbot-clone "Build a chatbot like Claude/ChatGPT"
    python src/main.py ecommerce-mvp "Build an e-commerce site with cart and checkout"
    python src/main.py rest-api "Build a REST API for task management"
"""

import asyncio
import os
import signal
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from src.checkpointing.factory import CheckpointerFactory, get_checkpointer
from src.workflow.orchestrator import create_workflow
from src.state.schemas import AppBuilderState
from src.utils.logging import setup_logging

# Load environment - Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
env_file = PROJECT_ROOT / ".env"
load_dotenv(env_file)

# Check if .env was loaded
env = os.getenv("ENVIRONMENT", "development")

# Setup logging
logger = setup_logging()


class SoftwareBuilderApp:
    """
    Main application with lifecycle management

    This class manages the multi-agent workflow for building
    any type of software application.
    """

    def __init__(self):
        self.workflow = None
        self.app = None
        self.running = True

    async def startup(self):
        """Initialize all components"""
        logger.info("🚀 Starting Multi-Agent Software Builder...")
        logger.info(f"   Environment: {env}")
        logger.info(f"   LangChain 1.1.0 | LangGraph 1.0.4")

        # Initialize checkpointer
        checkpointer = await get_checkpointer()

        # Create workflow (now async to load MCP tools)
        logger.info("📊 Creating multi-agent workflow...")
        self.workflow = await create_workflow()
        self.app = self.workflow.compile(checkpointer=checkpointer)

        logger.info("✅ Application ready\n")

    async def shutdown(self):
        """Cleanup resources"""
        logger.info("\n🛑 Shutting down gracefully...")
        await CheckpointerFactory.close()
        logger.info("✅ Shutdown complete")

    async def run(self, project_name: str, project_description: str):
        """
        Run the multi-agent system to build ANY software application

        Args:
            project_name: Name/slug for the project (e.g., "chatbot-clone", "ecommerce-mvp")
            project_description: Detailed description of what to build

        The system will:
        1. Initialize repository and generate features
        2. Implement features one by one
        3. Test each feature
        4. Review code quality
        5. Update documentation
        6. Repeat until all features are done
        """
        # Generate paths dynamically
        output_base = os.getenv("OUTPUT_DIR", "./output")
        repo_path = os.path.join(output_base, project_name)

        thread_id = CheckpointerFactory.get_thread_id(project_name)

        config = {
            "configurable": {
                "thread_id": thread_id
            },
            # Increase recursion limit for projects with many features
            # Each feature needs ~4 steps (coding → testing → qa → gitops)
            # Default 25 is too low for 7+ features
            "recursion_limit": 150
        }

        # Initialize state
        initial_state: AppBuilderState = {
            "messages": [HumanMessage(content=project_description)],
            "project_metadata": {
                "name": project_name,
                "type": "unknown",  # Will be inferred by Initializer
                "domain": "unknown",
                "tech_stack": {
                    "backend": [],
                    "frontend": None,
                    "database": None,
                    "testing": [],
                    "deployment": None
                },
                "estimated_features": 0
            },
            "repo_path": repo_path,
            "project_name": project_name,
            "feature_list": [],
            "current_feature": None,
            "git_context": {
                "current_branch": "main",
                "last_commit_sha": "",
                "uncommitted_changes": False,
                "snapshot_tag": None
            },
            "test_context": {
                "last_run_timestamp": "",
                "passed_tests": 0,
                "failed_tests": 0,
                "coverage_percentage": 0.0,
                "failure_details": None,
                "last_result": None
            },
            "phase": "init",
            "retry_count": 0,
            "max_retries": 3,
            "init_script_path": None,
            "progress_log": []
        }

        logger.info(f"📝 Project: {project_description}")
        logger.info(f"📂 Output: {repo_path}")
        logger.info(f"🔖 Thread ID: {thread_id}\n")
        logger.info("=" * 80)
        logger.info("")

        try:
            # Stream workflow execution
            async for chunk in self.app.astream(initial_state, config):
                self._print_chunk(chunk)

                if not self.running:
                    logger.warning("\n⚠️  Interrupted by user")
                    break

        except KeyboardInterrupt:
            logger.warning("\n⚠️  Interrupted by user")
        except Exception as e:
            logger.error(f"\n❌ Error during execution: {e}")
            raise

        logger.info("\n" + "=" * 80)
        logger.info("✅ Multi-agent workflow completed!")

    def _print_chunk(self, chunk: dict):
        """
        Pretty print workflow updates with detailed logging

        Args:
            chunk: Workflow chunk from LangGraph stream
        """
        for node_name, node_output in chunk.items():
            # Print agent activity
            if node_name in ["initializer", "coding", "testing", "qa_doc"]:
                logger.info(f"\n{'='*60}")
                logger.info(f"🤖 {node_name.upper()} AGENT STARTED")
                logger.info("="*60)

            # Print messages from agents
            if isinstance(node_output, dict):
                if "messages" in node_output and node_output["messages"]:
                    latest = node_output["messages"][-1]

                    # Handle LangChain message objects (AIMessage, HumanMessage, etc.)
                    if hasattr(latest, "type"):
                        role = latest.type.upper()  # "ai", "human", "system"
                        content = latest.content if hasattr(latest, "content") else ""

                        # Check for tool calls in the message
                        if hasattr(latest, "tool_calls") and latest.tool_calls:
                            logger.info(f"\n🔧 TOOL CALLS:")
                            for tool_call in latest.tool_calls:
                                tool_name = tool_call.get("name", "unknown")
                                logger.info(f"   → {tool_name}")

                        # Check for tool results
                        if hasattr(latest, "name") and latest.name:
                            # This is a ToolMessage
                            logger.info(f"\n✅ Tool Result: {latest.name}")
                            result_preview = str(content)[:100]
                            logger.info(f"   {result_preview}...")
                    else:
                        # Fallback for dict-style messages
                        role = latest.get("role", "agent").upper()
                        content = latest.get("content", "")

                    # Print AI responses (not tool results)
                    if content and role == "AI":
                        logger.info(f"\n💭 Agent: {content[:200]}...")

                # Print state updates
                if "current_feature" in node_output and node_output["current_feature"]:
                    feature = node_output["current_feature"]
                    logger.info(f"\n📌 Current Feature:")
                    logger.info(f"   ID: {feature['id']}")
                    logger.info(f"   Title: {feature['title']}")
                    logger.info(f"   Status: {feature.get('status', 'unknown')}")
                    logger.info(f"   Priority: {feature.get('priority', 'unknown')}")

                if "phase" in node_output:
                    logger.info(f"\n📍 Phase: {node_output['phase']}")

                # Print feature list stats
                if "feature_list" in node_output and node_output["feature_list"]:
                    features = node_output["feature_list"]
                    pending = sum(1 for f in features if f.get("status") == "pending")
                    in_progress = sum(1 for f in features if f.get("status") == "in_progress")
                    done = sum(1 for f in features if f.get("status") == "done")
                    failed = sum(1 for f in features if f.get("status") == "failed")

                    logger.info(f"\n📊 Progress:")
                    logger.info(f"   Total: {len(features)} features")
                    logger.info(f"   ✅ Done: {done}")
                    logger.info(f"   🔄 In Progress: {in_progress}")
                    logger.info(f"   ⏳ Pending: {pending}")
                    if failed > 0:
                        logger.info(f"   ❌ Failed: {failed}")

                # Print git context updates
                if "git_context" in node_output:
                    git_ctx = node_output["git_context"]
                    if git_ctx.get("last_commit_sha"):
                        logger.info(f"\n🔖 Last commit: {git_ctx['last_commit_sha'][:7]}")

                # Print test results
                if "test_context" in node_output:
                    test_ctx = node_output["test_context"]
                    if test_ctx.get("last_result"):
                        result = test_ctx["last_result"]
                        passed = result.get("passed", False)
                        status_icon = "✅" if passed else "❌"
                        logger.info(f"\n{status_icon} Tests: {test_ctx.get('passed_tests', 0)}/{test_ctx.get('passed_tests', 0) + test_ctx.get('failed_tests', 0)} passed")


async def main():
    """Main entry point"""
    # Parse command-line arguments
    if len(sys.argv) < 3:
        print("❌ Error: Missing required arguments\n")
        print("Usage: python src/main.py <project_name> <project_description>\n")
        print("Examples:")
        print('  python src/main.py chatbot-clone "Build a chatbot like Claude/ChatGPT"')
        print('  python src/main.py ecommerce-mvp "Build an e-commerce site with cart and checkout"')
        print('  python src/main.py rest-api "Build a REST API for task management with PostgreSQL"')
        print('  python src/main.py blog-platform "Build a blog with markdown editor and SEO"')
        sys.exit(1)

    project_name = sys.argv[1]
    project_description = sys.argv[2]

    app = SoftwareBuilderApp()

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        app.running = False
        logger.warning("\n⚠️  Shutting down gracefully...")

    # Handle Ctrl+C gracefully (Windows compatible)
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)

    try:
        await app.startup()

        # Run the multi-agent system
        await app.run(
            project_name=project_name,
            project_description=project_description
        )

    finally:
        await app.shutdown()


if __name__ == "__main__":
    # Fix for Windows - psycopg requires SelectorEventLoop
    import sys
    import selectors

    if sys.platform == 'win32':
        # Use SelectorEventLoop on Windows for psycopg compatibility
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run the async main function
    asyncio.run(main())
