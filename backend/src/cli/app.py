"""
Textual Application for Multi-Agent Builder

Main application controller with keyboard bindings and screen management.
"""

from textual.app import App, ComposeResult
from textual.binding import Binding
from src.cli.screens.setup_screen import SetupScreen
from src.cli.screens.main_screen import MainScreen


class BuilderApp(App):
    """
    Multi-Agent Builder Interactive CLI

    Features:
    - Live feature board with status updates
    - Real-time log streaming
    - Token usage visualization
    - Keyboard controls for pause/resume
    """

    CSS_PATH = "styles.tcss"  # Textual CSS for styling

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("p", "toggle_pause", "Pause/Resume", show=True),
        Binding("s", "skip_feature", "Skip Feature", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.project_name = None
        self.project_description = None
        self.paused = False

    def on_mount(self) -> None:
        """Show setup screen on startup"""
        self.push_screen(SetupScreen())

    def action_quit(self) -> None:
        """Quit the application with graceful shutdown"""
        # Gracefully stop workflow if running
        from src.cli.runner.workflow_runner import WorkflowRunner
        if WorkflowRunner.is_running():
            self.notify("Stopping workflow...", severity="warning")
            # Run async stop in a sync context
            import asyncio
            try:
                asyncio.get_event_loop().run_until_complete(WorkflowRunner.stop())
            except Exception as e:
                self.notify(f"Error stopping workflow: {str(e)}", severity="error")
        self.exit()

    def action_toggle_pause(self) -> None:
        """Toggle pause state"""
        from src.cli.runner.workflow_runner import WorkflowRunner

        if not WorkflowRunner.is_running():
            self.notify("No workflow running", severity="warning")
            return

        self.paused = not self.paused

        # Signal workflow runner to pause/resume
        if self.paused:
            WorkflowRunner.pause()
            self.notify("Workflow paused", severity="information")
        else:
            WorkflowRunner.resume()
            self.notify("Workflow resumed", severity="information")

    def action_skip_feature(self) -> None:
        """
        Skip current feature (mark as failed, move to next)

        Note: This is a best-effort implementation. The workflow is autonomous
        and may not immediately respond to this signal.
        """
        from src.cli.runner.workflow_runner import WorkflowRunner

        if not WorkflowRunner.is_running():
            self.notify("No workflow running", severity="warning")
            return

        # Note: Since the workflow is autonomous and runs in LangGraph,
        # we cannot easily interrupt it mid-feature. This would require
        # modifying the orchestrator to check for skip signals.
        # For now, we just notify the user.
        self.notify(
            "Skip feature requires orchestrator modification",
            severity="warning",
            timeout=5
        )

    def start_workflow(self, project_name: str, description: str):
        """
        Start workflow execution and switch to main screen

        Args:
            project_name: Name of the project to build
            description: Project description for the agents
        """
        self.project_name = project_name
        self.project_description = description

        # Launch main screen
        self.push_screen(MainScreen(project_name, description))
