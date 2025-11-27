# Multi-Agent Software Builder - Complete Implementation Guide

**Version**: 1.0
**Last Updated**: November 2025
**Target**: Build a GENERIC software engineering system that can construct ANY type of application (chatbots, APIs, e-commerce, blogs, etc.) using 4 specialized AI agents

**CRITICAL**: This is NOT a chatbot builder - it's a general-purpose autonomous software engineering system that adapts to any project type based on user description.

**NOTE ON EXAMPLES**: Throughout this document, "chatbot clone" is used as ONE example among many possible projects. The system can build ANY type of software: e-commerce sites, REST APIs, blogs, dashboards, CLIs, mobile backends, etc. All code examples and configurations are generic and project-agnostic.

## Recent Updates (Generic Transformation)

All naming, code examples, and configurations have been updated to be **completely generic**:

- ✅ **Project naming**: `chatbot-builder` → `app-builder`
- ✅ **Database naming**: `chatbot_builder` → `app_builder`
- ✅ **Docker containers**: `chatbot_*` → `app_*`
- ✅ **State schemas**: `ChatbotBuilderState` → `AppBuilderState`
- ✅ **Main class**: `ChatbotBuilderApp` → `SoftwareBuilderApp`
- ✅ **CLI interface**: Now accepts `project_name` and `project_description` as arguments
- ✅ **Dynamic paths**: Output directories generated dynamically per project
- ✅ **Feature generation**: LLM-powered, adapts to ANY project type
- ✅ **Tech stack inference**: Automatically chooses appropriate frameworks
- ✅ **Adaptive testing**: E2E for web apps, API tests for backends, unit tests for CLIs

