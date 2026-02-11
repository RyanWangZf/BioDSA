# BioDSA Agent Development Skill

## When to Use This Skill

Use this skill when the user wants to:
- Create a **new agent** in the BioDSA framework
- Understand the **agent architecture** (BaseAgent, state, tools, graphs)
- Implement a **single-agent** or **multi-agent** workflow
- Add new **tools or tool wrappers** for an agent
- Create a **run script** for an agent
- Make a new agent pass a **sanity check**
- Understand what the **deliverables** look like for prototyping an agent
- **Build an agent from reference materials** (paper PDFs, design docs, or any knowledge folder)
- **Build an agent and evaluate it on benchmark datasets** (from `benchmarks/`)

## Repository Overview

BioDSA is a framework for building biomedical data science agents. The codebase provides:
- A `BaseAgent` class that handles LLM initialization, sandbox management, and workspace setup
- LangGraph-based agent workflows (single-agent loops, multi-stage pipelines, multi-agent orchestration)
- 17+ biomedical knowledge base integrations (PubMed, ChEMBL, UniProt, Open Targets, Ensembl, etc.)
- A Docker-based sandbox for safe code execution
- An `ExecutionResults` class for structured output and PDF report generation

## Key Paths

| What                     | Path                                           |
| ------------------------ | ---------------------------------------------- |
| Base agent class         | `biodsa/agents/base_agent.py`                  |
| Shared agent state       | `biodsa/agents/state.py`                       |
| Agent implementations    | `biodsa/agents/<agent_name>/`                  |
| Low-level API tools      | `biodsa/tools/<knowledge_base>/`               |
| LangChain tool wrappers  | `biodsa/tool_wrappers/<domain>/`               |
| Sandbox / code execution | `biodsa/sandbox/`                              |
| ExecutionResults         | `biodsa/sandbox/execution.py`                  |
| Agent exports            | `biodsa/agents/__init__.py`                    |
| Run scripts              | `run_<agent_name>.py` (top-level)              |
| Benchmarks               | `benchmarks/`                                  |
| Tests                    | `tests/`                                       |

## Skill Library Contents

This skill library is organized into seven guides:

| Guide | File | What It Covers |
| ----- | ---- | -------------- |
| 0 | [00-environment-setup.md](./00-environment-setup.md) | **Automatic** environment setup: conda env, pipenv install, `.env` configuration, Docker sandbox — run this before anything else if the env is not ready |
| 1 | [01-base-agent.md](./01-base-agent.md) | `BaseAgent` class, constructor, key methods, LLM initialization, sandbox lifecycle |
| 2 | [02-single-agent.md](./02-single-agent.md) | How to subclass `BaseAgent` for a single-agent workflow (ReAct loop, multi-stage pipeline, custom workflow) |
| 3 | [03-multi-agent.md](./03-multi-agent.md) | Multi-agent patterns: orchestrator + sub-agents, multi-participant meetings |
| 4 | [04-tools-and-wrappers.md](./04-tools-and-wrappers.md) | How to create tools (`biodsa/tools/`), wrap them as LangChain tools (`biodsa/tool_wrappers/`), and wire them into agents |
| 5 | [05-deliverables-and-testing.md](./05-deliverables-and-testing.md) | What a completed agent prototype looks like: folder structure, `__init__.py` exports, run script, `ExecutionResults`, PDF reports, sanity checks |
| 6 | [06-user-workflows.md](./06-user-workflows.md) | Two common development workflows: building from reference materials, and building for benchmark evaluation |

## Quick-Start Checklist for Creating a New Agent

When a user asks you to create a new agent, follow these steps in order:

### Phase 0: Ensure Environment is Ready

Before writing any code, verify the BioDSA environment is set up. Read [00-environment-setup.md](./00-environment-setup.md) and run the checks. If the environment is not ready (no conda/pipenv env, missing dependencies, no `.env`), **set it up automatically** — do not ask the user to do it manually.

### Phase 1: Propose Before Building

**IMPORTANT**: Do NOT start implementing immediately. First present a design proposal to the user and wait for their feedback.

