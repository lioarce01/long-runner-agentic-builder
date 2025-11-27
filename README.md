# Multi-Agent Software Builder

A **generic multi-agent system** that autonomously builds ANY type of software application using 4 specialized AI agents powered by LangChain 1.0 and LangGraph 1.0.

## Features

- **Truly Generic**: Builds chatbots, e-commerce sites, REST APIs, blogs, dashboards, CLIs, and more
- **Dynamic Feature Generation**: LLM generates features tailored to your project description
- **Tech Stack Inference**: Automatically chooses appropriate technologies (FastAPI vs Django, React vs Vue, etc.)
- **Durable Execution**: PostgreSQL checkpointing survives restarts and continues where it left off
- **Model-Agnostic**: Defaults to Gemini 2.0 Flash, supports Claude Sonnet 4.5 and GPT-4o
- **Adaptive Testing**: E2E for web apps, API tests for backends, unit tests for CLIs

## Technology Stack

Built with the latest AI frameworks:

- **LangChain 1.1.0** (Nov 24, 2025) - Agent framework
- **LangGraph 1.0.4** (Nov 25, 2025) - Agent runtime with durable state
- **langgraph-checkpoint-postgres 3.0.1** - PostgreSQL persistence
- **langchain-mcp-adapters 0.1.0+** - Model Context Protocol integration
- **Google Gemini 2.0 Flash** (default) - Free tier LLM
- **PostgreSQL 16** - State persistence
- **Playwright** - E2E testing
- **Python 3.10+** - Required

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Docker (for PostgreSQL)
- Node.js & npm (for Playwright)

### 2. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd app-builder

# Run setup script
chmod +x scripts/setup_dev.sh
./scripts/setup_dev.sh
```

### 3. Configuration

Create `.env.development` (or copy from `.env.production.example`):

```bash
ENVIRONMENT=development
DATABASE_URL=postgresql://langgraph:langgraph_dev_pass@localhost:5432/app_builder
DEFAULT_MODEL=google_genai:gemini-2.0-flash-exp
GOOGLE_API_KEY=your_google_api_key_here
OUTPUT_DIR=./output
```

### 4. Run the System

```bash
# Activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Build any type of application
python src/main.py <project-name> "<project-description>"
```

## Usage Examples

### Build a Chatbot

```bash
python src/main.py chatbot-clone "Build a chatbot like Claude with streaming responses and conversation history"
```

### Build an E-commerce Site

```bash
python src/main.py ecommerce-mvp "Build an e-commerce site with product catalog, shopping cart, and Stripe checkout"
```

### Build a REST API

```bash
python src/main.py task-api "Build a REST API for task management with PostgreSQL, JWT auth, and OpenAPI docs"
```

### Build a Blog Platform

```bash
python src/main.py blog-platform "Build a blog with markdown editor, SEO optimization, and comment system"
```

## How It Works

The system uses 4 specialized agents that work together:

### 1. Initializer Agent

- Analyzes project description
- Infers appropriate tech stack
- Generates tailored feature list (20-50 features)
- Creates git repository
- Generates init.sh script

### 2. Coding Agent

- Selects highest-priority feature
- Implements clean, tested code
- Follows best practices (PEP 8, type hints, docstrings)
- Creates git commit
- Updates progress log

### 3. Test Agent

- Generates appropriate tests (E2E/API/unit based on project type)
- Runs Playwright for web apps, pytest for APIs/CLIs
- Validates acceptance criteria
- Captures screenshots/logs on failure

### 4. QA/Doc Agent

- Runs code quality checks (ruff, mypy)
- Updates documentation (README, CHANGELOG)
- Validates quality gates
- Marks features as done

## Workflow

```
User Input: "Build [ANY APPLICATION]"
    ↓
┌─────────────────────────────────────────┐
│ INITIALIZER AGENT                       │
│ - Analyzes requirements                 │
│ - Infers tech stack                     │
│ - Generates features                    │
│ - Creates repository                    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ CODING AGENT (loops)                    │
│ - Selects next feature                  │
│ - Implements with clean code            │
│ - Runs unit tests                       │
│ - Creates commit                        │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ TEST AGENT                              │
│ - Runs E2E/API/unit tests               │
│ - Validates acceptance criteria         │
│ - Retries on failure (max 3 attempts)   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ QA/DOC AGENT                            │
│ - Code quality checks                   │
│ - Updates documentation                 │
│ - Marks feature complete                │
└─────────────────────────────────────────┘
    ↓
  More features? → Back to CODING AGENT
  All done? → END
