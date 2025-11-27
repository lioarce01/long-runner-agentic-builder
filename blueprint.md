# Sistema Multi-Agente para Tareas de Codificación Long-Running: Blueprint Técnico con LangChain 1.0 y LangGraph 1.0

**Versión**: 2.0 - Actualizado para LangChain 1.0 y LangGraph 1.0 (Noviembre 2025)

---

## Resumen Ejecutivo

**Un sistema multi-agente práctico para coding es factible en 10-16 semanas usando LangGraph 1.0, deepagents, integración MCP, y los patrones del research de Anthropic de Noviembre 2025.** Este documento está actualizado para reflejar los cambios significativos en el ecosistema LangChain/LangGraph con las releases 1.0 de Octubre 2025.

### Cambios Clave en LangChain/LangGraph 1.0

| Componente | Antes (v0.x) | Ahora (v1.0) |
|------------|--------------|--------------|
| Agentes prebuilt | `langgraph.prebuilt.create_react_agent` | `langchain.agents.create_agent` |
| Modelo | Instanciación manual | `init_chat_model("provider:model")` |
| Extensibilidad | Hooks complejos | **Middleware composable** |
| Python | 3.9+ | **3.10+ requerido** |
| Checkpointers | `langgraph.checkpoint` | Packages separados (v3.0.x) |
| Long-running | Custom | **deepagents** (agent harness) |

---

## 1. Arquitectura LangGraph 1.0: La Nueva Foundation

### 1.1 La Relación LangChain ↔ LangGraph

LangGraph 1.0 es el **runtime de bajo nivel**, y LangChain 1.0 es ahora una **API de alto nivel construida sobre ese runtime**. Esta inversión de la jerarquía es fundamental:

```
┌─────────────────────────────────────────────┐
│              deepagents                     │  ← Agent Harness (long-running)
│         (planning, filesystem, subagents)   │
├─────────────────────────────────────────────┤
│              LangChain 1.0                  │  ← Agent Framework (high-level)
│         (create_agent, middleware)          │
├─────────────────────────────────────────────┤
│              LangGraph 1.0                  │  ← Agent Runtime (low-level)
│    (durable state, graphs, checkpointing)   │
└─────────────────────────────────────────────┘
```

### 1.2 Cuándo Usar Cada Capa

| Capa | Usar cuando... |
|------|----------------|
| **LangGraph** | Necesitas workflows custom, control fino sobre flujo, grafos complejos |
| **LangChain** | Quieres el loop de agente core sin built-ins, construir prompts/tools desde cero |
| **deepagents** | Construyes agentes autónomos, long-running, con planning, filesystem, sub-agentes |

### 1.3 Features Core de LangGraph 1.0

LangGraph 1.0 estabiliza cuatro features de runtime que separan agentes de producción de demos:

**Durable Execution**: Si el servidor se reinicia a mitad de un workflow, el agente continúa exactamente donde quedó. El checkpointing guarda estado en cada ejecución de nodo.

**Streaming**: LangGraph transmite todo: tokens LLM, tool calls, updates de estado, transiciones de nodos. Los usuarios ven progreso en tiempo real.

**Human-in-the-Loop**: API de primera clase para pausar ejecución, guardar estado, y esperar input humano sin bloquear threads. Cuando el humano responde, la ejecución continúa desde el punto exacto.

**Memory**: Short-term memory (contexto de trabajo) está built-in en state management. Long-term memory usa checkpointers persistentes que se conectan a bases de datos.

---

## 2. API de Agentes en LangChain 1.0

### 2.1 `create_agent`: El Nuevo Estándar

La pieza central de LangChain 1.0 es `create_agent`, que reemplaza `create_react_agent` de LangGraph (ahora deprecado):

```python
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

# Model-agnostic initialization - swap Gemini/Claude/GPT libremente
model = init_chat_model("google_genai:gemini-2.0-flash", temperature=0)

# Crear agente con el nuevo patrón
agent = create_agent(
    model,
    tools=[file_edit, bash_run, test_runner],
    system_prompt="You are a coding agent that implements features incrementally."
)

# Compilar con checkpointer para persistencia
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
app = agent.compile(checkpointer=checkpointer)

# Invocar
config = {"configurable": {"thread_id": "feature-001"}}
result = await app.ainvoke(
    {"messages": [{"role": "user", "content": "Implement user authentication"}]},
    config
)
```

