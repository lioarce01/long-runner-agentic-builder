# Interactive CLI for Multi-Agent Builder

A full-featured Terminal User Interface (TUI) built with Textual for managing and monitoring long-running multi-agent software builds.

## Features

- **Real-time Feature Board**: Live table showing feature status with color-coded indicators
- **Streaming Logs**: Real-time log viewer with agent-specific color coding
- **Token Usage Chart**: Visual bar chart showing token consumption by agent
- **Live Status Header**: Project name, current phase, progress summary, and elapsed time
- **Keyboard Controls**: Pause/Resume workflow execution with keyboard shortcuts
- **Graceful Shutdown**: Clean exit with workflow state preservation

## Prerequisites

```bash
# Ensure you're using the virtual environment
cd backend
source venv/Scripts/activate  # Windows: venv\Scripts\activate
```

## Installation

Dependencies are already listed in `pyproject.toml`. The CLI requires:
- `textual==0.87.0` - Terminal UI framework
- `rich>=13.9.0` - Rich text formatting (already installed)

To install Textual:
```bash
venv/Scripts/python -m pip install textual==0.87.0
```

## Usage

### Starting the CLI

```bash
# From the backend directory with venv activated
python cli_main.py

# Or using the venv python directly
venv/Scripts/python cli_main.py
```

### Setup Screen

When you launch the CLI, you'll see the setup screen:

1. **Project Name**: Enter a unique project name (alphanumeric, hyphens, underscores only)
2. **Project Description**: Describe what you want to build (minimum 10 characters)
3. Press **Enter** or click **Start Build** to begin

### Main Dashboard

The dashboard shows:

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🚀 my-project  |  Implementing  |  3/10 features  |  ⏱ 00:15:42    │
├─────────────────────────────────────┬───────────────────────────────┤
│ Feature Board (75%)                 │ Token Chart (25%)             │
│ ┌─────────────────────────────────┐ │ ┌─────────────────────────┐ │
│ │ ID │ Title │ Status │ Attempts │ │ │ Total: 15,234          │ │
│ │ f1 │ Auth  │ ✓ done │    1     │ │ │                         │ │
│ │ f2 │ API   │ → code │    1     │ │ │ CODE ████████ 8,000    │ │
│ └─────────────────────────────────┘ │ │ TEST ████ 5,000        │ │
│                                      │ └─────────────────────────┘ │
│ Log Viewer (40%)                     │                             │
│ ┌─────────────────────────────────┐ │                             │
│ │ [10:23:15] [CODE] Implementing  │ │                             │
│ │ [10:23:18] [TEST] Running tests │ │                             │
│ └─────────────────────────────────┘ │                             │
└─────────────────────────────────────┴───────────────────────────────┘
```

### Keyboard Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| **Q** | Quit | Exit application (graceful shutdown) |
| **P** | Pause/Resume | Toggle workflow execution |
| **Ctrl+C** | Interrupt | Force quit (use Q for graceful shutdown) |

### Design & Theme

**Minimalist Dark Aesthetic** - Inspired by Vercel and Supabase:
- Pure black backgrounds (`#000000`)
- Subtle gray borders (`#1a1a1a`, `#222222`)
- Muted accent colors for sophistication
- High contrast for readability
- Clean, minimal visual hierarchy