1. **Identify the workflow** — Read [06-user-workflows.md](./06-user-workflows.md) to determine if this is a "from reference materials" or "benchmark-driven" task.
2. **Read the guides** — Read the relevant `.md` files in this directory to understand the patterns.
3. **Present a design proposal** — Before writing any code, present the user with a structured proposal covering:
   - **What you understood**: Restate the user's goal in your own words
   - **Agent pattern**: Which BioDSA pattern you'll use (ReAct, multi-stage pipeline, orchestrator, etc.) and why
   - **Workflow diagram**: A text or Mermaid flowchart of the proposed graph structure
   - **Tools**: Which existing tools from `biodsa/tools/` and `biodsa/tool_wrappers/` you'll reuse, and which new tools you need to create
   - **State fields**: Key domain-specific state fields beyond the default `messages`
   - **Input/Output**: What the agent takes as input and what it produces
   - **Open questions**: Anything unclear that would change the design (e.g., "Should the agent execute code in a sandbox or just reason?", "Do you want a single-agent loop or a multi-stage pipeline?")

   Wait for the user to confirm, adjust, or answer questions before proceeding.

### Phase 2: Implement

4. **Create the agent folder** — `biodsa/agents/<agent_name>/` with `__init__.py`, `agent.py`, `state.py`, `prompt.py`, `tools.py`, and `README.md`.
5. **Define the state** — Subclass `BaseModel` with `messages: Annotated[Sequence[BaseMessage], add_messages]` plus any domain-specific fields.
6. **Define the prompts** — System prompts as module-level string constants in `prompt.py`.
7. **Define the tools** — Either reuse existing tools from `biodsa/tools/` / `biodsa/tool_wrappers/`, or create new `BaseTool` subclasses in `tools.py` with Pydantic input schemas.
8. **Implement the agent** — Subclass `BaseAgent`, implement `__init__`, `_create_agent_graph`, `generate`, and `go`.
9. **Export the agent** — Add to `biodsa/agents/<agent_name>/__init__.py` and optionally to `biodsa/agents/__init__.py`.
10. **Create the run script** — `run_<agent_name>.py` at the repo root with an example invocation.

### Phase 3: Document and Verify

11. **Generate the design doc** — Create `biodsa/agents/<agent_name>/DESIGN.md` with Mermaid diagrams explaining the agent's architecture. See [05-deliverables-and-testing.md](./05-deliverables-and-testing.md) for the template.
12. **Sanity check** — Run the script end-to-end. Verify it produces an `ExecutionResults` with a non-empty `final_response`.
13. **(If benchmark-driven)** — Write an evaluation script that loads benchmark data and runs the agent on it. See [06-user-workflows.md](./06-user-workflows.md).

## Agent Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                    BaseAgent                         │
│  - LLM initialization (OpenAI/Azure/Anthropic/Google)│
│  - Sandbox management (Docker)                      │
│  - Workspace registration (upload datasets)         │
│  - Helper methods (_call_model, _format_messages)   │
└──────────────┬──────────────────────────────────────┘
               │ inherits
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌────────────┐   ┌─────────────────┐
│ Single     │   │ Multi-Agent     │
│ Agent      │   │ Framework       │
│            │   │                 │
│ ReactAgent │   │ DeepEvidence    │
│ CoderAgent │   │ VirtualLab     │
│ AgentMD    │   │                 │
│ TrialGPT   │   │ (orchestrator + │
│ GeneAgent  │   │  sub-workflows) │
│ InformGen  │   │                 │
│ TrialMind  │   │                 │
└────────────┘   └─────────────────┘
    │                     │
    ▼                     ▼
┌─────────────────────────────────────────────────────┐
│              LangGraph StateGraph                   │
│  Nodes → Edges → Conditional Edges → Compile        │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                 Tools Layer                          │
│  biodsa/tools/        → Pure API functions          │
│  biodsa/tool_wrappers/→ LangChain BaseTool wrappers │
│  Agent-specific tools → biodsa/agents/<name>/tools.py│
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│              ExecutionResults                        │
│  message_history + code_execution_results +         │
│  final_response → to_json() / to_pdf()              │
└─────────────────────────────────────────────────────┘
```
