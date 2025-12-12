"""
Log Viewer Widget

Real-time log streaming with auto-scroll and color-coded agents.
"""

import os
import json
from typing import List, Dict, Any
from textual.widgets import RichLog
from rich.text import Text


class LogViewer(RichLog):
    """
    Real-time log viewer with auto-scroll

    Displays progress_log.json entries chronologically with:
    - Color-coded agent names
    - Timestamps
    - Action descriptions
    - Feature IDs (when applicable)
    """

    def __init__(self, project_name: str, **kwargs):
        super().__init__(**kwargs)
        self.project_name = project_name
        self.last_log_count = 0
        self.max_lines = 1000

    def on_mount(self) -> None:
        """Configure log viewer on mount"""
        self.auto_scroll = True
        self.wrap = True
        self.highlight = True
        self.markup = True

        # Show initial message
        self.write(Text("Waiting for workflow to start...", style="dim italic"))

    async def refresh_from_disk(self) -> None:
        """
        Read progress_log.json and append new entries

        Only adds logs since last refresh to avoid duplicates.
        """
        repo_path = os.path.join(
            os.getenv("OUTPUT_DIR", "./output"),
            self.project_name
        )
        log_path = os.path.join(repo_path, "progress_log.json")

        if not os.path.exists(log_path):
            return

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                logs = json.load(f)

            # Only process new logs
            if len(logs) > self.last_log_count:
                new_logs = logs[self.last_log_count:]

                for log_entry in new_logs:
                    self._write_log_entry(log_entry)

                self.last_log_count = len(logs)

        except json.JSONDecodeError:
            # Handle corrupted JSON
            if self.last_log_count == 0:
                self.write(Text("⚠ Error: Failed to parse progress_log.json", style="bold red"))
        except Exception as e:
            # Handle other errors
            if self.last_log_count == 0:
                self.write(Text(f"⚠ Error loading logs: {str(e)}", style="bold red"))

    def _write_log_entry(self, log_entry: Dict[str, Any]) -> None:
        """
        Format and write a single log entry

        Args:
            log_entry: Dictionary containing log data
        """
        timestamp = log_entry.get("timestamp", "")
        agent = log_entry.get("agent", "system")
        action = log_entry.get("action", "")
        feature_id = log_entry.get("feature_id", "")
        status = log_entry.get("status", "")

        # Format timestamp (show only time portion)
        time_str = timestamp.split("T")[1][:8] if "T" in timestamp else timestamp[:8]

        # Color-code agent names
        agent_text = self._colorize_agent(agent)

        # Build log line
        log_line = Text()
        log_line.append(f"[{time_str}] ", style="dim")
        log_line.append(agent_text)
        log_line.append(" ")

        # Add action with optional status coloring
        if status:
            action_style = self._get_status_style(status)
            log_line.append(action, style=action_style)
        else:
            log_line.append(action)

        # Add feature ID if present
        if feature_id:
            log_line.append(f" ({feature_id})", style="dim cyan")

        self.write(log_line)

    def _colorize_agent(self, agent: str) -> Text:
        """
        Apply color coding to agent names

        Args:
            agent: Agent name string

        Returns:
            Rich Text object with color styling
        """
        agent_colors = {
            "initializer": ("INIT", "#A78BFA"),
            "coding": ("CODE", "#3B82F6"),
            "testing": ("TEST", "#FFD700"),
            "gitops": ("GIT", "#00D9A3"),
            "qa_doc": ("QA", "#60A5FA"),
            "system": ("SYS", "#999999"),
            "router": ("ROUT", "#A78BFA"),
        }

        display_name, style = agent_colors.get(
            agent.lower(),
            (agent.upper()[:4], "#999999")
        )

        return Text(f"[{display_name}]", style=style)

    def _get_status_style(self, status: str) -> str:
        """
        Get Rich style for status keywords

        Args:
            status: Status string

        Returns:
            Rich style string
        """
        status_styles = {
            "success": "#00D9A3",
            "completed": "#00D9A3",
            "done": "#00D9A3",
            "failed": "#FF6B6B",
            "error": "#FF6B6B",
            "warning": "#FFD700",
            "pending": "#666666",
            "running": "#3B82F6",
            "testing": "#FFD700",
        }

        return status_styles.get(status.lower(), "#ededed")