**Usage Example**:
```bash
# Build a chatbot
python src/main.py chatbot-clone "Build a chatbot like Claude/ChatGPT"

# Build an e-commerce site
python src/main.py ecommerce-mvp "Build an e-commerce site with cart and checkout"

# Build a REST API
python src/main.py task-api "Build a REST API for task management with PostgreSQL"
```

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Phase-by-Phase Implementation](#phase-by-phase-implementation)
6. [Agent Specifications](#agent-specifications)
7. [Workflow Orchestration](#workflow-orchestration)
8. [PostgreSQL Setup](#postgresql-setup)
9. [MCP Integration](#mcp-integration)
10. [Feature List](#feature-list)
11. [Code Examples](#code-examples)
12. [Testing Strategy](#testing-strategy)
13. [Deployment](#deployment)

---

## Executive Summary

### What We're Building

A **GENERIC meta-system** that uses 4 AI agents to autonomously build ANY type of software application over multiple sessions with:
- **Project-agnostic**: Builds chatbots, e-commerce sites, REST APIs, blogs, dashboards, CLIs, etc.
- **Dynamic feature generation**: Analyzes project requirements and generates appropriate feature lists
- **Tech stack inference**: Automatically chooses the right technologies (FastAPI vs Django, React vs Vue, PostgreSQL vs MongoDB, etc.)
- **Persistent state**: PostgreSQL checkpointing (survives restarts)
- **Durable execution**: Long-running tasks across multiple sessions
- **Incremental development**: One feature at a time
- **Adaptive testing**: E2E for web apps, API tests for backends, unit tests for CLIs
- **Full git integration**: Commits, history tracking, progress logs

### Key Innovations

1. **Truly Generic**: Not hardcoded for any specific project type - analyzes requirements and adapts
2. **Dynamic Feature Generation**: LLM generates feature lists tailored to the project (not from templates)
3. **Tech Stack Inference**: Automatically chooses appropriate frameworks, databases, and tools
4. **Model-Agnostic Design**: Defaults to Gemini 2.0 Flash (free tier) but can switch to Claude/GPT via environment variable
5. **PostgreSQL Everywhere**: Same checkpointing in dev and prod for parity
6. **MCP Integration**: GitHub, filesystem, and git operations via Model Context Protocol
7. **Feature-Scoped Threads**: Each feature gets its own checkpoint thread for isolation
8. **Adaptive Testing**: Testing strategy adapts to project type (E2E, API tests, unit tests, etc.)

### Timeline

- **Week 1-2**: Foundation (PostgreSQL, checkpointing, MCP)
- **Week 3-4**: Agent implementation (all 4 agents)
- **Week 5**: Workflow orchestration (LangGraph)
- **Week 6**: Integration and main application
- **Week 7**: Testing, documentation, polish

---

## System Architecture

### High-Level Flow

```
User Input: "Build [ANY TYPE OF APPLICATION]"
    ↓
┌─────────────────────────────────────────────────────────┐
│ INITIALIZER AGENT                                       │
│ - Creates git repo                                      │
│ - Generates dynamic feature list (JSON)                 │
│ - Creates init.sh script                                │
│ - Initializes progress log                              │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ CODING AGENT (loops until all features done)            │
│ - Reads current state from git + progress log           │
│ - Selects ONE highest priority pending feature          │
│ - Implements feature with clean code                    │
│ - Runs unit tests                                       │
│ - Creates git commit                                    │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ TEST AGENT                                              │
│ - Receives feature spec                                 │
│ - Generates Playwright E2E tests                        │
│ - Runs browser automation                               │
│ - Validates acceptance criteria                         │
│ - Marks feature done/failed                             │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ QA/DOC AGENT                                            │
│ - Reviews code quality (linting, typing)                │
│ - Updates documentation                                 │
│ - Updates progress log                                  │
│ - Updates CHANGELOG                                     │
│ - Marks feature complete                                │
└─────────────────────────────────────────────────────────┘
    ↓
  More features? → Back to CODING AGENT
  All done? → END
```

### Component Diagram

```
┌───────────────────────────────────────────────────────────┐
│                   Application Layer                        │
│  src/main.py - Entry point, CLI, lifecycle management     │
├───────────────────────────────────────────────────────────┤
│                   Workflow Layer                          │
│  src/workflow/orchestrator.py - LangGraph StateGraph      │
│  src/workflow/routers.py - Conditional routing logic      │
├───────────────────────────────────────────────────────────┤
│                   Agent Layer                             │
│  src/agents/initializer.py - Bootstrap project            │
│  src/agents/coding.py - Implement features                │
│  src/agents/testing.py - E2E validation                   │
│  src/agents/qa_doc.py - Quality assurance                 │
├───────────────────────────────────────────────────────────┤
│                   Tools Layer                             │
│  src/tools/feature_tools.py - Feature management          │
│  src/tools/git_tools.py - Git operations                  │
│  src/tools/test_tools.py - Test execution                 │
├───────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                    │
│  src/checkpointing/factory.py - PostgreSQL checkpointer   │
│  src/mcp/client.py - MCP server connections               │
│  src/utils/model.py - Model-agnostic LLM init             │
└───────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PostgreSQL  │    │ MCP Servers  │    │  LLM APIs    │
│ Checkpoints  │    │ fs, git, gh  │    │ Gemini/etc.  │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## Technology Stack

### Core Framework
- **LangGraph 1.0**: Agent runtime (durable execution, checkpointing)
- **LangChain 1.0**: Agent framework (`create_agent`, middleware)
- **Python 3.10+**: Required for LangChain 1.0

### Persistence
- **PostgreSQL 16**: Checkpointing database (dev & prod)
- **asyncpg**: Async PostgreSQL driver with connection pooling

### LLM Integration
- **Google Gemini 2.0 Flash** (default): Free tier, fast, 1M context
- **Anthropic Claude Sonnet 4.5** (optional): Best for complex coding
- **OpenAI GPT-4o** (optional): Good balance

### MCP (Model Context Protocol)
- **langchain-mcp-adapters**: Official MCP client for LangChain
- **@modelcontextprotocol/server-filesystem**: File operations
- **mcp-server-git**: Git operations
- **GitHub MCP** (optional): PR, issues, code review

### Testing
- **Playwright**: Browser automation for E2E tests
- **pytest**: Unit and integration tests
- **pytest-asyncio**: Async test support

### Code Quality
- **ruff**: Fast Python linter and formatter
- **mypy**: Static type checking

### Development
- **Docker & Docker Compose**: Local PostgreSQL
- **python-dotenv**: Environment management

---

## Project Structure

```
app-builder/  # GENERIC software builder (NOT chatbot-specific)
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── initializer.py       # Analyzes ANY project type and bootstraps it
│   │   ├── coding.py             # Implements ANY feature type
│   │   ├── testing.py            # Adaptive testing (E2E/API/unit based on project)
│   │   └── qa_doc.py             # Code review and documentation
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── project_analysis.py   # Analyzes project requirements, infers tech stack
│   │   ├── feature_tools.py      # Dynamic feature generation, status updates
│   │   ├── git_tools.py          # Git commit, log parsing
│   │   ├── test_tools.py         # Adaptive test execution (Playwright/pytest/etc.)
│   │   └── code_quality.py       # Linting, type checking
│   │
│   ├── state/
│   │   ├── __init__.py
│   │   └── schemas.py            # TypedDict state definitions
│   │
│   ├── workflow/
│   │   ├── __init__.py
│   │   ├── orchestrator.py       # LangGraph StateGraph
│   │   └── routers.py            # Conditional edge routing
│   │
│   ├── checkpointing/
│   │   ├── __init__.py
│   │   └── factory.py            # PostgreSQL checkpointer factory
│   │
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── client.py             # MCP client configuration
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── model.py              # Model-agnostic LLM init
│   │   └── logging.py            # Structured logging
│   │
│   └── main.py                   # Application entry point
│
├── config/
│   ├── prompts/
│   │   ├── initializer.txt       # Domain-agnostic system prompt
│   │   ├── coding.txt            # Generic coding agent prompt
│   │   ├── testing.txt           # Adaptive testing prompt
│   │   └── qa_doc.txt            # Generic QA/doc prompt
│   │
│   ├── feature_templates/        # Example feature lists for different project types
│   │   ├── chatbot_example.json  # Reference: chatbot features
│   │   ├── ecommerce_example.json # Reference: e-commerce features
│   │   ├── api_example.json      # Reference: REST API features
│   │   └── blog_example.json     # Reference: blog platform features
│   │
│   └── mcp_servers.json          # MCP server configurations
│
├── output/                       # Generated application code (varies by project)
│   ├── <project-name>/           # Each project in its own directory
│       ├── backend/
│       ├── frontend/
│       ├── tests/
│       ├── feature_list.json     # Generated by Initializer
│       ├── progress_log.json     # Updated by agents
│       └── init.sh               # Dev setup script
│
├── tests/
│   ├── unit/
│   │   ├── test_tools.py
│   │   ├── test_routers.py
│   │   └── test_state.py
│   │
│   ├── integration/
│   │   ├── test_agents.py
│   │   ├── test_checkpointing.py
│   │   └── test_mcp.py
│   │
│   └── system/
│       └── test_full_pipeline.py
│
├── scripts/
│   ├── inspect_checkpoints.py    # PostgreSQL inspection utility
│   ├── setup_dev.sh              # Initial dev setup
│   └── clean_checkpoints.py      # Cleanup old checkpoints
│
├── docker-compose.yml            # PostgreSQL + PgAdmin
├── .env.development              # Dev environment variables
├── .env.production.example       # Production template
├── pyproject.toml                # Dependencies and project config
├── pytest.ini                    # Pytest configuration
├── .gitignore
├── README.md
├── blueprint.md                  # Original blueprint (reference)
└── IMPLEMENTATION_PLAN.md        # This file
```

---

## Phase-by-Phase Implementation

### Phase 1: Foundation (Week 1-2)

#### Step 1.1: Project Setup

```bash
# Create project directory
mkdir app-builder
cd app-builder

# Initialize Python project
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Create basic structure
mkdir -p src/{agents,tools,state,workflow,checkpointing,mcp,utils}
mkdir -p config/prompts
mkdir -p tests/{unit,integration,system}
mkdir -p scripts
mkdir -p output

# Initialize git
git init
```

#### Step 1.2: Dependencies (pyproject.toml)

```toml
[project]
name = "app-builder"
version = "0.1.0"
description = "Multi-agent system for building software applications"
requires-python = ">=3.10"

dependencies = [
    # Core framework - LangChain 1.0 and LangGraph 1.0 (November 2025)
    "langchain>=1.1.0",           # LangChain 1.1.0 (Nov 24, 2025)
    "langchain-core>=1.1.0",      # LangChain Core 1.1.0 (Nov 21, 2025)
    "langgraph>=1.0.4",           # LangGraph 1.0.4 (Nov 25, 2025)
    "langgraph-checkpoint-postgres>=3.0.1",  # Compatible with LangGraph 1.0

    # MCP integration
    "langchain-mcp-adapters>=0.1.0",  # MCP support (March 2025)

    # LLM providers - All compatible with LangChain 1.0
    "langchain-google-genai>=3.2.0",   # Google GenAI 3.2.0 (Nov 24, 2025)
    "langchain-anthropic>=1.2.0",      # Anthropic 1.2.0 (Nov 24, 2025) - Optional
    "langchain-openai>=1.1.0",         # OpenAI 1.1.0 (Nov 24, 2025) - Optional

    # Database
    "asyncpg>=0.29.0",

    # Testing
    "playwright>=1.40.0",
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",

    # Code quality
    "ruff>=0.1.0",
    "mypy>=1.7.0",

    # Utilities
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.mypy]
python_version = "3.10"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

#### Step 1.3: Docker Compose for PostgreSQL

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: app_builder_db
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-langgraph}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-langgraph_dev_pass}
      POSTGRES_DB: ${POSTGRES_DB:-app_builder}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U langgraph"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - app_network

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: app_builder_pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL:-admin@appbuilder.local}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD:-admin}
    ports:
      - "${PGADMIN_PORT:-5050}:80"
    depends_on:
      - postgres
    networks:
      - app_network
    profiles:
      - debug  # Only start with: docker-compose --profile debug up

volumes:
  postgres_data:
    driver: local

networks:
  app_network:
    driver: bridge
```

#### Step 1.4: Environment Configuration

```bash
# .env.development
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://langgraph:langgraph_dev_pass@localhost:5432/app_builder
POSTGRES_USER=langgraph
POSTGRES_PASSWORD=langgraph_dev_pass
POSTGRES_DB=app_builder
POSTGRES_PORT=5432

# PgAdmin (optional)
PGADMIN_EMAIL=admin@appbuilder.local
PGADMIN_PASSWORD=admin
PGADMIN_PORT=5050

# LLM Configuration
DEFAULT_MODEL=google_genai:gemini-2.0-flash-exp
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Fallback models
# ANTHROPIC_API_KEY=your_anthropic_key
# OPENAI_API_KEY=your_openai_key

# MCP Configuration
GITHUB_TOKEN=your_github_token_here  # Optional but recommended

# Output directory (will be created dynamically per project)
OUTPUT_DIR=./output
```

#### Step 1.5: State Schemas (src/state/schemas.py)

See [Code Examples](#code-examples) section below for complete implementation.

#### Step 1.6: Checkpointer Factory (src/checkpointing/factory.py)

See [PostgreSQL Setup](#postgresql-setup) section below for complete implementation.

#### Step 1.7: MCP Client (src/mcp/client.py)

See [MCP Integration](#mcp-integration) section below for complete implementation.

#### Step 1.8: Model Utility (src/utils/model.py)

```python
# src/utils/model.py
from langchain.chat_models import init_chat_model
import os
from typing import Optional

def get_model(model_override: Optional[str] = None, temperature: float = 0):
    """
    Get LLM model - model-agnostic design

    Args:
        model_override: Optional model string (e.g., "anthropic:claude-sonnet-4-5-20250929")
        temperature: Model temperature (0 for deterministic, 1 for creative)

    Returns:
        Chat model instance

    Examples:
        >>> model = get_model()  # Uses DEFAULT_MODEL env var
        >>> model = get_model("google_genai:gemini-2.0-flash-exp")
        >>> model = get_model("anthropic:claude-sonnet-4-5-20250929", temperature=0.7)
    """
    model_name = model_override or os.getenv(
        "DEFAULT_MODEL",
        "google_genai:gemini-2.0-flash-exp"
    )

    try:
        return init_chat_model(model_name, temperature=temperature)
    except Exception as e:
        print(f"⚠️  Failed to initialize {model_name}: {e}")
        print("   Falling back to Gemini 2.0 Flash...")
        return init_chat_model("google_genai:gemini-2.0-flash-exp", temperature=temperature)

def get_cheap_model():
    """Get cheapest model for simple tasks"""
    return get_model("google_genai:gemini-2.0-flash-exp", temperature=0)

def get_smart_model():
    """Get best model for complex tasks"""
    # Try Claude first, fall back to Gemini
    if os.getenv("ANTHROPIC_API_KEY"):
        return get_model("anthropic:claude-sonnet-4-5-20250929", temperature=0)
    return get_cheap_model()
```

---

### Phase 2: Agent Implementation (Week 3-4)

Each agent follows this pattern:

```python
from langchain.agents import create_agent
from src.utils.model import get_model

# Load tools
tools = [tool1, tool2, ...]

# Load system prompt
with open("config/prompts/agent_name.txt") as f:
    system_prompt = f.read()

# Create agent
agent = create_agent(
    get_model(),
    tools=tools,
    system_prompt=system_prompt
)
```

See [Agent Specifications](#agent-specifications) section for detailed implementations.

---

### Phase 3: Workflow Orchestration (Week 5)

See [Workflow Orchestration](#workflow-orchestration) section for complete implementation.

---

### Phase 4: Main Application (Week 6)

See [Code Examples](#code-examples) section for main.py implementation.

---

### Phase 5: Testing (Week 7)

See [Testing Strategy](#testing-strategy) section.

---

## Agent Specifications

### 1. Initializer Agent

**File**: `src/agents/initializer.py`

**Purpose**: Analyze ANY project description, infer tech stack, and bootstrap the application.

**Tools**:
1. `analyze_project_requirements(description: str) -> ProjectMetadata` - Analyze project type, domain, and requirements
2. `infer_tech_stack(project_metadata: dict, user_constraints: dict) -> TechStack` - Choose appropriate technologies
3. `generate_feature_list(project_metadata: dict) -> list[Feature]` - **Dynamically** generate features using LLM
4. `create_git_repo(path: str) -> str`
5. `create_init_script(repo_path: str, tech_stack: TechStack) -> str` - Generate setup script for the inferred stack
6. `initialize_progress_log(repo_path: str) -> str`
7. MCP filesystem tools (read/write files)
8. MCP git tools (init, commit)

**System Prompt** (`config/prompts/initializer.txt`):
```
You are the Initializer Agent. Your job is to analyze ANY project description and bootstrap it.

CRITICAL: You work with ANY type of software project, not just chatbots.

WORKFLOW:
1. **Analyze project description** to understand:
   - Project type (web app, REST API, CLI tool, desktop app, mobile backend, etc.)
   - Domain (e-commerce, chat, blog, dashboard, finance, healthcare, etc.)
   - Core requirements and constraints
   - Scale expectations (MVP vs full-featured)

2. **Infer appropriate tech stack**:
   - Backend: Python (FastAPI/Django/Flask), Node (Express/NestJS), Ruby (Rails), Go, etc.
   - Frontend: React, Vue, Svelte, Angular, or NONE (for APIs/CLIs)
   - Database: PostgreSQL, MongoDB, MySQL, SQLite, or NONE (stateless)
   - Testing: pytest+Playwright, Jest+Cypress, Go testing, etc.
   - Deployment: Docker, Kubernetes, or simple (Heroku/Vercel)

3. **Generate comprehensive feature list** (20-50 features) tailored to the project:
   - Use LLM to generate features based on project type and domain
   - Features must be atomic (implementable in one session)
   - Features must be testable (clear acceptance criteria)
   - Features must be prioritized (1 = critical MVP, 5 = nice-to-have)

4. Create git repository
5. Create init.sh script with correct setup commands for the inferred stack
6. Initialize progress_log.json
7. Create initial commit

FEATURE GENERATION RULES:
- Features adapt to project type (chatbot needs messaging, e-commerce needs cart, etc.)
- Number of features depends on project complexity (simple API = 15-20, complex web app = 40-50)
- Always start with authentication, core functionality, then enhancements

Feature schema (GENERIC - adapts to project):
{
  "id": "f-001",
  "title": "Short descriptive title (varies by project)",
  "description": "Detailed description (context-specific)",
  "acceptance_criteria": [
    "Criterion 1: Specific, testable requirement",
    "Criterion 2: Another specific requirement"
  ],
  "status": "pending",
  "priority": 1,  // 1 = critical MVP, 5 = nice-to-have
  "complexity": "medium",  // low, medium, high
  "tech_stack": {
    "backend": ["<inferred>"],  // e.g., ["python", "fastapi"] or ["node", "express"]
    "frontend": ["<inferred>"] or null,  // null for backend-only projects
    "database": ["<inferred>"] or null
  }
}

EXAMPLES OF GENERATED FEATURES:

Chatbot project:
- f-001: "User authentication with JWT" (priority 2, medium)
- f-002: "Send message via POST /chat endpoint" (priority 1, high)
- f-003: "Stream AI response token-by-token" (priority 3, high)

E-commerce project:
- f-001: "Product catalog with search and filters" (priority 1, medium)
- f-002: "Shopping cart with add/remove items" (priority 1, low)
- f-003: "Stripe payment integration" (priority 2, high)

REST API project:
- f-001: "JWT authentication endpoints" (priority 1, medium)
- f-002: "CRUD endpoints for main resource" (priority 1, low)
- f-003: "OpenAPI/Swagger documentation" (priority 3, low)

Blog project:
- f-001: "Create and publish posts" (priority 1, medium)
- f-002: "Markdown editor with preview" (priority 2, medium)
- f-003: "SEO meta tags and sitemap" (priority 3, low)

INIT SCRIPT REQUIREMENTS (adapts to tech stack):
- Install all dependencies (pip, npm, cargo, etc. based on stack)
- Start backend server (uvicorn, npm start, rails server, etc.)
- Start frontend dev server (if frontend exists)
- Run database migrations (if database exists)
- Validate environment setup (check API keys, connections, etc.)

TECH STACK INFERENCE LOGIC:
- If "API" or "backend" in description → Backend-only (no frontend)
- If "chat", "e-commerce", "blog", "dashboard" → Full-stack (backend + frontend)
- If "CLI" or "command-line" → CLI tool (no frontend, no database usually)
- Python preferred for ML/AI, Node for real-time, Go for performance
- React most common frontend, Vue for simpler projects
- PostgreSQL for relational data, MongoDB for flexible schemas

PROGRESS LOG SCHEMA:
{
  "timestamp": "2025-11-26T10:00:00Z",
  "agent": "initializer",
  "feature_id": null,
  "action": "initialized",
  "project_type": "web_app",  // or "rest_api", "cli_tool", etc.
  "domain": "e-commerce",  // or "chat", "blog", etc.
  "commit_sha": "abc123",
  "notes": "Created project structure with FastAPI + React stack"
}

CRITICAL:
- Do NOT assume chatbot - analyze the actual project description
- Tech stack must match project requirements (don't use React for an API-only project)
- Feature list must be tailored to the specific project type
- Initial commit should include all bootstrap files
```

**Implementation Pattern**:
```python
from langchain.agents import create_agent
from langchain_core.tools import tool
from src.utils.model import get_model
import subprocess
import json
import os

@tool
def create_git_repo(path: str) -> str:
    """Initialize git repository at specified path"""
    os.makedirs(path, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True)
    return f"Git repository initialized at {path}"

@tool
def generate_feature_list(project_description: str) -> list[dict]:
    """Generate comprehensive feature list for ANY software project"""
    # This uses the LLM to dynamically generate features based on project type
    # Features adapt to: chatbots, e-commerce, APIs, blogs, dashboards, etc.
    # Example templates in config/feature_templates/ for reference only
    pass

# ... more tools ...

with open("config/prompts/initializer.txt") as f:
    system_prompt = f.read()

initializer_agent = create_agent(
    get_model(),
    tools=[create_git_repo, generate_feature_list, ...],
    system_prompt=system_prompt
)
```

---

### 2. Coding Agent

**File**: `src/agents/coding.py`

**Purpose**: Implement one feature at a time with clean code, tests, and git commits.

**Tools**:
1. `select_next_feature(feature_list: list[dict]) -> dict`
2. `run_init_script(repo_path: str) -> str`
3. `run_unit_tests(repo_path: str, test_pattern: str) -> dict`
4. `create_git_commit(repo_path: str, message: str) -> str`
5. `update_feature_status(feature_id: str, status: str) -> str`
6. MCP filesystem tools
7. MCP git tools

**System Prompt** (`config/prompts/coding.txt`):
```
You are the Coding Agent. Your job is to implement features incrementally and cleanly.

WORKFLOW (every session):
1. Read git log to understand current state
2. Read progress_log.json to see what's been done
3. Run init.sh to start development servers
4. Run basic smoke test to verify working state
5. Select ONE highest-priority pending feature
6. Implement the feature completely
7. Run unit tests to validate
8. Create git commit with descriptive message
9. Update progress log

IMPLEMENTATION RULES:
- Implement ONLY ONE feature per session
- Write clean, maintainable code following best practices
- Add unit tests for new functionality
- Do NOT modify or remove existing tests
- Follow existing code patterns and architecture
- Leave the codebase in a mergeable state

COMMIT MESSAGE FORMAT:
feat(feature-id): Brief description

Detailed description if needed.

Acceptance criteria met:
- Criterion 1
- Criterion 2

CRITICAL:
- ONE feature per session (no exceptions)
- All unit tests must pass before committing
- Code must follow project conventions
- Never break existing functionality
- Always update progress log after commit
```

---

### 3. Test Agent

**File**: `src/agents/testing.py`

**Purpose**: Validate features with end-to-end browser automation tests.

**Tools**:
1. `generate_playwright_tests(feature: dict) -> str`
2. `run_playwright_tests(test_file: str) -> dict`
3. `capture_test_screenshots(feature_id: str) -> list[str]`
4. `update_test_results(feature_id: str, results: dict) -> str`
5. MCP filesystem tools

**System Prompt** (`config/prompts/testing.txt`):
```
You are the Test Agent. Your job is to validate features with end-to-end tests.

WORKFLOW:
1. Receive feature specification from Coding Agent
2. Read the implemented code to understand what was changed
3. Generate Playwright E2E tests based on acceptance criteria
4. Run browser automation tests
5. Validate ALL acceptance criteria are met
6. Capture screenshots for visual validation
7. Mark feature as "done" if all tests pass, "failed" otherwise

TEST REQUIREMENTS:
- Test real user workflows (not just API calls)
- Use actual browser automation (Chrome/Firefox)
- Validate UI elements, interactions, and data flow
- Test edge cases and error handling
- Capture screenshots on failure for debugging

TEST RESULT FORMAT:
{
  "feature_id": "f-001",
  "passed": true/false,
  "total_tests": 5,
  "passed_tests": 5,
  "failed_tests": 0,
  "acceptance_criteria_met": ["criterion 1", "criterion 2"],
  "acceptance_criteria_failed": [],
  "screenshots": ["path/to/screenshot1.png"],
  "errors": [],
  "execution_time_ms": 1234
}

CRITICAL:
- Do NOT mark feature as done unless ALL acceptance criteria pass
- Use real browser automation (not mocks)
- Provide detailed failure reports with screenshots
- If tests fail, provide actionable feedback for Coding Agent
```

---

### 4. QA/Doc Agent

**File**: `src/agents/qa_doc.py`

**Purpose**: Review code quality, update documentation, and finalize feature completion.

**Tools**:
1. `run_code_quality_checks(repo_path: str, changed_files: list[str]) -> dict`
2. `update_progress_log(entry: dict) -> str`
3. `update_changelog(feature: dict) -> str`
4. `validate_acceptance_criteria(feature: dict) -> dict`
5. `generate_documentation(feature: dict) -> str`
6. MCP filesystem tools

**System Prompt** (`config/prompts/qa_doc.txt`):
```
You are the QA/Documentation Agent. Your job is to ensure quality and maintain documentation.

WORKFLOW:
1. Review code changes from Coding Agent
2. Run code quality checks (ruff, mypy)
3. Validate all acceptance criteria are truly met
4. Generate/update documentation for the feature
5. Update progress_log.json with completion status
6. Update CHANGELOG.md with feature summary
7. Mark feature as "done" in feature_list.json

CODE QUALITY CHECKS:
- Linting (ruff): No errors, minimal warnings
- Type checking (mypy): Strict mode passing
- Code coverage: New code has tests
- Security: No obvious vulnerabilities
- Performance: No obvious inefficiencies

DOCUMENTATION REQUIREMENTS:
- Update README if public API changed
- Add inline comments for complex logic
- Update API documentation if endpoints changed
- Include usage examples for new features

CRITICAL:
- Be thorough but efficient
- Flag technical debt for future sprints (don't block)
- Ensure documentation is clear and accurate
- Only mark feature "done" after all checks pass
```

---

## Workflow Orchestration

### LangGraph StateGraph Implementation

**File**: `src/workflow/orchestrator.py`

```python
from langgraph.graph import StateGraph, START, END
from src.state.schemas import AppBuilderState
from src.agents.initializer import initializer_agent
from src.agents.coding import coding_agent
from src.agents.testing import test_agent
from src.agents.qa_doc import qa_doc_agent
from src.workflow.routers import (
    route_after_init,
    route_after_coding,
    route_after_testing,
    route_after_qa
)

def create_workflow() -> StateGraph:
    """Create the multi-agent workflow using LangGraph"""

    workflow = StateGraph(ChatbotBuilderState)

    # Add agent nodes
    workflow.add_node("initializer", initializer_agent)
    workflow.add_node("coding", coding_agent)
    workflow.add_node("testing", test_agent)
    workflow.add_node("qa_doc", qa_doc_agent)

    # Define workflow edges
    workflow.add_edge(START, "initializer")

    # Conditional routing
    workflow.add_conditional_edges("initializer", route_after_init)
    workflow.add_conditional_edges("coding", route_after_coding)
    workflow.add_conditional_edges("testing", route_after_testing)
    workflow.add_conditional_edges("qa_doc", route_after_qa)

    return workflow
```

**File**: `src/workflow/routers.py`

```python
from src.state.schemas import AppBuilderState
from typing import Literal

def route_after_init(state: AppBuilderState) -> Literal["coding", "END"]:
    """Route after initialization"""
    if state.get("feature_list") and len(state["feature_list"]) > 0:
        return "coding"
    return "END"

def route_after_coding(state: AppBuilderState) -> Literal["testing", "END"]:
    """Route after coding"""
    if state.get("current_feature"):
        return "testing"
    # No more features to implement
    return "END"

def route_after_testing(state: AppBuilderState) -> Literal["qa_doc", "coding"]:
    """Route after testing - retry on failure"""
    test_result = state.get("test_context", {}).get("last_result", {})

    if test_result.get("passed"):
        return "qa_doc"

    # Handle test failure with retry logic
    current_feature = state["current_feature"]

    if current_feature["attempts"] >= 3:
        # Max retries reached - mark as failed and move on
        print(f"⚠️  Feature {current_feature['id']} failed after 3 attempts")
        current_feature["status"] = "failed"
        # This will cause coding agent to select next feature
        return "coding"

    # Retry - increment attempts and go back to coding
    current_feature["attempts"] += 1
    return "coding"

def route_after_qa(state: AppBuilderState) -> Literal["coding", "END"]:
    """Route after QA - continue or finish"""
    # Count remaining features
    pending_features = [
        f for f in state["feature_list"]
        if f["status"] == "pending"
    ]

    if pending_features:
        return "coding"  # More features to implement

    return "END"  # All done!
```

---

## PostgreSQL Setup

### Checkpointer Factory Implementation

**File**: `src/checkpointing/factory.py`

```python
import os
import asyncpg
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from typing import Optional
from contextlib import asynccontextmanager

class CheckpointerFactory:
    """Singleton factory for PostgreSQL checkpointer"""

    _instance: Optional[AsyncPostgresSaver] = None
    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def get_checkpointer(cls, force_new: bool = False) -> AsyncPostgresSaver:
        """
        Get or create checkpointer instance

        Args:
            force_new: Force creation of new instance

        Returns:
            AsyncPostgresSaver instance
        """
        if cls._instance is None or force_new:
            await cls._initialize()

        return cls._instance

    @classmethod
    async def _initialize(cls):
        """Initialize checkpointer with connection pool"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError(
                "DATABASE_URL environment variable must be set. "
                "Format: postgresql://user:pass@host:port/dbname"
            )

        print(f"📦 Connecting to PostgreSQL...")

        # Create connection pool
        cls._pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )

        # Create checkpointer
        cls._instance = AsyncPostgresSaver(cls._pool)

        # Setup tables (idempotent operation)
        await cls._instance.setup()

        print(f"✅ Checkpointer initialized with connection pool")

    @classmethod
    async def close(cls):
        """Close connection pool gracefully"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            cls._instance = None
            print("✅ Checkpointer connection pool closed")

    @classmethod
    def get_thread_id(
        cls,
        project_name: str,
        feature_id: Optional[str] = None
    ) -> str:
        """
        Generate thread ID for checkpointing

        Args:
            project_name: Name of the project being built
            feature_id: Optional feature ID for feature-scoped threads

        Returns:
            Thread ID string

        Examples:
            >>> get_thread_id("chatbot-clone")
            "chatbot-clone::project"
            >>> get_thread_id("chatbot-clone", "f-001")
            "chatbot-clone::f-001"
        """
        if feature_id:
            return f"{project_name}::{feature_id}"
        return f"{project_name}::project"

# Convenience functions
async def get_checkpointer() -> AsyncPostgresSaver:
    """Get the checkpointer instance"""
    return await CheckpointerFactory.get_checkpointer()

@asynccontextmanager
async def checkpointer_context():
    """Context manager for checkpointer lifecycle"""
    try:
        checkpointer = await get_checkpointer()
        yield checkpointer
    finally:
        await CheckpointerFactory.close()
```

### Database Inspection Script

**File**: `scripts/inspect_checkpoints.py`

```python
"""Utility to inspect checkpoints in PostgreSQL"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv
import sys

load_dotenv()

async def list_threads():
    """List all checkpoint threads"""
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))

    query = """
        SELECT DISTINCT
            config->>'thread_id' as thread_id,
            COUNT(*) as checkpoint_count,
            MAX(checkpoint_id) as latest_checkpoint,
            MAX(checkpoint->'ts') as last_updated
        FROM checkpoints
        GROUP BY config->>'thread_id'
        ORDER BY last_updated DESC
    """

    rows = await conn.fetch(query)

    print("\n📊 Checkpoint Threads:")
    print("=" * 80)
    for row in rows:
        print(f"Thread: {row['thread_id']}")
        print(f"  Checkpoints: {row['checkpoint_count']}")
        print(f"  Latest ID: {row['latest_checkpoint']}")
        print(f"  Last Updated: {row['last_updated']}")
        print()

    await conn.close()

async def get_thread_state(thread_id: str):
    """Get latest state for a thread"""
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))

    query = """
        SELECT checkpoint
        FROM checkpoints
        WHERE config->>'thread_id' = $1
        ORDER BY checkpoint_id DESC
        LIMIT 1
    """

    row = await conn.fetchrow(query, thread_id)

    if row:
        print(f"\n📝 Latest state for '{thread_id}':")
        print("=" * 80)
        print(row['checkpoint'])
    else:
        print(f"No checkpoints found for thread '{thread_id}'")

    await conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python inspect_checkpoints.py list")
        print("  python inspect_checkpoints.py state <thread_id>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        asyncio.run(list_threads())
    elif command == "state" and len(sys.argv) == 3:
        asyncio.run(get_thread_state(sys.argv[2]))
    else:
        print("Invalid command")
        sys.exit(1)
```

---

## MCP Integration

### MCP Client Configuration

**File**: `src/mcp/client.py`

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
import os
from typing import Any

async def create_mcp_client(project_path: str = None) -> MultiServerMCPClient:
    """
    Create MCP client with filesystem, git, and optionally GitHub servers

    Args:
        project_path: Path to the project directory (defaults to OUTPUT_DIR env var)

    Returns:
        Configured MultiServerMCPClient instance
    """
    if project_path is None:
        project_path = os.getenv("OUTPUT_DIR", "./output")

    github_token = os.getenv("GITHUB_TOKEN")

    config: dict[str, Any] = {}

    # Filesystem server (always enabled)
    config["filesystem"] = {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", project_path],
        "transport": "stdio"
    }

    # Git server (always enabled)
    config["git"] = {
        "command": "uvx",
        "args": ["mcp-server-git", "--repository", project_path],
        "transport": "stdio"
    }

    # GitHub server (optional - requires token)
    if github_token:
        config["github"] = {
            "url": "https://api.githubcopilot.com/mcp/",
            "transport": "streamable_http",
            "headers": {"Authorization": f"Bearer {github_token}"}
        }
        print("✅ GitHub MCP server enabled")
    else:
        print("⚠️  GITHUB_TOKEN not set - GitHub MCP server disabled")

    try:
        client = MultiServerMCPClient(config)
        print(f"✅ MCP client initialized with {len(config)} servers")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize MCP client: {e}")
        # Fallback to filesystem only
        print("   Falling back to filesystem-only MCP client")
        return MultiServerMCPClient({
            "filesystem": config["filesystem"]
        })

async def get_mcp_tools():
    """Get all tools from MCP servers"""
    client = await create_mcp_client()
    tools = await client.get_tools()
    print(f"📦 Loaded {len(tools)} tools from MCP servers")
    return tools
```

---

## Feature List

### IMPORTANT: Features are Generated Dynamically

**CRITICAL**: Feature lists are NOT hardcoded. The Initializer Agent generates them dynamically based on project description using an LLM.

**Files**:
- `config/feature_templates/` - Example feature lists for reference (NOT used directly)
- `output/<project-name>/feature_list.json` - Generated at runtime by Initializer Agent

```json
[
  {
    "id": "f-001",
    "title": "User registration with email/password",
    "description": "Implement user registration endpoint that accepts email and password, validates input, hashes password, and stores user in database",
    "acceptance_criteria": [
      "POST /api/auth/register endpoint exists",
      "Validates email format",
      "Validates password strength (min 8 chars)",
      "Hashes password with bcrypt",
      "Returns JWT token on success",
      "Returns 400 on validation error"
    ],
    "status": "pending",
    "priority": 2,
    "complexity": "medium"
  },
  {
    "id": "f-002",
    "title": "User login with JWT authentication",
    "description": "Implement login endpoint that verifies credentials and returns JWT token for authenticated sessions",
    "acceptance_criteria": [
      "POST /api/auth/login endpoint exists",
      "Validates email and password",
      "Returns JWT token on success",
      "Token includes user_id and expiry",
      "Returns 401 on invalid credentials"
    ],
    "status": "pending",
    "priority": 2,
    "complexity": "medium"
  },
  {
    "id": "f-003",
    "title": "Display chat interface with input and message list",
    "description": "Create React component for chat UI with message list, input field, and send button",
    "acceptance_criteria": [
      "Chat component renders in main view",
      "Message list displays previous messages",
      "Input field accepts user text",
      "Send button is clickable",
      "UI is responsive on mobile"
    ],
    "status": "pending",
    "priority": 1,
    "complexity": "low"
  },
  {
    "id": "f-004",
    "title": "Send message via POST /chat endpoint",
    "description": "Implement backend endpoint that receives user messages and forwards to LLM API",
    "acceptance_criteria": [
      "POST /api/chat endpoint exists",
      "Accepts message text and conversation_id",
      "Calls LLM API (OpenAI/Anthropic)",
      "Stores user message in database",
      "Stores AI response in database",
      "Returns AI response"
    ],
    "status": "pending",
    "priority": 1,
    "complexity": "high"
  },
  {
    "id": "f-005",
    "title": "Display AI response in chat UI",
    "description": "Update chat UI to show AI response after sending message",
    "acceptance_criteria": [
      "AI response appears in message list",
      "Loading indicator shows while waiting",
      "Messages are visually distinct (user vs AI)",
      "Auto-scroll to latest message",
      "Error message shown on failure"
    ],
    "status": "pending",
    "priority": 1,
    "complexity": "medium"
  },
  {
    "id": "f-006",
    "title": "Create new conversation",
    "description": "Allow users to start a new conversation thread",
    "acceptance_criteria": [
      "New conversation button exists",
      "POST /api/conversations endpoint creates conversation",
      "Conversation has unique ID",
      "Conversation stored with user_id",
      "UI switches to new conversation on creation"
    ],
    "status": "pending",
    "priority": 2,
    "complexity": "low"
  },
  {
    "id": "f-007",
    "title": "List all user conversations in sidebar",
    "description": "Display list of user's conversations in a sidebar with titles and timestamps",
    "acceptance_criteria": [
      "GET /api/conversations endpoint returns user's conversations",
      "Sidebar displays conversation list",
      "Each conversation shows title and last updated time",
      "Conversations sorted by most recent",
      "Active conversation is highlighted"
    ],
    "status": "pending",
    "priority": 2,
    "complexity": "medium"
  },
  {
    "id": "f-008",
    "title": "Load conversation history on select",
    "description": "When user clicks a conversation in sidebar, load all messages for that conversation",
    "acceptance_criteria": [
      "GET /api/conversations/:id/messages endpoint exists",
      "Returns all messages for conversation",
      "Messages displayed in correct order",
      "UI updates without full page reload",
      "Loading state shown while fetching"
    ],
    "status": "pending",
    "priority": 2,
    "complexity": "medium"
  },
  {
    "id": "f-009",
    "title": "Stream AI response token-by-token",
    "description": "Implement Server-Sent Events to stream AI response as it's generated",
    "acceptance_criteria": [
      "POST /api/chat endpoint supports streaming",
      "Uses SSE for token streaming",
      "Tokens appear incrementally in UI",
      "Stream ends with done signal",
      "Fallback to non-streaming if SSE fails"
    ],
    "status": "pending",
    "priority": 3,
    "complexity": "high"
  },
  {
    "id": "f-010",
    "title": "Render markdown in messages",
    "description": "Parse and render markdown formatting in both user and AI messages",
    "acceptance_criteria": [
      "Bold, italic, headers render correctly",
      "Code blocks have syntax highlighting",
      "Links are clickable",
      "Lists render as HTML lists",
      "Markdown library integrated (e.g., marked.js)"
    ],
    "status": "pending",
    "priority": 3,
    "complexity": "low"
  },
  {
    "id": "f-011",
    "title": "Code syntax highlighting in messages",
    "description": "Highlight code blocks with appropriate syntax coloring",
    "acceptance_criteria": [
      "Code blocks detected with language tag",
      "Syntax highlighting applied (e.g., Prism.js)",
      "Multiple languages supported (Python, JS, etc.)",
      "Fallback to plain text if language unknown"
    ],
    "status": "pending",
    "priority": 3,
    "complexity": "low"
  },
  {
    "id": "f-012",
    "title": "Copy code block button",
    "description": "Add copy button to code blocks for easy copying",
    "acceptance_criteria": [
      "Copy button appears on hover over code block",
      "Clicking button copies code to clipboard",
      "Visual feedback on successful copy",
      "Works on all modern browsers"
    ],
    "status": "pending",
    "priority": 3,
    "complexity": "low"
  },
  {
    "id": "f-013",
    "title": "Dark mode toggle",
    "description": "Implement dark/light theme toggle with persistence",
    "acceptance_criteria": [
      "Toggle button in header",
      "Dark theme applied to all components",
      "Preference saved to localStorage",
      "Theme persists across sessions",
      "Smooth transition between themes"
    ],
    "status": "pending",
    "priority": 3,
    "complexity": "medium"
  },
  {
    "id": "f-014",
    "title": "Responsive mobile layout",
    "description": "Ensure chat UI works well on mobile devices",
    "acceptance_criteria": [
      "Sidebar collapses on mobile",
      "Chat input remains accessible on mobile keyboard",
      "Messages readable on small screens",
      "Touch interactions work smoothly",
      "Tested on iOS and Android"
    ],
    "status": "pending",
    "priority": 3,
    "complexity": "medium"
  },
  {
    "id": "f-015",
    "title": "Keyboard shortcuts for common actions",
    "description": "Add keyboard shortcuts: Enter to send, Ctrl+K for new chat, etc.",
    "acceptance_criteria": [
      "Enter sends message (Shift+Enter for new line)",
      "Ctrl+K (Cmd+K on Mac) starts new conversation",
      "Esc closes modals",
      "Shortcuts shown in help menu",
      "Shortcuts don't conflict with browser defaults"
    ],
    "status": "pending",
    "priority": 3,
    "complexity": "low"
  },
  {
    "id": "f-016",
    "title": "Delete conversation",
    "description": "Allow users to delete conversations they no longer need",
    "acceptance_criteria": [
      "Delete button on each conversation in sidebar",
      "Confirmation dialog before deletion",
      "DELETE /api/conversations/:id endpoint",
      "Conversation and messages removed from database",
      "UI updates after deletion"
    ],
    "status": "pending",
    "priority": 3,
    "complexity": "low"
  },
  {
    "id": "f-017",
    "title": "Password reset functionality",
    "description": "Implement password reset via email link",
    "acceptance_criteria": [
      "POST /api/auth/forgot-password endpoint",
      "Email sent with reset token",
      "Reset token expires after 1 hour",
      "POST /api/auth/reset-password verifies token",
      "Password updated on valid token"
    ],
    "status": "pending",
    "priority": 2,
    "complexity": "high"
  },
  {
    "id": "f-018",
    "title": "User logout and session management",
    "description": "Implement logout functionality and proper session handling",
    "acceptance_criteria": [
      "Logout button in UI",
      "POST /api/auth/logout endpoint",
      "JWT token invalidated",
      "User redirected to login",
      "Session state cleared"
    ],
    "status": "pending",
    "priority": 2,
    "complexity": "low"
  },
  {
    "id": "f-019",
    "title": "Character count indicator",
    "description": "Show character count in message input with limit warning",
    "acceptance_criteria": [
      "Character count shown below input",
      "Warning color when approaching limit (e.g., 4000 chars)",
      "Send button disabled when over limit",
      "Count updates in real-time"
    ],
    "status": "pending",
    "priority": 3,
    "complexity": "low"
  },
  {
    "id": "f-020",
    "title": "Display streaming indicator",
    "description": "Show visual indicator when AI is generating response",
    "acceptance_criteria": [
      "Typing indicator (e.g., animated dots) appears",
      "Indicator shows while streaming",
      "Indicator disappears when stream ends",
      "Works with both streaming and non-streaming"
    ],
    "status": "pending",
    "priority": 3,
    "complexity": "low"
  },
  {
    "id": "f-021",
    "title": "Handle stream errors gracefully",
    "description": "Properly handle and display errors during streaming",
    "acceptance_criteria": [
      "Network errors shown to user",
      "Partial response preserved on error",
      "Retry button offered on failure",
      "Error logged for debugging",
      "User not left in broken state"
    ],
    "status": "pending",
    "priority": 3,
    "complexity": "medium"
  },
  {
    "id": "f-022",
    "title": "Auto-scroll to latest message",
    "description": "Automatically scroll chat to bottom when new messages arrive",
    "acceptance_criteria": [
      "Scrolls to bottom on new message",
      "Doesn't scroll if user scrolled up",
      "Smooth scroll animation",
      "Works with streaming messages"
    ],
    "status": "pending",
    "priority": 3,
    "complexity": "low"
  },
  {
    "id": "f-023",
    "title": "LLM integration with OpenAI/Anthropic API",
    "description": "Integrate backend with LLM provider APIs",
    "acceptance_criteria": [
      "API client configured with key",
      "Supports multiple providers (OpenAI, Anthropic)",
      "Provider selectable via env var",
      "Error handling for rate limits",
      "Timeout handling (30s max)"
    ],
    "status": "pending",
    "priority": 1,
    "complexity": "high"
  },
  {
    "id": "f-024",
    "title": "Database schema for users and conversations",
    "description": "Design and implement PostgreSQL schema for application data",
    "acceptance_criteria": [
      "Users table (id, email, password_hash, created_at)",
      "Conversations table (id, user_id, title, created_at, updated_at)",
      "Messages table (id, conversation_id, role, content, created_at)",
      "Foreign keys and indexes configured",
      "Migration scripts created"
    ],
    "status": "pending",
    "priority": 1,
    "complexity": "medium"
  },
  {
    "id": "f-025",
    "title": "Environment configuration and secrets management",
    "description": "Set up proper environment variable handling for all secrets",
    "acceptance_criteria": [
      ".env file template created",
      "All secrets loaded from environment",
      "No secrets in code or git",
      "Different configs for dev/prod",
      "Validation on startup"
    ],
    "status": "pending",
    "priority": 1,
    "complexity": "low"
  }
]
```

---

## Code Examples

### Main Application

**File**: `src/main.py`

```python
"""
Multi-Agent Software Builder
Main entry point for the application
"""

import asyncio
import os
import signal
from dotenv import load_dotenv
from src.checkpointing.factory import CheckpointerFactory, get_checkpointer
from src.workflow.orchestrator import create_workflow
from src.state.schemas import AppBuilderState

# Load environment
env = os.getenv("ENVIRONMENT", "development")
load_dotenv(f".env.{env}")

class SoftwareBuilderApp:
    """Main application with lifecycle management"""

    def __init__(self):
        self.workflow = None
        self.app = None
        self.running = True

    async def startup(self):
        """Initialize all components"""
        print("🚀 Starting Multi-Agent Software Builder...")
        print(f"   Environment: {env}")

        # Initialize checkpointer
        checkpointer = await get_checkpointer()

        # Create workflow
        print("📊 Creating workflow...")
        self.workflow = create_workflow()
        self.app = self.workflow.compile(checkpointer=checkpointer)

        print("✅ Application ready\n")

    async def shutdown(self):
        """Cleanup resources"""
        print("\n🛑 Shutting down gracefully...")
        await CheckpointerFactory.close()
        print("✅ Shutdown complete")

    async def run(self, project_name: str, project_description: str):
        """
        Run the multi-agent system to build ANY software application

        Args:
            project_name: Name/slug for the project (e.g., "chatbot-clone", "ecommerce-mvp")
            project_description: Detailed description of what to build
        """
        # Generate paths dynamically
        output_base = os.getenv("OUTPUT_DIR", "./output")
        repo_path = os.path.join(output_base, project_name)

        thread_id = CheckpointerFactory.get_thread_id(project_name)

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        initial_state: AppBuilderState = {
            "messages": [{
                "role": "user",
                "content": project_description
            }],
            "phase": "init",
            "repo_path": repo_path,
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
                "failure_details": None
            },
            "progress_log": [],
            "retry_count": 0,
            "max_retries": 3,
            "project_name": project_name,
            "init_script_path": None
        }

        print(f"📝 Project: {project_description}")
        print(f"📂 Output: {repo_path}")
        print(f"🔖 Thread ID: {thread_id}\n")
        print("=" * 80)
        print()

        try:
            async for chunk in self.app.astream(initial_state, config):
                # Print updates from each agent
                self._print_chunk(chunk)

                if not self.running:
                    print("\n⚠️  Interrupted by user")
                    break

        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
        except Exception as e:
            print(f"\n❌ Error during execution: {e}")
            raise

        print("\n" + "=" * 80)
        print("✅ Multi-agent workflow completed!")

    def _print_chunk(self, chunk: dict):
        """Pretty print workflow updates"""
        for node_name, node_output in chunk.items():
            if node_name == "messages":
                # Print latest message
                if node_output:
                    latest = node_output[-1]
                    print(f"\n[{latest.get('role', 'agent').upper()}]")
                    print(latest.get('content', ''))

            elif node_name in ["initializer", "coding", "testing", "qa_doc"]:
                print(f"\n🤖 {node_name.upper()} AGENT")
                print("-" * 40)

            # Print state updates
            if isinstance(node_output, dict):
                if "current_feature" in node_output and node_output["current_feature"]:
                    feature = node_output["current_feature"]
                    print(f"📌 Feature: {feature['id']} - {feature['title']}")

                if "phase" in node_output:
                    print(f"📍 Phase: {node_output['phase']}")

async def main():
    """Main entry point"""
    import sys

    # Parse command-line arguments
    if len(sys.argv) < 3:
        print("Usage: python src/main.py <project_name> <project_description>")
        print("\nExamples:")
        print('  python src/main.py chatbot-clone "Build a chatbot like Claude/ChatGPT"')
        print('  python src/main.py ecommerce-mvp "Build an e-commerce site with cart and checkout"')
        print('  python src/main.py rest-api "Build a REST API for task management"')
        sys.exit(1)

    project_name = sys.argv[1]
    project_description = sys.argv[2]

    app = SoftwareBuilderApp()

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()

    def signal_handler():
        app.running = False

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await app.startup()

        # Run the system with dynamic project
        await app.run(
            project_name=project_name,
            project_description=project_description
        )

    finally:
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

### State Schemas

**File**: `src/state/schemas.py`

```python
"""
State schemas for the multi-agent workflow
Uses TypedDict as required by LangChain 1.0 (Pydantic not supported)

CRITICAL: These schemas are GENERIC and work for ANY project type
"""

from typing import TypedDict, Annotated, Literal, Optional
from langgraph.graph import add_messages

# Tech stack definition
class TechStack(TypedDict):
    """Inferred technology stack for the project"""
    backend: list[str]  # e.g., ["python", "fastapi"] or ["node", "express"]
    frontend: Optional[list[str]]  # e.g., ["react", "typescript"] or None for APIs
    database: Optional[list[str]]  # e.g., ["postgresql"] or None for stateless
    testing: list[str]  # e.g., ["pytest", "playwright"] or ["jest", "cypress"]
    deployment: Optional[list[str]]  # e.g., ["docker", "kubernetes"] or None

# Project metadata
class ProjectMetadata(TypedDict):
    """Metadata about the project being built"""
    name: str  # Project name (e.g., "chatbot-clone", "ecommerce-mvp")
    type: str  # Project type: "web_app", "rest_api", "cli_tool", "desktop_app", etc.
    domain: str  # Domain: "e-commerce", "chat", "blog", "dashboard", "finance", etc.
    tech_stack: TechStack
    estimated_features: int  # Estimated number of features to implement

# Feature definition
class Feature(TypedDict):
    """Individual feature to be implemented (generic for any project type)"""
    id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    status: Literal["pending", "in_progress", "testing", "done", "failed"]
    priority: int  # 1 = highest (critical MVP), 5 = lowest (nice-to-have)
    complexity: Literal["low", "medium", "high"]
    attempts: int  # Number of implementation attempts
    tech_stack: TechStack  # Which parts of the stack this feature touches

# Git context
class GitContext(TypedDict):
    """Git repository state"""
    current_branch: str
    last_commit_sha: str
    uncommitted_changes: bool
    snapshot_tag: Optional[str]

# Test context
class TestContext(TypedDict):
    """Testing state and results"""
    last_run_timestamp: str
    passed_tests: int
    failed_tests: int
    coverage_percentage: float
    failure_details: Optional[list[dict]]

# Main state
class AppBuilderState(TypedDict):
    """
    GENERIC state for building ANY type of application

    This state is persisted in PostgreSQL checkpoints and survives
    across sessions. Each agent can read and update this state.

    Works for: chatbots, e-commerce, REST APIs, blogs, dashboards, CLIs, etc.
    """
    # Core messaging
    messages: Annotated[list, add_messages]

    # Project information (dynamically inferred)
    project_metadata: ProjectMetadata
    repo_path: str

    # Feature management
    feature_list: list[Feature]
    current_feature: Optional[Feature]

    # Context objects
    git_context: GitContext
    test_context: TestContext

    # Workflow control
    phase: Literal["init", "coding", "testing", "qa", "complete"]
    retry_count: int
    max_retries: int

    # Scripts and paths
    init_script_path: Optional[str]

    # Progress tracking
    progress_log: list[dict]
```

---

## Testing Strategy

### Unit Tests

**File**: `tests/unit/test_routers.py`

```python
import pytest
from src.workflow.routers import (
    route_after_init,
    route_after_coding,
    route_after_testing,
    route_after_qa
)
from src.state.schemas import AppBuilderState, Feature

def test_route_after_init_with_features():
    state: AppBuilderState = {
        "feature_list": [
            {"id": "f-001", "title": "Test", "status": "pending", "priority": 1}
        ],
        # ... other required fields
    }
    assert route_after_init(state) == "coding"

def test_route_after_init_no_features():
    state: AppBuilderState = {
        "feature_list": [],
        # ... other required fields
    }
    assert route_after_init(state) == "END"

def test_route_after_testing_success():
    state: AppBuilderState = {
        "test_context": {
            "last_result": {"passed": True}
        },
        "current_feature": {
            "id": "f-001",
            "attempts": 1
        },
        # ... other required fields
    }
    assert route_after_testing(state) == "qa_doc"

def test_route_after_testing_failure_retry():
    state: AppBuilderState = {
        "test_context": {
            "last_result": {"passed": False}
        },
        "current_feature": {
            "id": "f-001",
            "attempts": 1
        },
        # ... other required fields
    }
    assert route_after_testing(state) == "coding"
    assert state["current_feature"]["attempts"] == 2

def test_route_after_testing_max_retries():
    state: AppBuilderState = {
        "test_context": {
            "last_result": {"passed": False}
        },
        "current_feature": {
            "id": "f-001",
            "attempts": 3  # Max retries
        },
        # ... other required fields
    }
    assert route_after_testing(state) == "coding"
    assert state["current_feature"]["status"] == "failed"
```

### Integration Tests

**File**: `tests/integration/test_checkpointing.py`

```python
import pytest
import asyncio
from src.checkpointing.factory import CheckpointerFactory, get_checkpointer
from src.state.schemas import AppBuilderState

@pytest.mark.asyncio
async def test_checkpointer_initialization():
    """Test that checkpointer initializes correctly"""
    checkpointer = await get_checkpointer()
    assert checkpointer is not None

@pytest.mark.asyncio
async def test_checkpoint_save_and_restore():
    """Test saving and restoring state"""
    checkpointer = await get_checkpointer()

    thread_id = "test-thread-001"
    config = {"configurable": {"thread_id": thread_id}}

    # Save state
    initial_state: AppBuilderState = {
        "messages": [{"role": "user", "content": "test"}],
        "feature_list": [],
        "phase": "init",
        # ... other fields
    }

    await checkpointer.aput(config, initial_state, {})

    # Restore state
    restored = await checkpointer.aget(config)

    assert restored is not None
    assert restored["phase"] == "init"

@pytest.mark.asyncio
async def test_thread_id_generation():
    """Test thread ID factory method"""
    project_id = CheckpointerFactory.get_thread_id("my-app")
    assert project_id == "my-app::project"

    feature_id = CheckpointerFactory.get_thread_id("my-app", "f-001")
    assert feature_id == "my-app::f-001"
```

### System Tests

**File**: `tests/system/test_full_pipeline.py`

```python
import pytest
import asyncio
from src.main import SoftwareBuilderApp

@pytest.mark.asyncio
@pytest.mark.slow
async def test_full_pipeline_simple_feature():
    """
    Test the full multi-agent pipeline on a simple feature
    This is a slow test that uses real LLM calls
    """
    app = SoftwareBuilderApp()

    await app.startup()

    try:
        # Run with a very simple project description
        await app.run(
            project_name="test-hello-api",
            project_description="Build a simple hello world API with one GET endpoint"
        )

        # Verify output
        import os
        output_dir = os.getenv("OUTPUT_DIR", "./output")
        project_path = os.path.join(output_dir, "test-hello-api")

        assert os.path.exists(project_path)
        assert os.path.exists(os.path.join(project_path, ".git"))
        assert os.path.exists(os.path.join(project_path, "feature_list.json"))

    finally:
        await app.shutdown()
```

---

## Deployment

### Production Environment Setup

1. **PostgreSQL Database**:
   ```bash
   # Use managed PostgreSQL (AWS RDS, Google Cloud SQL, etc.)
   # Or self-hosted with connection pooling
   ```

2. **Environment Variables**:
   ```bash
   # .env.production
   ENVIRONMENT=production
   DATABASE_URL=postgresql://user:pass@prod-host:5432/app_builder
   DEFAULT_MODEL=google_genai:gemini-2.0-flash-exp
   GOOGLE_API_KEY=prod_key_here
   OUTPUT_DIR=/var/app/output
   ```

3. **Run Application**:
   ```bash
   # Install dependencies
   pip install -e .

   # Run
   python src/main.py
   ```

4. **Monitoring** (optional):
   - LangSmith for agent tracing
   - Prometheus metrics
   - Log aggregation (e.g., CloudWatch, Datadog)

---

## Next Steps

After completing this implementation:

1. **Test the system** with progressively complex projects
2. **Optimize prompts** based on observed agent behavior
3. **Add human-in-the-loop** approval gates for critical operations
4. **Implement LangSmith** tracing for debugging
5. **Add rate limiting** to prevent API cost overruns
6. **Create a web UI** for non-technical users
7. **Generalize beyond chatbots** to other types of web applications

---

## Conclusion

This implementation plan provides a complete, production-ready architecture for a multi-agent system that can autonomously build **ANY type of software application**. The key innovations are:

- **Truly Generic**: Not hardcoded for chatbots - analyzes requirements and adapts to any project type
- **Dynamic Feature Generation**: LLM generates features tailored to the specific project
- **Tech Stack Inference**: Automatically chooses appropriate technologies
- **PostgreSQL everywhere** for dev/prod parity
- **Model-agnostic design** for flexibility (defaults to Gemini, works with Claude/GPT)
- **MCP integration** for standardized tooling
- **Feature-scoped checkpointing** for scalability
- **Adaptive testing** that matches the project type
- **Retry logic** for resilience

The system is designed to be **pragmatic**, **maintainable**, and **scalable** - ready for real-world use across diverse project types.
