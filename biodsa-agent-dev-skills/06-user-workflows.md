# 06 — User Workflows

This guide covers the two primary workflows users follow when building agents with BioDSA and an AI coding assistant (Cursor, Claude Code).

---

## Workflow 1: Build an Agent from Reference Materials

### When to Use

The user provides a folder or set of documents — a research paper (PDF), design notes, algorithm descriptions, or any reference materials — and asks you to build an agent that implements the described approach.

### Input Signals

- "Here is the paper, build an agent that does what it describes"
- "I have a folder with docs about a new agent idea — implement it"
- User attaches or points to PDFs, markdown files, or a directory of reference materials
- User describes an agent concept with a link to a paper or existing tool

### Step-by-Step Procedure

#### 1. Read and Understand the Reference Materials

- Read every document the user provides (PDFs, markdown, text files, etc.)
- Identify the **core algorithm / workflow** the paper describes
- Extract:
  - **Input format**: What does the agent take as input?
  - **Output format**: What should the agent produce?
  - **Processing stages**: What are the logical steps?
  - **External resources**: Does it need APIs, databases, knowledge bases?
  - **Evaluation criteria**: How is the approach judged to be correct?

#### 2. Map to BioDSA Patterns

Based on the reference materials, decide which BioDSA pattern fits best:

| Reference Describes… | BioDSA Pattern | Guide |
|----------------------|----------------|-------|
| A single-step tool-calling loop | ReAct agent (Pattern A) | [02-single-agent.md](./02-single-agent.md) |
| A multi-step pipeline (e.g., search → filter → analyze) | Multi-stage pipeline (Pattern C) | [02-single-agent.md](./02-single-agent.md) |
| An orchestrator delegating to specialized sub-agents | Orchestrator + sub-workflows | [03-multi-agent.md](./03-multi-agent.md) |
| A discussion/meeting among multiple participants | Multi-participant meeting | [03-multi-agent.md](./03-multi-agent.md) |

#### 3. Identify Reusable Tools

Check existing tools in `biodsa/tools/` and `biodsa/tool_wrappers/` before building new ones. Common reusable tools:

| Need | Existing Tool |
|------|--------------|
| PubMed search | `biodsa/tools/pubmed/` |
| Gene info lookup | `biodsa/tools/ncbi_gene/`, `biodsa/tools/ensembl/` |
| Drug/compound data | `biodsa/tools/chembl/`, `biodsa/tools/pubchem/` |
| Disease info | `biodsa/tools/disease/` |
| Clinical trials | `biodsa/tools/clinical_trials/` |
| Protein info | `biodsa/tools/uniprot/`, `biodsa/tools/protein_atlas/` |
| Pathway analysis | `biodsa/tools/reactome/` |
| Code execution (sandbox) | `biodsa/tool_wrappers/code_exec_tool.py` |
| Web search | `biodsa/tool_wrappers/web_search/` |

See [04-tools-and-wrappers.md](./04-tools-and-wrappers.md) for the full catalog and how to create new tools.

#### 4. Create the Agent

Follow the standard checklist from [SKILL.md](./SKILL.md):

1. Create `biodsa/agents/<agent_name>/` with all required files
2. Translate the paper's algorithm into a LangGraph `StateGraph`
3. Map the paper's "stages" to graph nodes
4. Map the paper's "decision points" to conditional edges
5. Write prompts that encode the paper's domain knowledge
6. Wire up tools (reuse existing + create agent-specific ones)
7. Implement `go()` returning `ExecutionResults`

#### 5. Create a Run Script with a Realistic Example

The run script (`run_<agent_name>.py`) should use an example that mirrors the paper's use cases:

```python
"""
<AgentName> Example Script

Based on: <Paper title and citation>
Reference: <Path to the reference materials folder>
"""
import sys, os
current_dir = os.getcwd()
REPO_BASE_DIR = os.path.dirname(os.path.abspath(current_dir))
sys.path.append(REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))

from biodsa.agents.<agent_name> import <AgentClass>

agent = <AgentClass>(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

# Use an example from the paper or reference materials
example_input = """<realistic input based on the paper's examples>"""

results = agent.go(example_input)
print(results.final_response)
```

#### 6. Sanity Check

Follow the procedure in [05-deliverables-and-testing.md](./05-deliverables-and-testing.md).

### Example: User Provides a Paper on Drug Repurposing

```
User: "Here is a paper on computational drug repurposing using knowledge graphs.
       The paper is at ~/papers/drug_repurposing_2025.pdf. Build this as an agent."
```

What you do:
1. Read the PDF — extract the algorithm (e.g., disease → target genes → drug candidates → evidence scoring)
2. Map to BioDSA: Multi-stage pipeline (Pattern C in 02-single-agent.md)
3. Reuse tools: `biodsa/tools/disease/`, `biodsa/tools/ncbi_gene/`, `biodsa/tools/chembl/`, `biodsa/tools/pubmed/`
4. Create `biodsa/agents/drug_repurposing/` with a 4-node StateGraph
5. Write `run_drug_repurposing.py` using a disease from the paper as example input
6. Run sanity check

