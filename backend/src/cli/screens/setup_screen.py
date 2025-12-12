"""
Setup Screen for Project Configuration

Initial screen that collects project name and description from user.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Input, Button, Label, Static
from textual import on
from textual.validation import Function, ValidationResult, Validator


class ProjectNameValidator(Validator):
    """Validator for project names"""

    def validate(self, value: str) -> ValidationResult:
        """Validate project name"""
        if not value:
            return self.failure("Project name is required")

        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not all(c.isalnum() or c in ('-', '_') for c in value):
            return self.failure("Only alphanumeric, hyphens, and underscores allowed")

        if len(value) < 3:
            return self.failure("Project name must be at least 3 characters")

        return self.success()


class SetupScreen(Screen):
    """
    Setup screen for project configuration

    Asks user for:
    - Project name
    - Project description

    Validates input and starts workflow when submitted.
    """

    CSS = """
    SetupScreen {
        align: center middle;
    }

    #setup_container {
        width: 80;
        height: auto;
        border: solid $primary;
        padding: 2;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .label {
        margin-top: 1;
        margin-bottom: 1;
        color: $text;
    }

    Input {
        margin-bottom: 1;
    }

    #start_button {
        width: 100%;
        margin-top: 2;
    }

    #error_message {
        color: $error;
        text-align: center;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the setup screen layout"""
        yield Container(
            Vertical(
                Label("Multi-Agent Software Builder", id="title"),
                Static("", id="subtitle"),
                Label("Project Name:", classes="label"),
                Input(
                    placeholder="my-awesome-app",
                    id="project_name",
                    validators=[ProjectNameValidator()],
                ),
                Label("Project Description:", classes="label"),
                Input(
                    placeholder="Build a REST API for task management with PostgreSQL",
                    id="project_description",
                ),
                Static("", id="error_message"),
                Button("Start Build", variant="primary", id="start_button"),
                id="setup_container"
            )
        )

    def on_mount(self) -> None:
        """Set up screen on mount"""
        # Focus on project name input
        self.query_one("#project_name", Input).focus()

    @on(Button.Pressed, "#start_button")
    def on_start_button(self, event: Button.Pressed) -> None:
        """Handle start button click"""
        project_name_input = self.query_one("#project_name", Input)
        description_input = self.query_one("#project_description", Input)
        error_message = self.query_one("#error_message", Static)

        project_name = project_name_input.value.strip()
        description = description_input.value.strip()

        # Validate inputs
        if not project_name:
            error_message.update("❌ Project name is required")
            project_name_input.focus()
            return

        if not description:
            error_message.update("❌ Project description is required")
            description_input.focus()
            return

        if len(description) < 10:
            error_message.update("❌ Description must be at least 10 characters")
            description_input.focus()
            return

        # Validation passed - start workflow
        error_message.update("")
        self.app.start_workflow(project_name, description)
        self.dismiss()

    @on(Input.Submitted, "#project_name")
    def on_project_name_submitted(self, event: Input.Submitted) -> None:
        """Move to description input on Enter"""
        self.query_one("#project_description", Input).focus()

    @on(Input.Submitted, "#project_description")
    def on_description_submitted(self, event: Input.Submitted) -> None:
        """Submit form on Enter in description field"""
        self.query_one("#start_button", Button).press()