### 2.2 Model-Agnostic Design con `init_chat_model()`

`init_chat_model()` permite cambio de modelo en runtime sin cambios de código:

```python
from langchain.chat_models import init_chat_model

# Diferentes providers con la misma API
model_gemini = init_chat_model("google_genai:gemini-2.5-pro")
model_claude = init_chat_model("anthropic:claude-sonnet-4-5-20250929")
model_openai = init_chat_model("openai:gpt-4o")

# El string infiere automáticamente el provider
# "gpt-5" se infiere como "openai:gpt-5"
```

### 2.3 Middleware: La Solución de LangChain 1.0 para Context Engineering

Middleware es como Express.js o Django middleware, pero para agentes AI. Intercepta el loop del agente, dando control quirúrgico sobre qué pasa antes, durante, y después de llamadas al modelo.

```python
from langchain.agents import create_agent
from langchain.agents.middleware import (
    SummarizationMiddleware,  # Compacta contexto largo
    LLMToolSelectorMiddleware,  # Pre-filtra tools
    AgentMiddleware
)

# Middleware de summarización para context compaction
agent = create_agent(
    model="openai:gpt-4o",
    tools=my_tools,
    middleware=[
        SummarizationMiddleware(
            model="openai:gpt-4o-mini",  # Modelo más barato para summarización
            max_tokens_before_summary=4000,
            messages_to_keep=5
        )
    ]
)
```

**Flujo de Request con Middleware**:
```
User Input 
  → Middleware 1: before_model 
  → Middleware 2: before_model 
  → Middleware 1,2: modify_model_request 
  → LLM Call 
  ← Middleware 2: after_model 
  ← Middleware 1: after_model 
  ← Final Response
```

### 2.4 Custom State con TypedDict

**Importante**: En LangChain 1.0, custom state schemas **deben** ser tipos TypedDict. Pydantic models y dataclasses **ya no son soportados**.

```python
from typing import TypedDict, Annotated
from langchain.agents import AgentState, create_agent
from langgraph.graph import add_messages

class CodingAgentState(AgentState):
    """Estado extendido para el coding agent"""
    current_feature: str
    feature_list: list[dict]
    progress_log: list[str]
    messages: Annotated[list, add_messages]

agent = create_agent(
    model="google_genai:gemini-2.0-flash",
    tools=coding_tools,
    state_schema=CodingAgentState
)
```

---

## 3. deepagents: Agent Harness para Long-Running Tasks

### 3.1 ¿Por Qué deepagents?

deepagents implementa los cuatro elementos clave observados en sistemas de agentes exitosos como Claude Code, Deep Research, y Manus:

1. **Planning Tool** - Los agentes escriben y actualizan todo lists para descomponer tareas
2. **Sub-Agent Spawning** - Delegación de subtareas a subagentes especializados
3. **File System Access** - Lectura/escritura de archivos para manejar contexto grande
4. **Detailed System Prompts** - Instrucciones comprehensivas para uso de tools

### 3.2 Creación de Deep Agent

```python
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

# Por defecto usa "claude-sonnet-4-5-20250929"
# Customizable con cualquier modelo LangChain
model = init_chat_model("google_genai:gemini-2.0-flash")

@tool
def run_tests(test_path: str) -> str:
    """Ejecuta tests y retorna resultados"""
    import subprocess
    result = subprocess.run(["pytest", test_path, "-v"], capture_output=True, text=True)
    return result.stdout + result.stderr

agent = create_deep_agent(
    model=model,
    tools=[run_tests],
    system_prompt="""You are a coding agent working on a chatbot clone.
    Always implement one feature at a time.
    Run tests after each change.
    Update the progress log after completing each feature."""
)

# Invocar
async for chunk in agent.astream({"messages": [{"role": "user", "content": "..."}]}):
    chunk["messages"][-1].pretty_print()
```

### 3.3 Pluggable Backends (deepagents 0.2)

deepagents 0.2 introduce backends pluggables para controlar cómo funcionan las operaciones de filesystem:

```python
from deepagents import create_deep_agent
from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.backends import (
    StateBackend,      # Ephemeral (en state del agente)
    StoreBackend,      # Persistente (cross-thread via LangGraph Store)
    FilesystemBackend, # Local filesystem real
    CompositeBackend   # Combina múltiples backends
)

# Backend híbrido: ephemeral por defecto, pero /memories/ persiste en store
backend = CompositeBackend(
    default=StateBackend(),
    routes={
        "/memories/": StoreBackend(),  # Long-term memory
        "/project/": FilesystemBackend(root_dir="/home/user/project")
    }
)

agent = create_deep_agent(
    middleware=[FilesystemMiddleware(backend=backend)]
)
```