---

## Workflow 2: Build an Agent for Benchmark Evaluation

### When to Use

The user provides one or more benchmark datasets (or points to `benchmarks/`) and asks you to build an agent that can be evaluated on them.

### Input Signals

- "Build an agent that can handle BioDSA-1K tasks"
- "I want to evaluate an agent on the HLE-Medicine benchmark"
- "Create an agent and test it on `benchmarks/LabBench/`"
- User points to CSV, JSONL, or Parquet files with task data

### Available Benchmarks

The `benchmarks/` directory contains:

| Benchmark | Location | Format | # Tasks | Task Type |
|-----------|----------|--------|---------|-----------|
| BioDSA-1K | `benchmarks/BioDSA-1K/dataset/biodsa_1k_hypothesis.parquet` | Parquet | 1,029 | Hypothesis validation |
| BioDSBench-Python | `benchmarks/BioDSBench-Python/dataset/python_tasks_with_class.jsonl` | JSONL | 128 | Python code generation |
| BioDSBench-R | `benchmarks/BioDSBench-R/dataset/R_tasks_with_class.jsonl` | JSONL | 165 | R code generation |
| HLE-Biomedicine | `benchmarks/HLE-biomedicine/hle_biomedicine_40.csv` | CSV | 40 | Hard reasoning QA |
| HLE-Medicine | `benchmarks/HLE-medicine/hle_medicine_30.csv` | CSV | 30 | Hard reasoning QA |
| LabBench (LitQA) | `benchmarks/LabBench/LitQA2_25.csv` | CSV | 25 | Literature QA |
| LabBench (DBQA) | `benchmarks/LabBench/DBQA_50.csv` | CSV | 50 | Database QA |
| SuperGPQA | `benchmarks/SuperGPQA/SuperGPQA-hard-medicine-172.csv` | CSV | 172 | Expert-level QA |
| TrialPanoramaBench | `benchmarks/TrialPanoramaBench/evidence_synthesis_50.csv` | CSV | 50 | Evidence synthesis |
| TRQA-lit | `benchmarks/TRQA-lit/TRQA-lit-choice-172.csv` | CSV | 172 | Literature QA |

See `benchmarks/README.md` for full details.

### Step-by-Step Procedure

#### 1. Understand the Benchmark

Read the benchmark data to understand:
- **Input format**: What question/task is given to the agent?
- **Expected output**: What does a correct answer look like?
- **Evaluation metric**: Exact match? Code pass rate? F1? Human judgment?

Loading examples:

```python
import pandas as pd
import json

# CSV benchmarks
df = pd.read_csv("benchmarks/HLE-medicine/hle_medicine_30.csv")
# Columns: id, question, answer, answer_type, rationale, raw_subject

# Parquet benchmarks
df = pd.read_parquet("benchmarks/BioDSA-1K/dataset/biodsa_1k_hypothesis.parquet")

# JSONL benchmarks
tasks = []
with open("benchmarks/BioDSBench-Python/dataset/python_tasks_with_class.jsonl") as f:
    for line in f:
        tasks.append(json.loads(line))
# Fields: study_ids, question_ids, queries, reference_answer, test_cases, tables, ...
```

#### 2. Design the Agent for the Task Type

| Benchmark Type | Recommended Agent Pattern | Key Tools |
|---------------|--------------------------|-----------|
| **QA / Reasoning** (HLE, SuperGPQA, TRQA-lit) | ReAct agent with knowledge base tools | PubMed search, web search, code execution for calculations |
| **Code Generation** (BioDSBench) | Coder agent or ReAct with code execution | `CodeExecutionTool` (sandbox), dataset loading |
| **Hypothesis Validation** (BioDSA-1K) | Multi-stage pipeline (plan → code → validate) | `CodeExecutionTool`, statistical analysis tools |
| **Evidence Synthesis** (TrialPanoramaBench) | Multi-stage or multi-agent (search → extract → synthesize) | PubMed, clinical trials, literature tools |
| **Literature QA** (LabBench) | ReAct with literature search tools | PubMed, PubTator, web search |

#### 3. Build the Agent

Follow the standard agent creation flow (see guides 01–05). Key considerations for benchmark agents:

- **Input parsing**: Your agent's `go()` method should accept the benchmark's question/task format directly
- **Output formatting**: The agent's `final_response` should match what the benchmark expects (e.g., a letter choice for multiple-choice, executable code for code generation)
- **Determinism**: Consider setting `temperature=0` for reproducible results

#### 4. Write the Evaluation Script

Create an evaluation script at the repo root (e.g., `eval_<agent_name>.py` or `eval_<benchmark_name>.py`):

