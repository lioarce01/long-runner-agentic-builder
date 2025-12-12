"""
Main Dashboard Screen

Shows live feature board, logs, and token usage.
"""

from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer
from src.cli.runner.workflow_runner import WorkflowRunner
from src.cli.components import FeatureTable, LogViewer, TokenChart, StatusHeader


class MainScreen(Screen):
    """
    Main dashboard screen

    Layout:
    - Header: Project name, status, elapsed time
    - Main Content (Horizontal Split):
      - Left Panel (75%):
        - Feature Board (60%)
        - Log Viewer (40%)
      - Right Panel (25%):
        - Token Usage Chart
    - Footer: Keyboard shortcuts
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("p", "toggle_pause", "Pause/Resume"),
    ]

    CSS = """
    #main_container {
        height: 100%;
        width: 100%;
    }

    #status_header {
        height: 3;
        padding: 1;
        background: $panel;
        border-bottom: solid $primary;
    }

    #content_horizontal {
        height: 1fr;
        width: 100%;
    }

    #left_panel {
        width: 75%;
        height: 100%;
    }

    #right_panel {
        width: 25%;
        height: 100%;
    }

    #feature_table_container {
        height: 60%;
        border: solid $accent;
        padding: 1;
    }

    #log_viewer_container {
        height: 40%;
        border: solid $accent;
        padding: 1;
        margin-top: 1;
    }

    #token_chart_container {
        height: 100%;
        border: solid $accent;
        padding: 1;
    }

    FeatureTable {
        height: 1fr;
    }

    LogViewer {
        height: 1fr;
    }

    TokenChart {
        height: 1fr;
    }
    """

    def __init__(self, project_name: str, description: str):
        super().__init__()
        self.project_name = project_name
        self.description = description
        self.workflow_runner = None

    def compose(self):
        """Compose the main screen layout with all widgets"""
        yield Header(show_clock=True)

        yield Container(
            # Status header
            Container(
                StatusHeader(self.project_name, id="status_header_widget"),
                id="status_header"
            ),

            # Main content area (horizontal split)
            Horizontal(
                # Left panel (75%) - Features and Logs
                Vertical(
                    Container(
                        FeatureTable(self.project_name, id="feature_table"),
                        id="feature_table_container"
                    ),
                    Container(
                        LogViewer(self.project_name, id="log_viewer"),
                        id="log_viewer_container"
                    ),
                    id="left_panel"
                ),

                # Right panel (25%) - Token chart
                Container(
                    TokenChart(self.project_name, id="token_chart"),
                    id="token_chart_container"
                ),

                id="content_horizontal"
            ),
            id="main_container"
        )

        yield Footer()

    async def on_mount(self) -> None:
        """Start workflow when screen mounts"""
        # Start workflow in background
        self.workflow_runner = WorkflowRunner(
            self.project_name,
            self.description,
            self
        )
        await self.workflow_runner.start()

        # Start periodic UI updates (every 500ms)
        self.set_interval(0.5, self.update_ui)

    async def update_ui(self):
        """
        Periodic UI update (called every 500ms)
        Reads state from disk and updates all widgets
        """
        try:
            # Update status header
            status_header = self.query_one("#status_header_widget", StatusHeader)
            await status_header.refresh_from_disk()

            # Update feature table
            feature_table = self.query_one("#feature_table", FeatureTable)
            await feature_table.refresh_from_disk()

            # Update log viewer
            log_viewer = self.query_one("#log_viewer", LogViewer)
            await log_viewer.refresh_from_disk()

            # Update token chart
            token_chart = self.query_one("#token_chart", TokenChart)
            await token_chart.refresh_from_disk()

            # Check for workflow errors
            error = WorkflowRunner.get_error()
            if error:
                self.app.notify(
                    f"Workflow error: {str(error)[:50]}",
                    severity="error",
                    timeout=10
                )

        except Exception as e:
            # Silently handle errors to prevent UI crashes
            # Errors will be visible in the log viewer
            pass

    async def on_unmount(self) -> None:
        """Clean up when screen is closed"""
        # Stop workflow if still running
        if self.workflow_runner and WorkflowRunner.is_running():
            await WorkflowRunner.stop()