### 3.4 Human-in-the-Loop con deepagents

```python
from langchain_core.tools import tool
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import InMemorySaver

@tool
def deploy_to_production(version: str) -> str:
    """Deploya una versión a producción"""
    return f"Deployed version {version}"

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    tools=[deploy_to_production],
    interrupt_on={
        "deploy_to_production": {
            "allowed_decisions": ["approve", "edit", "reject"]
        }
    }
)

# Compilar con checkpointer (requerido para HITL)
checkpointer = InMemorySaver()
app = agent.compile(checkpointer=checkpointer)
```

### 3.5 Integración de deepagents con MCP

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents import async_create_deep_agent

async def main():
    mcp_client = MultiServerMCPClient({
        "github": {
            "url": "https://api.githubcopilot.com/mcp/",
            "transport": "streamable_http",
            "headers": {"Authorization": f"Bearer {GITHUB_TOKEN}"}
        },
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/project"],
            "transport": "stdio"
        }
    })
    
    mcp_tools = await mcp_client.get_tools()
    
    agent = await async_create_deep_agent(tools=mcp_tools)
    
    async for chunk in agent.astream({"messages": [{"role": "user", "content": "..."}]}):
        chunk["messages"][-1].pretty_print()
```

---

## 4. Patrones Multi-Agente: Supervisor vs Swarm

### 4.1 Comparación de Arquitecturas

LangGraph ofrece dos bibliotecas principales para multi-agente:

| Aspecto | Supervisor | Swarm |
|---------|------------|-------|
| Control | Centralizado | Descentralizado |
| Comunicación | Hub-and-spoke | Peer-to-peer |
| Latencia | Mayor (traducción) | ~40% menor |
| Token Usage | Mayor | Menor |
| Flexibilidad | Menos flexible | Más flexible |
| Mejor para | Workflows estructurados | Tareas dinámicas |

### 4.2 Patrón Supervisor con LangChain 1.0

**Nota**: LangChain ahora recomienda implementar el patrón supervisor directamente via tools en lugar de usar `langgraph-supervisor` para la mayoría de casos:

```python
from langchain.agents import create_agent
from langchain.tools import tool, InjectedToolCallId
from langgraph.types import Command
from typing import Annotated

# Crear sub-agentes
coding_agent = create_agent(
    model="google_genai:gemini-2.0-flash",
    tools=[file_edit, bash_run],
    system_prompt="You implement code changes."
)

test_agent = create_agent(
    model="google_genai:gemini-2.0-flash", 
    tools=[run_tests, playwright_test],
    system_prompt="You run and validate tests."
)