```python
"""
Evaluate <AgentName> on <BenchmarkName>

Usage:
    python eval_<agent_name>.py --benchmark <benchmark_path> --output <output_dir>
"""
import sys, os, json, argparse
import pandas as pd

current_dir = os.getcwd()
REPO_BASE_DIR = os.path.dirname(os.path.abspath(current_dir))
sys.path.append(REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))

from biodsa.agents.<agent_name> import <AgentClass>


def load_benchmark(path: str):
    """Load benchmark dataset (CSV, JSONL, or Parquet)."""
    if path.endswith(".csv"):
        return pd.read_csv(path).to_dict("records")
    elif path.endswith(".parquet"):
        return pd.read_parquet(path).to_dict("records")
    elif path.endswith(".jsonl"):
        with open(path) as f:
            return [json.loads(line) for line in f]
    else:
        raise ValueError(f"Unsupported format: {path}")


def evaluate(agent, tasks: list, output_dir: str):
    """Run agent on all tasks and collect results."""
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for i, task in enumerate(tasks):
        task_id = task.get("id", task.get("data_id", i))
        question = task.get("question", task.get("queries", ""))
        ground_truth = task.get("answer", task.get("reference_answer", ""))

        print(f"[{i+1}/{len(tasks)}] Task {task_id}")

        try:
            agent_result = agent.go(question)
            prediction = agent_result.final_response
        except Exception as e:
            prediction = f"ERROR: {e}"

        results.append({
            "task_id": task_id,
            "question": question,
            "ground_truth": ground_truth,
            "prediction": prediction,
        })

        # Save incremental results
        with open(os.path.join(output_dir, "results.jsonl"), "a") as f:
            f.write(json.dumps(results[-1]) + "\n")

    return results


def compute_metrics(results: list):
    """Compute basic evaluation metrics."""
    total = len(results)
    correct = sum(
        1 for r in results
        if r["ground_truth"].strip().lower() == r["prediction"].strip().lower()
    )
    accuracy = correct / total if total > 0 else 0
    errors = sum(1 for r in results if r["prediction"].startswith("ERROR"))

    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "errors": errors,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", required=True, help="Path to benchmark file")
    parser.add_argument("--output", default="eval_results", help="Output directory")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of tasks")
    args = parser.parse_args()

    agent = <AgentClass>(
        model_name="gpt-5",
        api_type="azure",
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    )

    tasks = load_benchmark(args.benchmark)
    if args.limit:
        tasks = tasks[:args.limit]

    results = evaluate(agent, tasks, args.output)
    metrics = compute_metrics(results)

    print("\n=== Evaluation Results ===")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    # Save summary
    with open(os.path.join(args.output, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
```

#### 5. Run a Quick Smoke Test First

Before running the full benchmark, test on a small subset:

```bash
python eval_<agent_name>.py --benchmark benchmarks/HLE-medicine/hle_medicine_30.csv --limit 3 --output eval_results/smoke_test
```

Verify:
- Agent handles the benchmark's question format
- Output format matches expected answers
- No crashes on edge cases

#### 6. Run Full Evaluation

```bash
python eval_<agent_name>.py --benchmark benchmarks/HLE-medicine/hle_medicine_30.csv --output eval_results/hle_medicine
```

### Benchmark-Specific Tips

#### For QA Benchmarks (HLE, SuperGPQA, TRQA-lit, LabBench)

- Questions are typically free-text or multiple-choice
- Ground truth answers may be short (a letter, a number, or a phrase)
- Instruct the agent to give a **concise final answer** — include this in the system prompt:
  ```
  After your analysis, provide your final answer on a single line starting with "ANSWER: "
  ```
- Parse the agent's `final_response` to extract the answer for comparison

#### For Code Generation Benchmarks (BioDSBench)

- Each task includes `queries` (the question), `tables` (data file paths), `reference_answer` (gold code), and `test_cases` (assertions)
- The agent should generate Python/R code and execute it in the sandbox
- Evaluation: run the generated code + test cases, check if assertions pass
- Upload the task's data tables to the sandbox via `agent.register_workspace()`

#### For Hypothesis Validation (BioDSA-1K)

- Tasks include hypothesis statements, supporting tables, and analysis plans
- The agent should write and execute statistical analysis code
- Compare the agent's conclusion (support / reject hypothesis) against ground truth

#### For Evidence Synthesis (TrialPanoramaBench)

- Tasks require searching literature and synthesizing evidence
- Multi-agent or multi-stage pipelines work best
- Evaluation may require human judgment or semantic similarity

---

## Combining Workflows

Often both workflows apply together: a user provides a paper (Workflow 1) **and** a benchmark (Workflow 2). In that case:

1. First follow Workflow 1 to understand the algorithm and build the agent
2. Then follow Workflow 2 to create an evaluation script
3. Use benchmark results to iteratively improve the agent's prompts, tools, and logic

This iterate-and-evaluate loop is the core development cycle:

```
Reference Materials ──→ Build Agent ──→ Evaluate on Benchmark
        ▲                                      │
        └──── Improve prompts/tools/logic ◄────┘
```
