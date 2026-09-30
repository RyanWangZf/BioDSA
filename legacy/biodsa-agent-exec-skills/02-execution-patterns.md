# 02 — Execution Patterns

This guide covers how to configure, run, and orchestrate BioDSA agents.

> **Remember**: Your job is to write the script **and run it** to completion. Don't just hand the script to the user — execute it, monitor it, and deliver the results.

---

## Environment Setup

> **First-time setup?** Read [00-environment-setup.md](./00-environment-setup.md) first — it covers conda env creation, pipenv install, and full verification. The section below assumes the environment is already set up.

All agents require LLM API credentials. These are read from a `.env` file at the repo root.

### `.env` File

```bash
# Choose one provider and set a frontier model:

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
API_TYPE=azure
MODEL_NAME=gpt-5          # Use gpt-5, NOT gpt-4o or gpt-4o-mini

# OpenAI direct
# OPENAI_API_KEY=your_key
# API_TYPE=openai
# MODEL_NAME=gpt-5

# Anthropic
# ANTHROPIC_API_KEY=your_key
# API_TYPE=anthropic
# MODEL_NAME=claude-opus-4-20250514    # Use opus, NOT sonnet

# Google
# GOOGLE_API_KEY=your_key
# API_TYPE=google
# MODEL_NAME=gemini-2.5-pro
```

### Loading in Scripts

```python
import sys, os

REPO_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))
```

### LLM Configuration

All agents accept the same constructor parameters:

```python
agent = SomeAgent(
    model_name="gpt-5",          # ALWAYS use frontier models — see table below
    api_type="azure",             # "azure", "openai", "anthropic", "google"
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),  # Required for Azure, optional otherwise
)
```

### Model Selection — Always Use Frontier Models

BioDSA agents perform complex multi-step biomedical reasoning (literature search, evidence synthesis, code generation, clinical matching). Using weaker models leads to **poor-quality results** — missed evidence, incorrect reasoning, broken code. Always default to frontier-tier models.

| Provider | `api_type` | **Recommended** (use these) | Avoid (poor quality) | Needs `endpoint`? |
|----------|-----------|---------------------------|---------------------|-------------------|
| Azure OpenAI | `"azure"` | **`"gpt-5"`** | `"gpt-4o"`, `"gpt-4o-mini"` | Yes |
| OpenAI | `"openai"` | **`"gpt-5"`** | `"gpt-4o"`, `"gpt-4o-mini"` | No |
| Anthropic | `"anthropic"` | **`"claude-opus-4-20250514"`** | `"claude-sonnet-4-20250514"` | No |
| Google | `"google"` | **`"gemini-2.5-pro"`** | `"gemini-2.0-flash"` | No |

