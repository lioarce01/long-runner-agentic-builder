# Long-Running Multi-Agent Software Builder

> **Building production-ready applications autonomously, without losing context across hours or days of development.**

---

## What This Actually Does

Point this system at a project idea. Walk away. Come back hours later to find a fully implemented, tested, documented, and Git-versioned application—complete with 15+ features, passing tests, and a detailed audit trail of every decision made.

**This isn't a code generator. This is an autonomous development team.**

---

## The Problem We Solved

Traditional AI coding assistants have a fatal flaw: **they forget**.

Every time they start a new session, they begin with a blank slate. They can't maintain context across multiple hours or days. They can't track their own progress. They make the same mistakes twice. They lose track of what features they've implemented, what tests they've written, and what's left to do.

**We built a system that remembers everything.**

---

## How It Works: The Technical Innovation

### 1. **Stateful Multi-Agent Architecture**

Instead of one monolithic AI, we use **5 specialized agents** that work together like a real development team:

```
┌─────────────────┐
│  INITIALIZER    │  Analyzes requirements, infers tech stack,
│     AGENT       │  generates 20-50 tailored features
└─────────────────┘
         ↓
┌─────────────────┐
│    GITOPS       │  Creates Git repo, initial commit,
│     AGENT       │  creates GitHub repo, first push
└─────────────────┘
         ↓
┌─────────────────┐
│    CODING       │  Implements features incrementally,
│     AGENT       │  writes clean, production-ready code
└─────────────────┘
         ↓
┌─────────────────┐
│    TESTING      │  Generates and runs E2E/API/unit tests,
│     AGENT       │  validates acceptance criteria
└─────────────────┘
         ↓
┌─────────────────┐
│    QA/DOC       │  Code quality checks, documentation,
│     AGENT       │  marks features complete
└─────────────────┘
         ↓
┌─────────────────┐
│    GITOPS       │  Commits feature changes with conventional
│     AGENT       │  commit messages, pushes to GitHub
└─────────────────┘
         ↓
    (loops back to Coding for next feature)
```

Each agent is specialized, focused, and **maintains state across sessions**.

**Key Design Decision: Dedicated GitOps Agent**

Git operations (commits, pushes, GitHub repo creation) are handled by a specialized GitOps Agent rather than being embedded in other agents. This ensures:
- **Reliable commits**: Git operations always happen, regardless of LLM behavior
- **Conventional commits**: Consistent commit message format (`feat:`, `fix:`, `docs:`, etc.)
- **Clear separation**: Coding agents focus on code, GitOps handles version control

### 2. **Long-Running Task Persistence** (The Hard Part)

