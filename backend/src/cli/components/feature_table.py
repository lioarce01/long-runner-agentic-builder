"""
Feature Board Table Widget

Displays features with color-coded statuses in a reactive table.
"""

import os
import json
from typing import List, Dict, Any
from textual.widgets import DataTable
from textual.app import ComposeResult
from rich.text import Text


class FeatureTable(DataTable):
    """
    Feature board table with color-coded statuses

    Columns: ID | Title | Status | Attempts | Priority

    Status Colors:
    - done: green
    - testing: yellow
    - in_progress: blue
    - pending: gray
    - failed: red
    """

    def __init__(self, project_name: str, **kwargs):
        super().__init__(**kwargs)
        self.project_name = project_name
        self.cursor_type = "row"
        self.zebra_stripes = True

    def on_mount(self) -> None:
        """Initialize table structure"""
        self.add_columns("ID", "Title", "Status", "Attempts", "Priority")

    async def refresh_from_disk(self) -> None:
        """
        Read feature_list.json and update table with color-coded statuses
        """
        repo_path = os.path.join(
            os.getenv("OUTPUT_DIR", "./output"),
            self.project_name
        )
        feature_path = os.path.join(repo_path, "feature_list.json")

        if not os.path.exists(feature_path):
            # Show empty state
            if self.row_count == 0:
                self.add_row("—", "Initializing project...", "—", "—", "—")
            return

        try:
            with open(feature_path, "r", encoding="utf-8") as f:
                features = json.load(f)

            # Clear existing rows
            self.clear()

            if not features:
                self.add_row("—", "No features yet", "—", "—", "—")
                return

            # Add feature rows with color-coded statuses
            for feature in features:
                feature_id = feature.get("id", "N/A")
                title = feature.get("title", "Untitled")[:50]  # Truncate long titles
                status = feature.get("status", "pending")
                attempts = str(feature.get("attempts", 0))
                priority = str(feature.get("priority", 0))

                # Apply status colors
                status_text = self._colorize_status(status)

                self.add_row(
                    Text(feature_id, style="bold cyan"),
                    title,
                    status_text,
                    attempts,
                    priority
                )

        except json.JSONDecodeError:
            # Handle corrupted JSON
            self.clear()
            self.add_row("ERROR", "Failed to parse feature_list.json", "—", "—", "—")
        except Exception as e:
            # Handle other errors
            self.clear()
            self.add_row("ERROR", f"Error loading features: {str(e)[:40]}", "—", "—", "—")

    def _colorize_status(self, status: str) -> Text:
        """
        Apply color coding to status text

        Args:
            status: Feature status string

        Returns:
            Rich Text object with color styling
        """
        status_styles = {
            "done": ("✓ done", "#00D9A3"),
            "testing": ("⚡ testing", "#FFD700"),
            "in_progress": ("→ in_progress", "#3B82F6"),
            "coding": ("⚙ coding", "#3B82F6"),
            "pending": ("○ pending", "#666666"),
            "failed": ("✗ failed", "#FF6B6B"),
            "blocked": ("⚠ blocked", "#FF6B6B"),
        }

        display_text, style = status_styles.get(
            status.lower(),
            (f"? {status}", "#999999")
        )

        return Text(display_text, style=style)
