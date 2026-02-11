# 03 — Output and Deliverables

This guide covers how to handle agent output: `ExecutionResults`, PDF reports, JSON export, artifact download, and specialized result types.

---

## ExecutionResults

Every agent's `go()` method returns an `ExecutionResults` instance (or a subclass).

> **Source**: `biodsa/sandbox/execution.py`

### Core Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `final_response` | `str` | The agent's final answer / summary |
| `message_history` | `List[Dict[str, str]]` | Full conversation trace (all LLM calls, tool results) |
| `code_execution_results` | `List[Dict[str, str]]` | Code blocks executed and their stdout/stderr |
| `sandbox` | `ExecutionSandboxWrapper` | Reference to the Docker sandbox (may be `None`) |

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `to_json(output_path=None)` | `dict` | Serialize to JSON; saves to file if path provided |
| `to_pdf(output_dir, filename=None, include_artifacts=True)` | `str` | Generate a PDF report; returns path to PDF |
| `download_artifacts(output_dir)` | `List[str]` | Download files generated in sandbox; returns filenames |
| `__str__()` | `str` | Pretty-printed summary |

---

## Saving JSON

```python
results = agent.go("Analyze TP53 mutations in breast cancer")

# Get as dict
data = results.to_json()

# Save to file
results.to_json(output_path="output/results.json")
```

The JSON contains:
```json
{
    "final_response": "...",
    "message_history": [...],
    "code_execution_results": [...]
}
```

---

## Generating PDF Reports

```python
# Basic PDF
pdf_path = results.to_pdf(output_dir="output")

# Custom filename
pdf_path = results.to_pdf(output_dir="output", filename="survival_analysis.pdf")

# Without artifacts (faster, no sandbox download)
pdf_path = results.to_pdf(output_dir="output", include_artifacts=False)
```

The PDF includes:
- Header with BioDSA logo and title
- **User Query** section
- **Agent Exploration Process** — truncated code blocks showing reasoning steps
- **Results and Analysis** — final response with embedded figures
- **Supplementary Materials** — full code and execution logs

**Note**: PDF generation requires the `reportlab` package.

---

## Downloading Artifacts

Agents that execute code in the sandbox may generate files (plots, CSVs, etc.). Download them:

```python
filenames = results.download_artifacts(output_dir="output/artifacts")
print(f"Downloaded: {filenames}")
# e.g., ["survival_plot.png", "summary_table.csv"]
```

**Requires** the sandbox to be available (`results.sandbox is not None`).

---

## Specialized Result Types

Some agents return subclasses of `ExecutionResults` with additional fields.

### DeepEvidenceExecutionResults

Returned by `DeepEvidenceAgent`.

Additional capabilities:
```python
# Export interactive evidence graph as HTML
results.export_evidence_graph_html("evidence_graph.html")
```

### SLRMetaExecutionResults

Returned by `SLRMetaAgent`.

Additional fields:
| Field | Type | Description |
|-------|------|-------------|
| `identified_pubmed` | `list` | PubMed articles found |
| `identified_ctgov` | `list` | ClinicalTrials.gov entries found |
| `included_studies` | `list` | Studies included in final synthesis |
| `final_report` | `str` | Full systematic review report |

### InformGenExecutionResults

Returned by `InformGenAgent`.

Additional fields:
| Field | Type | Description |
|-------|------|-------------|
| `completed_sections` | `list` | Document sections completed |
| `final_document` | `str` | Full generated document |
| `total_input_tokens` | `int` | Total input tokens used |
| `total_output_tokens` | `int` | Total output tokens used |

### TrialMindSLRExecutionResults

Returned by `TrialMindSLRAgent`.

Similar to `SLRMetaExecutionResults` with SLR-specific metadata.

---

## Complete Deliverable Script Template

When a user asks to run an agent:
1. **Generate** this script (fill in the agent and task)
2. **Save** it to a file at the repo root
3. **Execute** it via the terminal
4. **Wait** for it to complete
5. **Report** the results back to the user

```python
"""
Run <AgentName> on: <brief task description>

Usage:
    python run_task.py
"""
import sys, os

REPO_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))

from biodsa.agents import <AgentClass>

# ── Initialize ──────────────────────────────────────────────
agent = <AgentClass>(
    model_name=os.environ.get("MODEL_NAME", "gpt-5"),
    api_type=os.environ.get("API_TYPE", "azure"),
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

# ── (Optional) Register data ────────────────────────────────
# agent.register_workspace("/path/to/data")

# ── Execute ─────────────────────────────────────────────────
task = """<user's task description>"""

results = agent.go(task)

# ── Deliverables ────────────────────────────────────────────
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Print final answer
print("=" * 60)
print("RESULT:")
print("=" * 60)
print(results.final_response)

# Save JSON
results.to_json(output_path=os.path.join(output_dir, "results.json"))
print(f"\nJSON saved to {output_dir}/results.json")

# Generate PDF report
try:
    pdf_path = results.to_pdf(output_dir=output_dir)
    print(f"PDF report saved to {pdf_path}")
except Exception as e:
    print(f"PDF generation skipped: {e}")

# Download artifacts (plots, tables, etc.)
try:
    artifacts = results.download_artifacts(output_dir=os.path.join(output_dir, "artifacts"))
    if artifacts:
        print(f"Artifacts downloaded: {artifacts}")
except Exception as e:
    print(f"Artifact download skipped: {e}")

# ── Cleanup ─────────────────────────────────────────────────
# agent.clear_workspace()
```

### Script Conventions

1. **Always save JSON** — it's the most reliable output format
2. **Always try PDF** — wrap in try/except since it requires `reportlab`
3. **Always try artifacts** — wrap in try/except since it requires Docker sandbox
4. **Print `final_response`** — so the user sees immediate output in the terminal
5. **Use environment variables** — never hardcode API keys
6. **Create output directory** — ensure it exists before saving

---

## End-to-End Execution Checklist

After running the script, verify and report:

| Check | How |
|-------|-----|
| Script ran without errors | Terminal exit code is 0 |
| `final_response` is non-empty | Printed to stdout |
| JSON was saved | File exists at `output/results.json` |
| PDF was generated (if applicable) | File exists in `output/` |
| Artifacts downloaded (if applicable) | Files exist in `output/artifacts/` |

**If the script fails:**
1. Read the error traceback from the terminal
2. Common issues: missing `.env` keys, wrong `api_type`, Docker not running, missing dependencies
3. Fix the script and re-run — do NOT just report the error and stop
4. If you cannot fix the issue (e.g., user needs to provide API keys), explain exactly what is needed

**After success:**
- Summarize the `final_response` for the user
- List the saved deliverables (JSON path, PDF path, artifact paths)
- If the user might want to re-run with different parameters, note what to change