**Status Colors:**
- 🟢 **done** - Teal green (#00D9A3) - Supabase-inspired
- 🟡 **testing** - Gold (#FFD700)
- 🔵 **in_progress** / **coding** - Blue (#3B82F6)
- ⚫ **pending** - Dark gray (#666666)
- 🔴 **failed** - Soft red (#FF6B6B)
- 🔴 **blocked** - Soft red (#FF6B6B)

**Agent Colors:**
- 🟣 **INIT** - Purple (#A78BFA)
- 🔵 **CODE** - Blue (#3B82F6)
- 🟡 **TEST** - Gold (#FFD700)
- 🟢 **GIT** - Teal (#00D9A3)
- 🔵 **QA** - Light Blue (#60A5FA)

## How It Works

### Architecture

The CLI wraps the existing multi-agent workflow without modifying it:

1. **Setup Screen** collects project info
2. **WorkflowRunner** starts the workflow in a background asyncio task
3. **MainScreen** polls disk files every 500ms for updates
4. **Components** render data from JSON files:
   - `feature_list.json` - Feature statuses
   - `progress_log.json` - Action history
   - `token_usage.json` - Token analytics

### Data Flow

```
Workflow (orchestrator.py)
    ↓ writes to disk
State Files (*.json)
    ↓ polled every 500ms
CLI Components (FeatureTable, LogViewer, etc.)
    ↓ render
Terminal UI
```

### Pause/Resume

- **Pause**: Sets an asyncio Event flag that blocks the workflow stream
- **Resume**: Clears the flag, allowing workflow to continue
- State is preserved during pause (checkpointing continues to work)

### Graceful Shutdown

When you press **Q**:
1. CLI signals workflow to stop
2. Workflow completes current chunk (up to 5 seconds)
3. State is checkpointed
4. CLI exits cleanly

## File Locations

### Source Files

```
backend/
├── cli_main.py                        # CLI entry point
└── src/
    └── cli/
        ├── app.py                     # BuilderApp (main controller)
        ├── styles.tcss                # Textual CSS styling
        ├── components/
        │   ├── feature_table.py       # Feature board table
        │   ├── log_viewer.py          # Log streaming viewer
        │   ├── token_chart.py         # Token usage chart
        │   └── status_header.py       # Status header widget
        ├── screens/
        │   ├── setup_screen.py        # Project setup form
        │   └── main_screen.py         # Main dashboard
        └── runner/
            └── workflow_runner.py     # Background workflow executor
```

### Output Files

The CLI reads from the output directory:

```
output/
└── {project-name}/
    ├── feature_list.json      # Feature statuses
    ├── progress_log.json      # Action history
    ├── token_usage.json       # Token analytics
    └── ... (project files)
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'textual'`:
```bash
cd backend
venv/Scripts/python -m pip install textual==0.87.0
```

### UI Not Updating

The UI polls files every 500ms. If updates seem slow:
- Check that the workflow is actually running (not paused)
- Verify output files exist in `output/{project-name}/`
- Look for errors in the log viewer

### Workflow Won't Stop

If pressing **Q** doesn't exit:
- Use **Ctrl+C** for force quit
- Check for errors in the console
- Workflow might be stuck waiting for external input

### Layout Issues

If the UI looks broken:
- Resize your terminal (minimum 80x24 recommended)
- Check terminal color support (256-color or better)
- Try a different terminal emulator

## Development

### Running Tests

```bash
cd backend
venv/Scripts/python -m pytest tests/
```

### Checking Syntax

```bash
cd backend
venv/Scripts/python -m py_compile cli_main.py
venv/Scripts/python -m py_compile src/cli/**/*.py
```

### Style Guide

The CLI follows the project's global style guide:
- `snake_case` for functions and variables
- `PascalCase` for classes
- Comprehensive docstrings
- Type hints for all public methods

## Known Limitations

1. **Single Project**: Only one project can run at a time
2. **Skip Feature**: Not implemented (requires orchestrator changes)
3. **No Replay**: Can't replay past builds from checkpoints (future enhancement)
4. **Windows-Specific**: Some paths/commands are Windows-specific

## Future Enhancements

- [ ] Multiple project tabs
- [ ] Replay mode for viewing past builds
- [ ] Export logs/reports to file
- [ ] Agent-specific log filtering
- [ ] Feature dependency graph visualization
- [ ] Dark/light theme toggle

## Support

For issues or questions:
1. Check the main project README
2. Review the implementation plan: `interactive-cli-implementation-plan.md`
3. Inspect logs in `output/{project-name}/progress_log.json`

---

**Built with [Textual](https://textual.textualize.io/) - Modern Python TUI Framework**