**When generating scripts:**
- Default `model_name` to `"gpt-5"` (or the provider's frontier equivalent)
- If the user's `.env` has `MODEL_NAME` set to a weaker model, warn them before running
- Only use smaller models if the user explicitly asks for it (e.g., for cost reasons)

---

## Workspace Registration

Some agents need access to local data files. Use `register_workspace()` to upload files to the Docker sandbox.

```python
# Upload all CSV files from a directory to the sandbox
agent.register_workspace("./biomedical_data/cBioPortal/datasets/acbc_mskcc_2015")
```

**What it does:**
- Uploads all `.csv` files to `/workdir/<filename>.csv` inside the sandbox
- Installs `biodsa.tools` in the sandbox for in-sandbox API access
- Returns `True` if successful, `False` if sandbox unavailable (falls back to local)

**Which agents need workspace:**

| Agent | Needs Workspace? | Why |
|-------|-----------------|-----|
| DSWizardAgent | **Yes** | Analyzes uploaded CSV data |
| CoderAgent | Optional | For code that reads data files |
| ReactAgent | Optional | For tool-calling on data |
| InformGenAgent | **Yes** | Reads source documents |
| All others | No | Use external APIs/knowledge bases |

### Cleanup

After execution, free sandbox resources:

```python
agent.clear_workspace()
```

---

## Single Task Execution

The standard pattern for running an agent on one task.

### Step-by-Step Workflow

1. **Write** the script to a file at the repo root (e.g., `run_task.py`)
2. **Run** it in the terminal: `python run_task.py`
3. **Monitor** the output — agent runs can take seconds to minutes
4. **Report** the `final_response` and deliverable locations to the user
5. **If it fails** — read the error, fix the script, and re-run

### Script Template

```python
import sys, os, json

REPO_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))

from biodsa.agents import DSWizardAgent

# 1. Initialize
agent = DSWizardAgent(
    model_name=os.environ.get("MODEL_NAME", "gpt-5"),
    api_type=os.environ.get("API_TYPE", "azure"),
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

# 2. (Optional) Register data
agent.register_workspace("./biomedical_data/cBioPortal/datasets/acbc_mskcc_2015")

# 3. Run
results = agent.go("Perform survival analysis for TP53 mutant vs wild-type patients")

# 4. Output
print(results.final_response)

# 5. Save deliverables
os.makedirs("output", exist_ok=True)
results.to_json(output_path="output/results.json")
results.to_pdf(output_dir="output")
results.download_artifacts(output_dir="output/artifacts")

# 6. Cleanup
agent.clear_workspace()
```

### Running the Script

After writing the script, execute it immediately:

```bash
cd /path/to/BioDSA
python run_task.py
```

**Tips for monitoring long-running agents:**
- Agent runs may take 30 seconds to several minutes depending on complexity
- If the agent calls external APIs (PubMed, ClinicalTrials.gov, etc.), expect network latency
- The `verbose=True` default means the agent prints progress to stdout — watch for it
- If the script appears stuck for an unreasonable time (>10 minutes for a simple query), it may be worth interrupting and investigating

---

## Batch Execution

Run an agent over multiple tasks (e.g., a benchmark dataset or a list of queries):

```python
import sys, os, json, argparse
import pandas as pd

REPO_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))

from biodsa.agents import DeepEvidenceAgent


def load_tasks(path: str) -> list:
    """Load tasks from CSV, JSONL, or Parquet."""
    if path.endswith(".csv"):
        return pd.read_csv(path).to_dict("records")
    elif path.endswith(".parquet"):
        return pd.read_parquet(path).to_dict("records")
    elif path.endswith(".jsonl"):
        with open(path) as f:
            return [json.loads(line) for line in f]
    else:
        raise ValueError(f"Unsupported format: {path}")


def run_batch(agent, tasks: list, output_dir: str):
    """Run agent on each task, save incremental results."""
    os.makedirs(output_dir, exist_ok=True)

    for i, task in enumerate(tasks):
        task_id = task.get("id", task.get("data_id", i))
        question = task.get("question", task.get("queries", str(task)))

        print(f"\n[{i+1}/{len(tasks)}] Task {task_id}")
        print(f"  Q: {question[:100]}...")

        try:
            result = agent.go(question)
            prediction = result.final_response

            # Save individual result
            result.to_json(output_path=os.path.join(output_dir, f"task_{task_id}.json"))
        except Exception as e:
            prediction = f"ERROR: {e}"

        # Append to incremental log
        with open(os.path.join(output_dir, "results.jsonl"), "a") as f:
            f.write(json.dumps({
                "task_id": task_id,
                "question": question,
                "prediction": prediction,
                "ground_truth": task.get("answer", ""),
            }) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch-run a BioDSA agent")
    parser.add_argument("--tasks", required=True, help="Path to task file (CSV/JSONL/Parquet)")
    parser.add_argument("--output", default="batch_output", help="Output directory")
    parser.add_argument("--limit", type=int, default=None, help="Max tasks to run")
    args = parser.parse_args()

    agent = DeepEvidenceAgent(
        model_name=os.environ.get("MODEL_NAME", "gpt-5"),
        api_type=os.environ.get("API_TYPE", "azure"),
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    )

    tasks = load_tasks(args.tasks)
    if args.limit:
        tasks = tasks[:args.limit]

    run_batch(agent, tasks, args.output)
    print(f"\nDone. Results saved to {args.output}/")
```

---

## Chaining Agents

Some workflows require running multiple agents in sequence:

### VirtualLab Follow-Up Meetings

```python
from biodsa.agents import VirtualLabAgent

agent = VirtualLabAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

# First meeting: brainstorm
results_1 = agent.go(
    "Design a CRISPR screen for drug resistance genes in melanoma",
    meeting_type="team",
)

# Follow-up meeting: refine based on prior discussion
results_2 = agent.go(
    "Refine the experimental design focusing on controls and validation",
    previous_results=results_1,
    meeting_type="team",
)
```

### Research → Analysis Pipeline

```python
from biodsa.agents import DeepEvidenceAgent, DSWizardAgent

# Step 1: Research
research_agent = DeepEvidenceAgent(...)
research_results = research_agent.go(
    "Find biomarkers for predicting immunotherapy response in NSCLC"
)

# Step 2: Analyze — feed research findings into a data analysis task
analysis_agent = DSWizardAgent(...)
analysis_agent.register_workspace("./patient_data")

analysis_results = analysis_agent.go(
    f"Based on these findings:\n{research_results.final_response}\n\n"
    f"Analyze the patient dataset for these biomarker patterns."
)
```

---

## Error Handling

```python
from biodsa.sandbox.execution import ExecutionResults

try:
    results = agent.go(query)
except Exception as e:
    print(f"Agent execution failed: {e}")
    # Create a stub result for logging
    results = ExecutionResults(
        sandbox=None,
        message_history=[{"role": "user", "content": query}],
        code_execution_results=[],
        final_response=f"ERROR: {e}",
    )

# Check for meaningful output
if not results.final_response or results.final_response.startswith("ERROR"):
    print("Warning: Agent did not produce a useful response")
```

---

## Docker Sandbox

BioDSA agents execute generated code in isolated Docker containers. This is automatic — agents that need code execution will use the sandbox if Docker is available.

### Setup

```bash
cd biodsa_env/python_sandbox
./build_sandbox.sh
# Creates: biodsa-sandbox-py:latest
```

### Fallback

If Docker is not running, agents fall back to local `exec()` execution. This is fine for prototyping but not recommended for production.
