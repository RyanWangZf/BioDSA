# BioDSA Agent Execution Skill

## Core Principle

**Write the script AND run it.** When a user asks to execute a BioDSA agent, do NOT just hand them a script and tell them to run it themselves. You must:
1. Write the execution script
2. **Run the script** via the terminal to start the agent
3. Monitor the output and report the results back to the user
4. Collect and present the deliverables (JSON, PDF, artifacts)

This is the key difference from the dev skill — the exec skill is about **completing the task end-to-end**, not just scaffolding code.

## When to Use This Skill

Use this skill when the user wants to:
- **Run an existing BioDSA agent** on a task (not build a new one)
- **Execute a biomedical task** using an agent and get results
- **Pick the right agent** for a given biomedical task
- **Run agents in batch** over datasets or benchmark files
- **Chain agent runs** (feed one agent's output into another)

Do NOT use this skill for creating new agents — use the `biodsa-agent-dev-skills` for that.

## Agent Catalog

These agents are available in BioDSA. Read [01-agent-catalog.md](./01-agent-catalog.md) for full details on each.

| Agent | Best For | Import |
|-------|----------|--------|
| **DSWizardAgent** | Data analysis on biomedical datasets (CSV, tables) | `from biodsa.agents import DSWizardAgent` |
| **DeepEvidenceAgent** | Deep research across 17+ biomedical knowledge bases | `from biodsa.agents import DeepEvidenceAgent` |
| **CoderAgent** | Direct code generation + sandbox execution | `from biodsa.agents import CoderAgent` |
| **ReactAgent** | Tool-calling ReAct loop for general tasks | `from biodsa.agents import ReactAgent` |
| **TrialMindSLRAgent** | Systematic literature review (search → screen → extract → synthesize) | `from biodsa.agents.trialmind_slr import TrialMindSLRAgent` |
| **SLRMetaAgent** | Systematic review + meta-analysis with forest plots | `from biodsa.agents import SLRMetaAgent` |
| **InformGenAgent** | Clinical/regulatory document generation | `from biodsa.agents.informgen import InformGenAgent` |
| **TrialGPTAgent** | Patient-to-clinical-trial matching | `from biodsa.agents.trialgpt import TrialGPTAgent` |
| **AgentMD** | Clinical risk prediction with medical calculators | `from biodsa.agents.agentmd import AgentMD` |
| **GeneAgent** | Gene set analysis with self-verification | `from biodsa.agents.geneagent import GeneAgent` |
| **VirtualLabAgent** | Multi-agent scientific discussion meetings | `from biodsa.agents import VirtualLabAgent` |

## Model Selection — Use Frontier Models

**IMPORTANT**: BioDSA agents perform complex multi-step biomedical reasoning. Always use **frontier-tier models** to ensure high-quality results. Weaker models (gpt-4o, gpt-4o-mini, claude-sonnet, etc.) produce significantly worse results and should be avoided unless the user explicitly requests them.

| Provider | Recommended Model | Avoid |
|----------|------------------|-------|
| Azure OpenAI | `"gpt-5"` | `"gpt-4o"`, `"gpt-4o-mini"` |
| OpenAI | `"gpt-5"` | `"gpt-4o"`, `"gpt-4o-mini"` |
| Anthropic | `"claude-opus-4-20250514"` | `"claude-sonnet-4-20250514"` |
| Google | `"gemini-2.5-pro"` | `"gemini-2.0-flash"` |

When reading the user's `.env` file, check the `MODEL_NAME` value. If it is set to a weaker model, **warn the user** that it may produce poor results and suggest upgrading.

## Quick-Start: Running an Agent

When a user describes a task, follow these steps **in order**:

### Step 0: Ensure Environment is Ready

Before anything, verify the BioDSA environment is set up. Read [00-environment-setup.md](./00-environment-setup.md) and run the checks. If the environment is not ready (no conda/pipenv env, missing dependencies, no `.env`), **set it up automatically** — do not ask the user to do it manually. This includes:
- Creating an isolated conda/pipenv environment (never install into the user's base Python)
- Running `pipenv install` to install all dependencies
- Configuring `.env` with API keys
- Optionally building the Docker sandbox

### Step 1: Check Model Configuration

Verify the `.env` file has `MODEL_NAME` set to a **frontier model** (see Model Selection above). If it is set to a weaker model like `gpt-4o` or `gpt-4o-mini`, warn the user and suggest upgrading to `gpt-5` / `claude-opus-4-20250514` / `gemini-2.5-pro`.

### Step 2: Pick the Agent

Match the user's task to the right agent from the catalog above. See [01-agent-catalog.md](./01-agent-catalog.md) for the full decision guide and `go()` signatures.

### Step 3: Write the Script

Generate a complete Python script at the repo root (e.g., `run_task.py`). Follow the patterns in [02-execution-patterns.md](./02-execution-patterns.md). Use the template below.

### Step 4: Run the Script

**IMPORTANT**: Do NOT stop after writing the script. Execute it immediately:

```bash
cd /path/to/BioDSA
python run_task.py
```

Monitor the output. Agent runs can take seconds to minutes depending on complexity. Wait for the script to complete.

### Step 5: Report Results

After the script finishes:
- Show the user the `final_response` from the terminal output
- Tell the user where deliverables were saved (JSON, PDF, artifacts)
- If the run failed, diagnose the error and fix the script, then re-run
- If the run succeeded, summarize the key findings for the user

### Execution Template

Every agent script follows this skeleton:

```python
import sys, os
REPO_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))

from biodsa.agents import <AgentClass>

agent = <AgentClass>(
    model_name=os.environ.get("MODEL_NAME", "gpt-5"),
    api_type=os.environ.get("API_TYPE", "azure"),
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

# (Optional) Register data for analysis agents
# agent.register_workspace("/path/to/data")

results = agent.go("<user's task description>")

# Save deliverables
os.makedirs("output", exist_ok=True)
print(results.final_response)
results.to_json(output_path="output/results.json")
results.to_pdf(output_dir="output")
```

### What "Done" Looks Like

You are NOT done until:
- The script has been **written to a file**
- The script has been **executed** in the terminal
- The agent has **finished running** and produced output
- You have **reported the results** (or the error) back to the user

## Skill Library Contents

| Guide | File | What It Covers |
| ----- | ---- | -------------- |
| 0 | [00-environment-setup.md](./00-environment-setup.md) | **Automatic** environment setup: conda env, pipenv install, `.env` configuration, Docker sandbox — run this before anything else if the env is not ready |
| 1 | [01-agent-catalog.md](./01-agent-catalog.md) | All available agents: when to use each, import paths, `go()` signatures, required parameters |
| 2 | [02-execution-patterns.md](./02-execution-patterns.md) | LLM configuration, model selection, workspace registration, single runs, batch runs, chaining agents |
| 3 | [03-output-and-deliverables.md](./03-output-and-deliverables.md) | `ExecutionResults` API, PDF reports, JSON export, artifact download, specialized result types |

## Key Paths

| What | Path |
| ---- | ---- |
| Agent imports | `biodsa/agents/__init__.py` |
| Agent implementations | `biodsa/agents/<agent_name>/` |
| Sandbox & ExecutionResults | `biodsa/sandbox/execution.py` |
| Example run scripts | `scripts/run_*.py` and `run_*.py` (repo root) |
| Benchmarks | `benchmarks/` |
| Example datasets | `biomedical_data/` |
| Environment config | `.env` (create from `.env.example`) |
| Tutorials | `tutorials/` |