```

## Project Structure

```
app-builder/
├── src/
│   ├── agents/           # 4 specialized agents
│   │   ├── initializer.py
│   │   ├── coding.py
│   │   ├── testing.py
│   │   └── qa_doc.py
│   ├── tools/            # LangChain tools
│   │   ├── feature_tools.py
│   │   ├── git_tools.py
│   │   ├── test_tools.py
│   │   └── code_quality.py
│   ├── state/            # TypedDict schemas
│   │   └── schemas.py
│   ├── workflow/         # LangGraph orchestration
│   │   ├── orchestrator.py
│   │   └── routers.py
│   ├── checkpointing/    # PostgreSQL persistence
│   │   └── factory.py
│   ├── mcp/              # Model Context Protocol
│   │   └── client.py
│   ├── utils/            # Utilities
│   │   ├── model.py
│   │   └── logging.py
│   └── main.py           # Entry point
├── config/
│   └── prompts/          # Agent system prompts
│       ├── initializer.txt
│       ├── coding.txt
│       ├── testing.txt
│       └── qa_doc.txt
├── scripts/
│   ├── inspect_checkpoints.py
│   └── setup_dev.sh
├── output/               # Generated applications
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Utility Scripts

### Inspect Checkpoints

```bash
# List all checkpoint threads
python scripts/inspect_checkpoints.py list

# View state for specific thread
python scripts/inspect_checkpoints.py state chatbot-clone::project

# Delete checkpoints for thread
python scripts/inspect_checkpoints.py delete chatbot-clone::project
```

### Database Management

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Stop PostgreSQL
docker-compose down

# Start with PgAdmin (for debugging)
docker-compose --profile debug up -d
# Access PgAdmin at http://localhost:5050
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment (development/production) | development |
| `DATABASE_URL` | PostgreSQL connection string | postgresql://langgraph:langgraph_dev_pass@localhost:5432/app_builder |
| `DEFAULT_MODEL` | LLM model to use | google_genai:gemini-2.0-flash-exp |
| `GOOGLE_API_KEY` | Google API key for Gemini | (required) |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | (optional) |
| `OPENAI_API_KEY` | OpenAI API key for GPT | (optional) |
| `GITHUB_TOKEN` | GitHub token for MCP | (optional) |
| `OUTPUT_DIR` | Output directory for generated apps | ./output |
| `LOG_LEVEL` | Logging level | INFO |

### Model Configuration

The system uses a model-agnostic design with `init_chat_model()` from LangChain 1.0:

```python
# Default (Gemini 2.0 Flash - free tier)
DEFAULT_MODEL=google_genai:gemini-2.0-flash-exp

# Best for coding (Claude Sonnet 4.5)
DEFAULT_MODEL=anthropic:claude-sonnet-4-5-20250929

# Alternative (GPT-4o)
DEFAULT_MODEL=openai:gpt-4o
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/system/

# Run with coverage
pytest --cov=src tests/
```

### Code Quality

```bash
# Linting
ruff check src/

# Type checking
mypy src/

# Formatting
ruff format src/
```

## Troubleshooting

### PostgreSQL Connection Issues

```bash
# Check if PostgreSQL is running
docker ps

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Checkpoint Issues

```bash
# View all checkpoints
python scripts/inspect_checkpoints.py list

# Delete stuck checkpoint
python scripts/inspect_checkpoints.py delete <thread-id>
```

### Model API Issues

```bash
# Verify API keys are set
echo $GOOGLE_API_KEY
echo $ANTHROPIC_API_KEY

# Test model connection
python -c "from src.utils.model import get_model; m = get_model(); print(m.invoke([{'role': 'user', 'content': 'Hello'}]))"
```

## Architecture

### LangChain 1.0 Patterns

- **create_agent()**: Standard agent creation
- **init_chat_model()**: Model-agnostic initialization
- **Middleware**: Context management and summarization
- **TypedDict State**: Required for LangChain 1.0 (no Pydantic)

### LangGraph 1.0 Features

- **Durable Execution**: State persists across restarts
- **Streaming**: Real-time updates from agents
- **Human-in-the-Loop**: Approval gates (future)
- **Memory**: Short-term (checkpoints) + long-term (store)

### MCP Integration

- **Filesystem**: File read/write operations
- **Git**: Repository management
- **GitHub**: PR/issue management (optional)

## Roadmap

- [ ] Human-in-the-loop approval gates
- [ ] LangSmith tracing integration
- [ ] Rate limiting and cost controls
- [ ] Web UI for non-technical users
- [ ] Docker deployment support
- [ ] Multi-language support (currently Python-focused)

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Built with:
- [LangChain](https://github.com/langchain-ai/langchain) 1.1.0
- [LangGraph](https://github.com/langchain-ai/langgraph) 1.0.4
- [MCP](https://modelcontextprotocol.io) (Model Context Protocol)
- Google Gemini 2.0 Flash

---

**Made with LangChain 1.0 and LangGraph 1.0 (November 2025)**