# Definir tools de handoff para el supervisor
@tool("delegate_to_coding_agent", description="Delegate coding tasks to the coding specialist")
def call_coding_agent(
    task: str,
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    result = coding_agent.invoke({"messages": [{"role": "user", "content": task}]})
    return Command(update={
        "messages": [ToolMessage(content=result["messages"][-1].content, tool_call_id=tool_call_id)]
    })

@tool("delegate_to_test_agent", description="Delegate testing tasks to the test specialist")  
def call_test_agent(
    task: str,
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    result = test_agent.invoke({"messages": [{"role": "user", "content": task}]})
    return Command(update={
        "messages": [ToolMessage(content=result["messages"][-1].content, tool_call_id=tool_call_id)]
    })

# Crear supervisor
supervisor = create_agent(
    model="google_genai:gemini-2.0-flash",
    tools=[call_coding_agent, call_test_agent],
    system_prompt="""You are a team supervisor managing a coding expert and a test expert.
    Delegate coding tasks to the coding agent and testing tasks to the test agent.
    Coordinate their work to complete features incrementally."""
)
```

### 4.3 Patrón Swarm

En un swarm, todos los agentes están al mismo nivel y sus relaciones se definen mediante handoff tools explícitos:

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent  # Aún soportado para swarm
from langgraph_swarm import create_handoff_tool, create_swarm
from langgraph.checkpoint.memory import InMemorySaver

model = ChatOpenAI(model="gpt-4o")

# Agente de Coding
coding_agent = create_react_agent(
    model,
    tools=[
        file_edit, 
        bash_run,
        create_handoff_tool(agent_name="TestAgent", description="Hand off to test agent when code is ready")
    ],
    prompt="You are a coding specialist. Implement features and hand off to TestAgent when ready.",
    name="CodingAgent"
)

# Agente de Testing
test_agent = create_react_agent(
    model,
    tools=[
        run_tests,
        playwright_test,
        create_handoff_tool(agent_name="CodingAgent", description="Hand back to coding if tests fail")
    ],
    prompt="You are a test specialist. Validate implementations and hand back if issues found.",
    name="TestAgent"
)

# Crear swarm
checkpointer = InMemorySaver()
workflow = create_swarm(
    [coding_agent, test_agent],
    default_active_agent="CodingAgent"
)
app = workflow.compile(checkpointer=checkpointer)

# El swarm recuerda qué agente estaba activo
config = {"configurable": {"thread_id": "feature-001"}}
turn_1 = app.invoke({"messages": [{"role": "user", "content": "Implement login feature"}]}, config)
# Siguiente mensaje continúa con el último agente activo
turn_2 = app.invoke({"messages": [{"role": "user", "content": "Check if tests pass"}]}, config)
```

### 4.4 Benchmarks: Supervisor vs Swarm

Según benchmarks de LangChain (Junio 2025):

- **Swarm usa ~40% menos latencia** que supervisor debido a la eliminación del intermediario
- **Supervisor usa más tokens** debido a la "traducción" entre agentes
- **Single-agent baseline** performa mejor cuando hay solo 1-2 dominios
- **Multi-agent** (supervisor o swarm) escala mejor cuando hay 3+ dominios especializados

---

## 5. Integración MCP (Model Context Protocol)

### 5.1 langchain-mcp-adapters

La librería oficial para integrar MCP con LangChain/LangGraph:

```bash
pip install langchain-mcp-adapters
```

### 5.2 MultiServerMCPClient

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

client = MultiServerMCPClient({
    # MCP Server via stdio (local subprocess)
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/project"],
        "transport": "stdio"
    },
    # MCP Server via HTTP (remote)
    "github": {
        "url": "https://api.githubcopilot.com/mcp/",
        "transport": "streamable_http",
        "headers": {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    },
    # Git MCP server
    "git": {
        "command": "uvx",
        "args": ["mcp-server-git", "--repository", "/project"],
        "transport": "stdio"
    }
})

# Cargar todas las tools de todos los servidores
tools = await client.get_tools()

# Crear agente con MCP tools
agent = create_agent("google_genai:gemini-2.0-flash", tools)

# Usar el agente
response = await agent.ainvoke({
    "messages": [{"role": "user", "content": "Create a new branch called feature/auth"}]
})
```

### 5.3 Transportes Disponibles

| Transporte | Descripción | Uso |
|------------|-------------|-----|
| `stdio` | Subprocess local, comunicación via stdin/stdout | Tools locales, setups simples |
| `streamable_http` | Servidor HTTP independiente | Conexiones remotas, múltiples clientes |
| `sse` | Server-Sent Events | Streaming en tiempo real |

### 5.4 MCP Servers Esenciales para Coding Agents

| Server | Propósito | Instalación |
|--------|-----------|-------------|
| **Filesystem** | Read/write archivos | `npx @modelcontextprotocol/server-filesystem` |
| **Git** | Commits, branches, diffs | `uvx mcp-server-git` |
| **GitHub** | PRs, issues, code review | API HTTP via GitHub Copilot |
| **Memory** | Knowledge graph persistence | `npx @modelcontextprotocol/server-memory` |

---

## 6. Checkpointing y Persistencia

### 6.1 Checkpointers Disponibles (v3.0.x)

Los checkpointers ahora viven en packages separados:

```bash
pip install langgraph-checkpoint-sqlite   # Para desarrollo/MVP
pip install langgraph-checkpoint-postgres  # Para producción
```

### 6.2 SQLite Checkpointer (MVP)

```python
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

# Crear conexión
conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)

# O usar context manager
from langgraph.checkpoint.sqlite import SqliteSaver
with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    app = agent.compile(checkpointer=checkpointer)
    # Usar app...
```

### 6.3 PostgreSQL Checkpointer (Producción)

```python
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgres://user:pass@localhost:5432/dbname?sslmode=disable"

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    # IMPORTANTE: Llamar setup() la primera vez
    checkpointer.setup()
    
    app = agent.compile(checkpointer=checkpointer)
    
    config = {"configurable": {"thread_id": "feature-001"}}
    result = app.invoke({"messages": [...]}, config)
```

**Importante para PostgreSQL**:
- Usar `autocommit=True` y `row_factory=dict_row` si creas conexiones manualmente
- Llamar `.setup()` la primera vez para crear tablas

### 6.4 Async Checkpointers

```python
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async with aiosqlite.connect("checkpoints.db") as conn:
    checkpointer = AsyncSqliteSaver(conn)
    app = agent.compile(checkpointer=checkpointer)
    result = await app.ainvoke({"messages": [...]}, config)
```

### 6.5 LangGraph Store para Long-Term Memory

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

# Short-term memory (por thread)
checkpointer = InMemorySaver()

# Long-term memory (cross-thread)
store = InMemoryStore()

app = agent.compile(
    checkpointer=checkpointer,
    store=store
)
```

---

## 7. Arquitectura Propuesta: 4 Agentes para Chatbot Clone

### 7.1 Visión General

```
┌─────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                              │
│                  (LangGraph StateGraph)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  │ INITIALIZER  │  │   CODING     │  │    TEST      │  │   QA/DOC     │
│  │    AGENT     │→ │    AGENT     │→ │    AGENT     │→ │    AGENT     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
│        ↓                 ↓                 ↓                 ↓
│  - feature_list    - file_edit       - run_tests       - review_code
│  - init_script     - bash_run        - playwright      - update_docs
│  - progress_log    - git_commit      - validate_ui     - update_log
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                     SHARED STATE                                 │
│  - feature_list: list[Feature]                                   │
│  - progress_log: list[LogEntry]                                  │
│  - current_feature: Feature | None                               │
│  - git_snapshot: str                                             │
│  - messages: list[Message]                                       │
├─────────────────────────────────────────────────────────────────┤
│                   PERSISTENCE LAYER                              │
│  - PostgresSaver (checkpoints)                                   │
│  - InMemoryStore (long-term memory)                              │
│  - Git repository (code versioning)                              │
│  - MCP Servers (GitHub, Filesystem, Git)                         │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Definición de Estado

```python
from typing import TypedDict, Annotated, Literal
from langgraph.graph import add_messages

class Feature(TypedDict):
    id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    status: Literal["pending", "in_progress", "testing", "done", "failed"]
    priority: int

class LogEntry(TypedDict):
    timestamp: str
    agent: str
    feature_id: str
    action: str
    commit: str | None
    notes: str

class ChatbotCloneState(TypedDict):
    """Estado compartido entre todos los agentes"""
    # Core state
    messages: Annotated[list, add_messages]
    feature_list: list[Feature]
    progress_log: list[LogEntry]
    current_feature: Feature | None
    
    # Git/repo state
    git_snapshot: str
    repo_path: str
    
    # Workflow control
    phase: Literal["init", "coding", "testing", "qa", "complete"]
    retry_count: int
    
    # Context for agents
    init_script_path: str | None
    last_test_result: dict | None
```

### 7.3 Implementación de Agentes

```python
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient

# Model-agnostic
model = init_chat_model("google_genai:gemini-2.0-flash", temperature=0)

# MCP Client para todos los agentes
mcp_client = MultiServerMCPClient({
    "github": {
        "url": "https://api.githubcopilot.com/mcp/",
        "transport": "streamable_http",
        "headers": {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    },
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/project"],
        "transport": "stdio"
    },
    "git": {
        "command": "uvx",
        "args": ["mcp-server-git", "--repository", "/project"],
        "transport": "stdio"
    }
})

mcp_tools = await mcp_client.get_tools()

# ============ INITIALIZER AGENT ============
@tool
def create_feature_list(project_description: str) -> list[dict]:
    """Analiza el proyecto y genera una lista estructurada de features"""
    # Implementación...
    pass

@tool
def create_init_script(repo_path: str) -> str:
    """Crea script init.sh para levantar el proyecto"""
    # Implementación...
    pass

initializer_agent = create_agent(
    model,
    tools=[create_feature_list, create_init_script, *mcp_tools],
    system_prompt="""You are the Initializer Agent. Your job is to:
    1. Create a git repository for the project
    2. Generate a comprehensive feature list in JSON format (200+ features for a chatbot clone)
    3. Create init.sh script for starting development servers
    4. Write initial progress_log.json
    5. Create the initial commit
    
    CRITICAL: Generate features that are atomic and testable. Each feature should be completable in one session.
    Format features as JSON with: id, title, description, acceptance_criteria, status, priority.
    """
)

# ============ CODING AGENT ============
@tool
def select_next_feature(feature_list: list[dict]) -> dict:
    """Selecciona la siguiente feature pendiente de mayor prioridad"""
    pending = [f for f in feature_list if f["status"] == "pending"]
    return min(pending, key=lambda f: f["priority"]) if pending else None

coding_agent = create_agent(
    model,
    tools=[select_next_feature, *mcp_tools],
    system_prompt="""You are the Coding Agent. At the start of each session:
    1. Read git logs and progress_log.json
    2. Run init.sh to start servers
    3. Run basic E2E test to verify working state
    4. Select ONE highest-priority incomplete feature
    5. Implement the feature incrementally
    6. Run unit tests locally
    7. Commit with descriptive message
    
    CRITICAL: Only implement ONE feature per session. Leave the codebase in a clean, mergeable state.
    Never modify or remove existing tests.
    """
)

# ============ TEST AGENT ============
@tool
def run_playwright_tests(test_spec: str) -> dict:
    """Ejecuta tests E2E con Playwright"""
    import subprocess
    result = subprocess.run(
        ["npx", "playwright", "test", test_spec],
        capture_output=True, text=True
    )
    return {
        "passed": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr
    }

test_agent = create_agent(
    model,
    tools=[run_playwright_tests, *mcp_tools],
    system_prompt="""You are the Test Agent. Your job is to:
    1. Receive feature specification and code changes from Coding Agent
    2. Generate appropriate test cases based on acceptance criteria
    3. Run E2E tests with Playwright (browser automation)
    4. Only mark feature as "done" if ALL tests pass
    5. If tests fail, return detailed error report
    
    CRITICAL: Use browser automation to test features as a user would. 
    Unit tests alone are NOT sufficient for marking a feature complete.
    """
)

# ============ QA/DOC AGENT ============
@tool
def review_code_quality(file_paths: list[str]) -> dict:
    """Ejecuta linters y análisis estático"""
    import subprocess
    results = {}
    for path in file_paths:
        lint_result = subprocess.run(["ruff", "check", path], capture_output=True, text=True)
        results[path] = {"passed": lint_result.returncode == 0, "issues": lint_result.stdout}
    return results

@tool
def update_progress_log(entry: dict) -> str:
    """Actualiza el log de progreso con una nueva entrada"""
    import json
    with open("/project/progress_log.json", "r+") as f:
        log = json.load(f)
        log.append(entry)
        f.seek(0)
        json.dump(log, f, indent=2)
    return "Progress log updated"

qa_doc_agent = create_agent(
    model,
    tools=[review_code_quality, update_progress_log, *mcp_tools],
    system_prompt="""You are the QA/Documentation Agent. Your job is to:
    1. Review code quality (linting, style)
    2. Validate acceptance criteria are met
    3. Generate documentation for completed features
    4. Update progress_log.json with completion status
    5. Update feature_list.json to mark feature as "done"
    6. Create or update CHANGELOG.md
    
    CRITICAL: Be thorough but efficient. Flag technical debt for future sprints.
    """
)
```

### 7.4 Workflow Orchestration con LangGraph

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

def create_multi_agent_workflow():
    workflow = StateGraph(ChatbotCloneState)
    
    # Añadir nodos
    workflow.add_node("initializer", initializer_agent)
    workflow.add_node("coding", coding_agent)
    workflow.add_node("testing", test_agent)
    workflow.add_node("qa_doc", qa_doc_agent)
    
    # Router function
    def route_after_init(state: ChatbotCloneState) -> str:
        if state.get("feature_list") and len(state["feature_list"]) > 0:
            return "coding"
        return END
    
    def route_after_coding(state: ChatbotCloneState) -> str:
        if state.get("current_feature"):
            return "testing"
        return END  # No more features
    
    def route_after_testing(state: ChatbotCloneState) -> str:
        if state.get("last_test_result", {}).get("passed"):
            return "qa_doc"
        # Tests failed - back to coding
        return "coding"
    
    def route_after_qa(state: ChatbotCloneState) -> str:
        # Check if all features done
        pending = [f for f in state["feature_list"] if f["status"] != "done"]
        if not pending:
            return END
        return "coding"  # Continue with next feature
    
    # Añadir edges
    workflow.add_edge(START, "initializer")
    workflow.add_conditional_edges("initializer", route_after_init)
    workflow.add_conditional_edges("coding", route_after_coding)
    workflow.add_conditional_edges("testing", route_after_testing)
    workflow.add_conditional_edges("qa_doc", route_after_qa)
    
    return workflow

# Compilar con persistencia
workflow = create_multi_agent_workflow()

DB_URI = "postgres://user:pass@localhost:5432/chatbot_clone"
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()
    app = workflow.compile(checkpointer=checkpointer)
    
    # Ejecutar
    config = {"configurable": {"thread_id": "chatbot-v1"}}
    result = app.invoke({
        "messages": [{"role": "user", "content": "Build a Claude.ai clone with chat, history, and streaming"}],
        "phase": "init"
    }, config)
```

---

## 8. Implementación del MVP

### 8.1 Tech Stack Recomendado

| Componente | Elección MVP | Costo Mensual |
|------------|--------------|---------------|
| **Framework** | LangGraph 1.0 + deepagents | Free |
| **Persistencia** | SQLite → PostgreSQL | $0-25 |
| **Sandboxing** | E2B (Hobby tier) | $0-50 |
| **Queue** | RQ + Redis (Upstash) | $0-25 |
| **Testing** | Playwright | Free |
| **Observability** | LangSmith | Free tier |
| **MCP** | langchain-mcp-adapters | Free |

**Total infraestructura MVP**: $0-100/month antes de costos de API.

### 8.2 Dependencias

```bash
# Core
pip install langchain langgraph deepagents

# Checkpointers
pip install langgraph-checkpoint-sqlite  # MVP
pip install langgraph-checkpoint-postgres  # Producción

# MCP
pip install langchain-mcp-adapters

# Model providers (instalar según necesidad)
pip install langchain-google-genai  # Gemini
pip install langchain-anthropic     # Claude
pip install langchain-openai        # GPT

# Testing
pip install playwright
playwright install

# Utilities
pip install python-dotenv pydantic
```

### 8.3 Estructura de Proyecto

```
chatbot-clone-builder/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── initializer.py      # Initializer Agent
│   │   ├── coding.py           # Coding Agent
│   │   ├── testing.py          # Test Agent
│   │   └── qa_doc.py           # QA/Doc Agent
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── file_tools.py       # File manipulation
│   │   ├── git_tools.py        # Git operations
│   │   ├── test_tools.py       # Test execution
│   │   └── mcp_setup.py        # MCP client config
│   ├── state/
│   │   ├── __init__.py
│   │   └── schemas.py          # TypedDict state schemas
│   ├── workflow/
│   │   ├── __init__.py
│   │   └── orchestrator.py     # LangGraph workflow
│   └── main.py                 # Entry point
├── config/
│   ├── mcp_servers.json        # MCP server configurations
│   └── prompts/                # System prompts for agents
├── tests/
│   ├── unit/
│   └── e2e/
├── output/                     # Generated chatbot code
├── .env
├── pyproject.toml
└── README.md
```

### 8.4 Timeline de Implementación

| Fase | Semanas | Entregables |
|------|---------|-------------|
| **1. Foundation** | 1-4 | LangGraph setup, MCP integration, SQLite checkpointing, Initializer agent |
| **2. Core Loop** | 5-8 | Coding agent, E2B sandbox, context compaction, Initializer → Coding handoff |
| **3. Verification** | 9-12 | Test agent con Playwright, QA agent, Doc agent |
| **4. Production** | 13-16 | PostgreSQL migration, LangSmith tracing, rate limiting, error handling |

---

## 9. Prompt para Claude Code

El siguiente prompt está diseñado para ser usado con Claude Code o un agente de coding para implementar el sistema completo:

```markdown
# Multi-Agent System Implementation Prompt

## Context
You are implementing a multi-agent system for building a chatbot clone (similar to Claude.ai) using:
- **LangGraph 1.0** as the runtime
- **LangChain 1.0** with `create_agent` API and middleware
- **deepagents** for long-running task capabilities
- **MCP** (Model Context Protocol) for GitHub, filesystem, and git integration
- **Gemini 2.0 Flash** as the primary model (model-agnostic design)

## Architecture Overview
The system has 4 specialized agents working in shifts:
1. **Initializer Agent**: Creates repo, feature list (JSON), init.sh, progress log
2. **Coding Agent**: Implements one feature per session, commits changes
3. **Test Agent**: Validates with Playwright E2E tests
4. **QA/Doc Agent**: Reviews quality, updates docs and progress log

## Technical Requirements

### State Management
- Use TypedDict for state schema (Pydantic NOT supported in LangChain 1.0)
- Include: feature_list, progress_log, current_feature, git_snapshot, messages

### Agent Creation
```python
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

model = init_chat_model("google_genai:gemini-2.0-flash", temperature=0)
agent = create_agent(model, tools=[...], system_prompt="...")
```

### MCP Integration
```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "github": {"url": "...", "transport": "streamable_http", "headers": {...}},
    "filesystem": {"command": "npx", "args": [...], "transport": "stdio"},
    "git": {"command": "uvx", "args": [...], "transport": "stdio"}
})
tools = await client.get_tools()
```

### Checkpointing
```python
from langgraph.checkpoint.sqlite import SqliteSaver  # MVP
from langgraph.checkpoint.postgres import PostgresSaver  # Production

checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
app = workflow.compile(checkpointer=checkpointer)
```

### Workflow
```python
from langgraph.graph import StateGraph, START, END

workflow = StateGraph(ChatbotCloneState)
workflow.add_node("initializer", initializer_agent)
workflow.add_node("coding", coding_agent)
# ... add conditional edges for routing
```

## Implementation Tasks

1. **Create project structure** following the layout specified
2. **Implement state schemas** in `src/state/schemas.py`
3. **Set up MCP client** in `src/tools/mcp_setup.py`
4. **Implement each agent** in `src/agents/`
5. **Create workflow orchestrator** in `src/workflow/orchestrator.py`
6. **Add entry point** in `src/main.py`
7. **Write tests** for agent functionality

## Critical Patterns to Follow

### Feature List Format (JSON)
```json
{
  "id": "f-0001",
  "title": "User can send a message",
  "description": "POST /chat endpoint that receives user message and returns response",
  "acceptance_criteria": [
    "Endpoint responds with 200",
    "Response includes assistant message",
    "Message appears in UI"
  ],
  "status": "pending",
  "priority": 1
}
```

### Progress Log Entry
```json
{
  "timestamp": "2025-11-26T18:00:00Z",
  "agent": "coding-agent",
  "feature_id": "f-0001",
  "action": "implemented",
  "commit": "abc123",
  "notes": "Added POST /chat endpoint with basic validation"
}
```

### Single Feature Per Session
Each Coding Agent session must:
1. Read current state (git log, progress log)
2. Select ONE pending feature
3. Implement it completely
4. Run local tests
5. Commit with descriptive message
6. Update progress log

### Clean State Invariant
Every session must end with the codebase in a mergeable state:
- All tests passing (or explicitly marked as TODO)
- No uncommitted changes
- Progress log updated

## Output
Generate the complete implementation with all files needed to run the multi-agent system.
Focus on clean, modular code that follows LangChain 1.0 and LangGraph 1.0 best practices.
```

---

## 10. Conclusión

**El sistema multi-agente propuesto es técnicamente factible y cost-effective con el ecosistema LangChain/LangGraph 1.0.**

### Puntos Clave

1. **LangGraph 1.0** provee el runtime durable necesario para tareas long-running
2. **LangChain 1.0** simplifica la creación de agentes con `create_agent` y middleware
3. **deepagents** es el "agent harness" recomendado para tareas complejas con planning y filesystem
4. **MCP integration** via `langchain-mcp-adapters` conecta GitHub, filesystem, y git sin wrappers custom
5. **El patrón de 4 agentes** (Initializer, Coding, Test, QA/Doc) mapea directamente al harness de Anthropic

### Timeline Realista
- **MVP funcional**: 10-12 semanas con 1-2 developers
- **Production-ready**: 14-16 semanas con testing y hardening

### Costos Estimados
- **Infraestructura**: $0-100/month
- **API costs** (Gemini/Claude): $100-500 para construir el chatbot inicial (dependiendo de la complejidad)

### Siguiente Paso
Usar el prompt de la Sección 9 con Claude Code o un sistema de agentes para implementar el MVP.