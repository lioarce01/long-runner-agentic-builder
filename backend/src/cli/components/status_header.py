"""
Status Header Widget

Displays project name, current status, and elapsed time.
"""

import os
import json
from datetime import datetime
from typing import Optional
from textual.widgets import Static
from rich.text import Text


class StatusHeader(Static):
    """
    Status header showing:
    - Project name
    - Current phase/status
    - Elapsed time
    - Progress summary (X/Y features completed)
    """

    def __init__(self, project_name: str, **kwargs):
        super().__init__(**kwargs)
        self.project_name = project_name
        self.start_time = datetime.now()

    def on_mount(self) -> None:
        """Initialize header"""
        self.update(self._render_header("Initializing", 0, 0, 0))

    async def refresh_from_disk(self) -> None:
        """
        Read state files and update header
        """
        repo_path = os.path.join(
            os.getenv("OUTPUT_DIR", "./output"),
            self.project_name
        )
        feature_path = os.path.join(repo_path, "feature_list.json")

        # Default values
        phase = "Running"
        total_features = 0
        done_features = 0
        failed_features = 0

        if os.path.exists(feature_path):
            try:
                with open(feature_path, "r", encoding="utf-8") as f:
                    features = json.load(f)

                total_features = len(features)
                done_features = sum(1 for f in features if f.get("status") == "done")
                failed_features = sum(1 for f in features if f.get("status") == "failed")

                # Determine phase from feature statuses
                if done_features == total_features and total_features > 0:
                    phase = "Completed"
                elif failed_features > 0:
                    phase = "Issues Detected"
                elif any(f.get("status") == "testing" for f in features):
                    phase = "Testing"
                elif any(f.get("status") in ["coding", "in_progress"] for f in features):
                    phase = "Implementing"
                else:
                    phase = "Planning"

            except (json.JSONDecodeError, Exception):
                phase = "Error Reading State"

        self.update(self._render_header(phase, total_features, done_features, failed_features))

    def _render_header(
        self,
        phase: str,
        total: int,
        done: int,
        failed: int
    ) -> Text:
        """
        Render header text with status information

        Args:
            phase: Current workflow phase
            total: Total number of features
            done: Number of completed features
            failed: Number of failed features

        Returns:
            Rich Text object with formatted header
        """
        # Calculate elapsed time
        elapsed = datetime.now() - self.start_time
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        elapsed_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Build header text
        header = Text()

        # Project name
        header.append(self.project_name, style="#ededed bold")
        header.append("  ·  ", style="#333333")

        # Phase with color coding
        phase_style = self._get_phase_style(phase)
        header.append(phase, style=phase_style)
        header.append("  ·  ", style="#333333")

        # Progress
        if total > 0:
            progress_text = f"{done}/{total}"
            if failed > 0:
                progress_text += f" ({failed} failed)"
                progress_style = "#FF6B6B"
            elif done == total:
                progress_style = "#00D9A3"
            else:
                progress_style = "#999999"

            header.append(progress_text, style=progress_style)
            header.append("  ·  ", style="#333333")

        # Elapsed time
        header.append(elapsed_str, style="#666666")

        return header

    def _get_phase_style(self, phase: str) -> str:
        """
        Get Rich style for phase text

        Args:
            phase: Phase name

        Returns:
            Rich style string
        """
        phase_styles = {
            "initializing": "#FFD700",
            "planning": "#A78BFA",
            "implementing": "#3B82F6",
            "coding": "#3B82F6",
            "testing": "#FFD700",
            "completed": "#00D9A3",
            "issues detected": "#FF6B6B",
            "error reading state": "#FF6B6B",
            "running": "#60A5FA",
        }

        return phase_styles.get(phase.lower(), "#999999")