This is where we diverge from typical AI coding tools. Inspired by [Anthropic's research on long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), we implemented a **dual-memory architecture**:

**Layer 1: External Persistent Memory (JSON Files)**

Every agent action writes to disk-based files serving as the system's external memory:
- `progress_log.json`: Complete audit trail with timestamps, agent name, feature ID, and decision rationale
- `feature_list.json`: Full feature state with status transitions: `pending → in_progress → testing → done`

```python
# State Synchronization Protocol:
# After EVERY agent execution:
1. Agent calls tools → updates feature_list.json on disk
2. Orchestrator syncs state from disk → in-memory state
3. Router makes decisions based on fresh state
4. Next agent starts with accurate context

# No more stale state. No more lost progress.
```

**Layer 2: Workflow Checkpointing (PostgreSQL)**

Entire workflow state checkpointed to PostgreSQL using LangGraph's built-in persistence:
- Survives crashes and restarts
- Time-travel debugging to any previous state
- Multiple parallel workflows without interference

**The Dual-Layer Approach:**
- JSON files = Agent audit trail and decision history
- PostgreSQL = Workflow orchestration state and recovery

**The Result:** An agent that worked on feature #1 yesterday can seamlessly continue with feature #15 today, knowing exactly what's been done and what's next.

### 3. **Smart Routing & Loop-Back**

The workflow doesn't just run sequentially—it **makes intelligent decisions**:

```python
# After Initializer completes...
route_after_init(state):
    return "gitops"  # Always go to GitOps for initial commit

# After GitOps completes...
route_after_gitops(state):
    if gitops_mode == "init":
        return "coding"  # Start implementing features
    elif pending_features_exist():
        return "coding"  # Next feature
    else:
        return "END"     # All done!

# After QA approves a feature...
route_after_qa(state):
    return "gitops"  # Always commit feature changes

# This enables processing 50+ features autonomously
```

**Conditional edges** handle failures too:
- Tests fail? → Retry coding (max 3 attempts)
- Quality checks fail? → Back to coding with specific feedback
- No pending features? → Workflow complete

---

## What It Can Build (Real Examples)

### ✅ E-commerce Platform (45 features, 8 hours)
- Product catalog with search and filters
- Shopping cart with session persistence
- Stripe checkout integration
- Admin dashboard
- Email notifications
- SEO optimization
- **Fully tested, documented, deployed**

### ✅ REST API (12 features, 2 hours)
- CRUD endpoints with PostgreSQL
- JWT authentication
- OpenAPI/Swagger documentation
- Rate limiting
- Docker deployment
- 95% test coverage

### ✅ Real-Time Chat App (30 features, 6 hours)
- WebSocket connections
- Message history
- User presence
- Typing indicators
- File uploads
- E2E tested with Playwright

**Every project includes:**
- Git repository with conventional commits (`feat:`, `fix:`, `docs:`)
- GitHub repository auto-created and synced
- Comprehensive test suite (E2E/API/unit)
- README with setup instructions
- CHANGELOG with feature history
- Code quality checks (linting, type checking)

---

## The Tech Stack: Why These Choices Matter

### **LangChain 1.0 + LangGraph 1.0**
- **Not just a library—a state management system** for agentic workflows
- Durable execution: Agents can run for days without losing context
- Built-in checkpointing: Survives crashes, restarts, network failures

### **PostgreSQL for Workflow State**
- Every state transition persisted
- Time-travel debugging: Rewind to any previous checkpoint
- Enables long-running tasks that traditional APIs can't handle

### **File-Based State Synchronization**
```python
sync_feature_list_from_disk(state, repo_path):
    # After agent execution:
    # 1. Read feature_list.json (source of truth)
    # 2. Update in-memory state
    # 3. Router sees fresh data for decisions
```

This pattern ensures **disk files are always the source of truth**—agents can inspect `progress_log.json` to understand what to do next, even after days of inactivity.

### **Multi-Model Support**
- **Initializer**: Claude Sonnet / Gemini for requirements analysis
- **Coding**: High-capability model for code generation
- **Testing**: Cost-effective model for test execution
- **QA/Doc**: Documentation-focused model
- **GitOps**: Lightweight model for commit message generation
- Model-agnostic design: Swap models without changing code

---

## The Key Innovations (What Makes This Different)

### 1. **No Context Loss Across Sessions**
Traditional AI: "I forgot what I was doing."
Our system: "I've completed features 1-14, currently implementing feature 15, 3 features failed testing and are marked for retry."

### 2. **Audit Trail for Everything**
Every decision, every code change, every test run—logged with timestamps and reasoning. You can trace exactly why the system made each choice.

### 3. **Self-Healing Workflows**
- Tests fail? System retries with different approaches
- Code quality issues? System refactors automatically
- Stuck in a loop? Maximum retry limits prevent infinite loops

### 4. **Dedicated GitOps Agent**
Version control is handled by a specialized agent that:
- Creates Git repositories and GitHub remotes automatically
- Generates meaningful commit messages following conventional commits
- Commits after each feature completion (not just at the end)
- Pushes to GitHub after every significant change
- Provides full traceability of code evolution

### 5. **Production-Ready Output**
This isn't prototype code. Every generated app includes:
- Error handling and validation
- Security best practices (no SQL injection, XSS protection)
- Performance optimizations (connection pooling, caching)
- Deployment configurations (Docker, environment variables)

---

## Technical Deep Dive: State Management

The hardest problem we solved was **state synchronization** across agent boundaries.

**The Challenge:**
```python
# Without sync, this happens:
Coding Agent: "I'll set feature f-001 to 'testing'"
  → Writes to feature_list.json
  → Returns to orchestrator

Router: "What features are in testing status?"
  → Reads stale state (f-001 still shows 'pending')
  → Makes wrong routing decision
  → Workflow breaks 💥
```

**Our Solution:**
```python
async def coding_node(state):
    result = await coding_graph.ainvoke(state)

    # CRITICAL: Sync state from disk after execution
    result = sync_feature_list_from_disk(result, repo_path)

    return result  # Router now sees fresh data

# Router makes correct decision ✅
```

This pattern applies after **every agent execution**, ensuring the workflow state always reflects reality.

---

## Architecture Diagrams

### State Flow
```
┌──────────────────────┐
│  Coding Agent        │
│  (implements code)   │
└──────────┬───────────┘
           │
           ↓
┌──────────────────────┐
│  Testing Agent       │
│  (validates feature) │
└──────────┬───────────┘
           │
           ↓
┌──────────────────────┐
│  QA Agent            │
│  (marks as done)     │
│  → writes to disk    │
└──────────┬───────────┘
           │
           ↓
┌──────────────────────┐
│  GitOps Agent        │
│  (commits & pushes)  │
└──────────┬───────────┘
           │
           ↓
┌──────────────────────┐
│  Router Function     │
│  (reads fresh state) │
│  → routes to Coding  │
│    or END            │
└──────────────────────┘
```

### Workflow Execution
```
User: "Build an e-commerce platform"
  ↓
Initializer: Generates 45 features, infers tech stack
  ↓ [state synced]
GitOps (INIT): Creates Git repo, initial commit, GitHub repo, push
  ↓
Coding (f-001): Implements project structure
  ↓ [state synced]
Testing (f-001): Runs tests → PASS
  ↓
QA (f-001): Quality checks → marks as DONE
  ↓ [state synced]
GitOps (FEATURE): Commits "feat(f-001): project structure" → push
  ↓ [router sees 44 pending]
Coding (f-002): Implements authentication ← LOOP BACK
  ↓
... (repeats for all 45 features)
  ↓
QA (f-045): Final feature complete
  ↓
GitOps (FEATURE): Final commit and push
  ↓ [router sees 0 pending]
END: Application complete with full Git history!
```

---

## Real-World Performance

| Metric | Value |
|--------|-------|
| **Average features per project** | 25-50 |
| **Typical runtime** | 4-12 hours |
| **Test coverage** | 75-90% |
| **Success rate** | ~85% of features complete successfully |
| **Failed features** | ~15% (marked as failed after 3 retry attempts) |
| **Context window usage** | Maintains state across 100+ LLM calls |
| **Checkpoint overhead** | <100ms per state save |

**Cost (using Gemini 2.0 Flash):**
- Small project (10 features): ~$0.50
- Medium project (30 features): ~$2.00
- Large project (50 features): ~$5.00

**Cost (using Claude Sonnet 4.5):**
- Small project: ~$5-10
- Medium project: ~$15-30
- Large project: ~$40-80

---

## What This Enables

### For Developers:
- **Prototype to production in hours, not weeks**
- Focus on architecture and business logic, not boilerplate
- Every generated app is a learning resource with best practices

### For Startups:
- **MVP in a day**
- Iterate on product ideas rapidly
- Lower technical barriers to entry

### For Research:
- **Autonomous agents that actually work on real tasks**
- Long-running task orchestration patterns
- Multi-agent collaboration at scale

---

## Limitations & Future Work

**Current Limitations:**
- Primarily Python/JavaScript projects (expanding to other languages)
- Requires human review for security-critical code
- ~15% feature failure rate on complex features
- No GUI (command-line only)

**Roadmap:**
- [x] Dedicated GitOps Agent for reliable version control
- [x] Conventional commits format
- [x] Automatic GitHub repository creation
- [ ] Research Agent for web searches and documentation lookup
- [ ] Memory management (context window optimization)
- [ ] Human-in-the-loop approval gates for critical decisions
- [ ] Web UI for non-technical users
- [ ] Multi-language support (Go, Rust, Java)
- [ ] Cost controls and budget limits
- [ ] Integration with existing codebases (not just greenfield)

---

## Getting Started

**Prerequisites:**
- Python 3.10+ (3.12 recommended)
- PostgreSQL (for workflow checkpointing)
- API keys for Google Gemini, Claude, or OpenAI
- GitHub token (for automatic repo creation)

**Quick Start:**
```bash
# 1. Navigate to backend directory
cd backend

# 2. Install dependencies
pip install -e .

# 3. Configure environment
cp .env.production.example .env
# Add your API keys:
#   GOOGLE_API_KEY=...
#   ANTHROPIC_API_KEY=...
#   GITHUB_TOKEN=...
#   DATABASE_URL=postgresql://...

# 4. Build something
python -m src.main my-project "Build a REST API for task management"

# 5. Monitor progress
tail -f ../output/my-project/progress_log.json

# 6. Check GitHub - your repo is already there!
```

**Full documentation:** See [SETUP.md](SETUP.md) for detailed installation instructions.

---

## Learn More

### Key Concepts
- [Anthropic: Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [Anthropic: Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [LangGraph: Multi-Agent Workflows](https://blog.langchain.com/langgraph-multi-agent-workflows/)

### Technical Deep Dives
- [State Management in Multi-Agent Systems](docs/STATE_MANAGEMENT.md)
- [Checkpoint Strategy & Recovery](docs/CHECKPOINTING.md)
- [Agent Orchestration Patterns](docs/ORCHESTRATION.md)

---

## Contributing

This is an experiment in autonomous software development. If you're working on similar problems—long-running agents, state management, multi-agent orchestration—**let's collaborate**.

Open an issue, submit a PR, or reach out directly.

---

## License

MIT License - Build whatever you want with this.

---

**Built with LangChain 1.0, LangGraph 1.0, and research from Anthropic's agent engineering team.**

*Making AI that builds software, so developers can focus on solving real problems.*
