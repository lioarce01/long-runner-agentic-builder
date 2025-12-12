"""
Token Usage Chart Widget

Displays token consumption by agent as a bar chart.
"""

import os
import json
from typing import Dict, Any
from textual.widgets import Static
from rich.text import Text
from rich.console import Group
from rich.panel import Panel


class TokenChart(Static):
    """
    Token usage chart with bar visualization

    Shows:
    - Total tokens consumed
    - Breakdown by agent
    - Visual bar chart
    """

    def __init__(self, project_name: str, **kwargs):
        super().__init__(**kwargs)
        self.project_name = project_name

    def on_mount(self) -> None:
        """Initialize chart"""
        self.update(self._render_empty_state())

    async def refresh_from_disk(self) -> None:
        """
        Read token_usage.json and update chart
        """
        repo_path = os.path.join(
            os.getenv("OUTPUT_DIR", "./output"),
            self.project_name
        )
        token_path = os.path.join(repo_path, "token_usage.json")

        if not os.path.exists(token_path):
            self.update(self._render_empty_state())
            return

        try:
            with open(token_path, "r", encoding="utf-8") as f:
                token_data = json.load(f)

            # Render chart with data
            self.update(self._render_chart(token_data))

        except json.JSONDecodeError:
            self.update(self._render_error("Failed to parse token_usage.json"))
        except Exception as e:
            self.update(self._render_error(f"Error: {str(e)[:40]}"))

    def _render_empty_state(self) -> Panel:
        """Render empty state when no data available"""
        content = Text("Waiting for tokens...", style="#666666", justify="center")
        return Panel(
            content,
            title="Tokens",
            title_align="left",
            border_style="#1a1a1a",
            padding=(1, 2),
        )

    def _render_error(self, error_msg: str) -> Panel:
        """Render error state"""
        content = Text(error_msg, style="#FF6B6B", justify="center")
        return Panel(
            content,
            title="Tokens",
            title_align="left",
            border_style="#1a1a1a",
            padding=(1, 2),
        )

    def _render_chart(self, token_data: Dict[str, Any]) -> Panel:
        """
        Render token usage chart

        Args:
            token_data: Dictionary with token usage data

        Returns:
            Rich Panel with formatted chart
        """
        total_tokens = token_data.get("total_tokens", 0)
        by_agent = token_data.get("by_agent", {})

        # Create chart lines
        lines = []

        # Total tokens header
        lines.append(Text(f"{total_tokens:,} tokens", style="#ededed"))
        lines.append(Text())  # Blank line

        if not by_agent:
            lines.append(Text("No agent data", style="#666666"))
        else:
            # Calculate max tokens for scaling
            max_tokens = max(by_agent.values()) if by_agent else 1

            # Sort agents by token usage (descending)
            sorted_agents = sorted(
                by_agent.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # Render bar for each agent
            for agent, tokens in sorted_agents:
                lines.append(self._render_bar(agent, tokens, max_tokens, total_tokens))

        # Group all lines
        content = Group(*lines)

        return Panel(
            content,
            title="Tokens",
            title_align="left",
            border_style="#1a1a1a",
            padding=(1, 2),
        )

    def _render_bar(
        self,
        agent: str,
        tokens: int,
        max_tokens: int,
        total_tokens: int
    ) -> Text:
        """
        Render a single bar for an agent

        Args:
            agent: Agent name
            tokens: Tokens consumed by this agent
            max_tokens: Maximum tokens (for scaling)
            total_tokens: Total tokens across all agents

        Returns:
            Rich Text object with formatted bar
        """
        # Calculate bar width (max 20 chars)
        bar_width = int((tokens / max_tokens) * 20) if max_tokens > 0 else 0
        bar_width = max(1, bar_width)  # Minimum 1 char if tokens > 0

        # Calculate percentage
        percentage = (tokens / total_tokens * 100) if total_tokens > 0 else 0

        # Color-code agent bars
        agent_colors = {
            "initializer": "#A78BFA",
            "coding": "#3B82F6",
            "testing": "#FFD700",
            "gitops": "#00D9A3",
            "qa_doc": "#60A5FA",
        }
        color = agent_colors.get(agent.lower(), "#999999")

        # Build bar line
        line = Text()
        line.append(f"{agent.upper()[:8]:<8} ", style="#ededed")
        line.append("█" * bar_width, style=color)
        line.append(f" {tokens:,} ({percentage:.1f}%)", style="#666666")

        return line
