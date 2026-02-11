# BioDSA Agent Development Skills

**Vibe-prototype new biomedical AI agents in minutes, not days.**

A skill library that teaches AI coding agents (Cursor, Claude Code, Codex CLI, Gemini CLI, OpenClaw) how to build new agents on the [BioDSA](https://github.com/RyanWangZf/BioDSA) framework. Install these skills, describe the agent you want in natural language, and your AI assistant produces a complete, working prototype that follows the codebase conventions and passes a sanity check.

## Why This Exists

BioDSA is a modular framework for building biomedical data science agents — but it has non-trivial architecture: a `BaseAgent` base class, LangGraph state graphs, a 3-layer tool system, Docker sandbox integration, and specific folder/export conventions. An AI coding agent working without context will miss these patterns and produce code that doesn't integrate.

This skill library gives AI agents **expert knowledge of the entire architecture** so they can:
- Correctly subclass `BaseAgent` with the right constructor, LLM setup, and sandbox lifecycle
- Build proper LangGraph workflows (ReAct loops, multi-stage pipelines, orchestrator systems)
- Reuse the 17+ existing knowledge base tools instead of reinventing them
- Follow the exact folder structure, `__init__.py` exports, and run script conventions
- Produce `ExecutionResults` with PDF report generation out of the box

## Implemented Agents in BioDSA

These are the agents already built on the framework — the same patterns the skills teach your AI assistant to follow:

| Agent | Type | Description | Paper | Docs |
|-------|------|-------------|-------|------|
| **DSWizard** | Single | Two-phase data science agent (planning then implementation) for biomedical data analysis | [Nature BME](https://www.nature.com/articles/s41551-025-01587-2) | [README](../biodsa/agents/dswizard/README.md) |
| **DeepEvidence** | Multi-agent | Hierarchical orchestrator + BFS/DFS sub-agents for deep research across 17+ knowledge bases | [arXiv](https://arxiv.org/abs/2601.11560) | [README](../biodsa/agents/deepevidence/README.md) |
| **TrialMind-SLR** | Multi-stage | Systematic literature review with 4-stage workflow (search, screen, extract, synthesize) | [npj Digit. Med.](https://www.nature.com/articles/s41746-025-01840-7) | [README](../biodsa/agents/trialmind_slr/README.md) |
| **InformGen** | Multi-stage | Clinical document generation with iterative write-review-revise workflow | [JAMIA](https://academic.oup.com/jamia/advance-article-abstract/doi/10.1093/jamia/ocaf174/8304363) | [README](../biodsa/agents/informgen/README.md) |
| **TrialGPT** | Multi-stage | Patient-to-trial matching with retrieval and eligibility scoring | [Nature Comm.](https://www.nature.com/articles/s41467-024-53081-z) | [README](../biodsa/agents/trialgpt/README.md) |
| **AgentMD** | Pipeline | Clinical risk prediction using large-scale toolkit of 2,164+ clinical calculators | [Nature Comm.](https://www.nature.com/articles/s41467-025-64430-x) | [README](../biodsa/agents/agentmd/README.md) |
| **GeneAgent** | Single | Self-verification agent for gene set analysis with database-backed claim verification | [Nature Methods](https://www.nature.com/articles/s41592-025-02748-6) | [README](../biodsa/agents/geneagent/README.md) |
| **Virtual Lab** | Multi-participant | Multi-agent meeting system for AI-powered scientific research discussions | [Nature](https://www.nature.com/articles/s41586-025-09442-9) | [README](../biodsa/agents/virtuallab/README.md) |

## Installation

All install scripts are at the **repo root**. Run from the BioDSA directory:

### For Cursor

```bash
./install-cursor.sh                            # Install to current project
./install-cursor.sh --project /path/to/project # Install to a different project
```

### For Claude Code

```bash
./install-claude-code.sh                            # Install globally
./install-claude-code.sh --project /path/to/project # Install to specific project
```

### For Codex CLI

```bash
./install-codex.sh                            # Install globally
./install-codex.sh --project /path/to/project # Install to specific project
```

### For Gemini CLI

```bash
./install-gemini.sh                            # Install globally
./install-gemini.sh --project /path/to/project # Install to specific project
```

### For OpenClaw

```bash
./install-openclaw.sh                            # Install globally
./install-openclaw.sh --project /path/to/workspace # Install to workspace
```

All installers support `--dry-run`, `--uninstall`, and `--verbose` flags.

### Manual Installation

Copy the skill files to the appropriate directory for your tool:

| Tool | Target Directory |
| ---- | ---------------- |
| Cursor | `<project>/.cursor/skills/biodsa-agent-development/` |
| Claude Code (global) | `~/.claude/skills/biodsa-agent-development/` |
| Claude Code (project) | `<project>/.claude/skills/biodsa-agent-development/` |
| Codex CLI (global) | `~/.codex/skills/biodsa-agent-development/` |
| Codex CLI (project) | `<project>/.codex/skills/biodsa-agent-development/` |
| Gemini CLI (global) | `~/.gemini/skills/biodsa-agent-development/` |
| Gemini CLI (project) | `<project>/.gemini/skills/biodsa-agent-development/` |
| OpenClaw (global) | `~/.openclaw/skills/biodsa-agent-development/` |
| OpenClaw (project) | `<project>/skills/biodsa-agent-development/` |

Files to copy from `biodsa-agent-dev-skills/`:
```
SKILL.md                       # Main entry point (agent reads this first)
01-base-agent.md               # BaseAgent class reference
02-single-agent.md             # Single agent patterns (ReAct, pipeline, multi-stage)
03-multi-agent.md              # Multi-agent patterns (orchestrator, meetings)
04-tools-and-wrappers.md       # Tools architecture (3 layers)
05-deliverables-and-testing.md # Folder structure, run scripts, sanity checks
06-user-workflows.md           # Development workflows (reference materials, benchmarks)
```

## Development Workflows

The skills support two primary workflows:

### Workflow 1: Build from Reference Materials
Provide a folder of documents (paper PDFs, design notes, algorithms) and the AI agent will:
1. Read and understand the reference materials
2. Map the described approach to a BioDSA agent pattern
3. Reuse existing tools where possible
4. Produce a complete, working agent

```
"Here is a paper on drug repurposing using knowledge graphs (~/papers/drug_repurposing.pdf).
 Build an agent that implements this approach."

"I have design docs in ./docs/trial_screener/ — build a TrialScreener agent from them."
```

### Workflow 2: Build for Benchmark Evaluation
Point to one or more benchmark datasets from `benchmarks/` and the AI agent will:
1. Analyze the benchmark format and task type
2. Build an agent suited to the task
3. Create an evaluation script that runs the agent on the benchmark
4. Report metrics (accuracy, pass rate, etc.)

```
"Build an agent that can answer the HLE-Medicine questions in benchmarks/HLE-medicine/"

"Create an agent and evaluate it on BioDSA-1K hypothesis validation tasks"

"I want to benchmark a literature QA agent on LabBench — build and evaluate it"
```

### Combined Workflow
Both workflows can be combined — provide reference materials **and** a benchmark:
```
"Here is a paper on clinical evidence synthesis. Build the agent and evaluate it
 on benchmarks/TrialPanoramaBench/evidence_synthesis_50.csv"
```

## Example Prompts

Once installed, try asking your AI agent:

```
"Create a new agent called DrugRepurposing that searches PubMed, ChEMBL, and Open Targets
 to find drug repurposing opportunities for a given disease."

"Build a multi-agent system where an orchestrator agent delegates gene analysis
 to a BFS sub-agent and pathway analysis to a DFS sub-agent."

"Help me implement a TrialScreener agent that takes a patient note and searches
 ClinicalTrials.gov for matching trials, then ranks them by eligibility."

"I need an agent that takes a gene set, runs enrichment analysis using the
 existing gene_set tools, and produces a summary report."
```

The AI agent will read the skill files, understand the BioDSA architecture, and produce:
1. An agent folder under `biodsa/agents/<name>/` with all required files
2. A run script at `run_<name>.py`
3. Code that follows the established patterns and passes a sanity check

## Skill Contents

| Guide | File | Topics |
| ----- | ---- | ------ |
| Base Agent | `01-base-agent.md` | `BaseAgent` constructor, LLM factory, sandbox lifecycle, `run_with_retry`, subclass contract |
| Single Agent | `02-single-agent.md` | Pattern A: ReAct loop, Pattern B: manual pipeline, Pattern C: LangGraph multi-stage pipeline |
| Multi-Agent | `03-multi-agent.md` | Orchestrator + sub-workflows (DeepEvidence pattern), multi-participant meetings (VirtualLab pattern) |
| Tools | `04-tools-and-wrappers.md` | 3-layer architecture: `biodsa/tools/` -> `biodsa/tool_wrappers/` -> `biodsa/agents/<name>/tools.py`; reusable tool catalog |
| Deliverables | `05-deliverables-and-testing.md` | Folder structure template, `__init__.py` exports, run script template, `ExecutionResults`, PDF generation, sanity check procedure |
| User Workflows | `06-user-workflows.md` | Two development workflows: building from reference materials (papers/docs), building for benchmark evaluation |

## How It Works

AI coding agents (Cursor, Claude Code, Codex CLI, Gemini CLI, OpenClaw) can be configured to read "skill" files — markdown documents that give them domain-specific expertise. When you ask the agent to do something related to BioDSA agent development, it reads the skill files and follows the documented patterns.

```
You: "Create a PubMed search agent"
         |
         v
    AI reads SKILL.md
         |
         v
    AI reads relevant guides
    (01-base-agent.md, 02-single-agent.md, 04-tools-and-wrappers.md, ...)
         |
         v
    AI generates:
    ├── biodsa/agents/pubmed_search/__init__.py
    ├── biodsa/agents/pubmed_search/agent.py
    ├── biodsa/agents/pubmed_search/state.py
    ├── biodsa/agents/pubmed_search/prompt.py
    ├── biodsa/agents/pubmed_search/tools.py
    ├── biodsa/agents/pubmed_search/README.md
    └── run_pubmed_search.py
```

## Uninstall

```bash
# Cursor
./install-cursor.sh --uninstall

# Claude Code
./install-claude-code.sh --uninstall
./install-claude-code.sh --project /path/to/project --uninstall

# Codex CLI
./install-codex.sh --uninstall

# Gemini CLI
./install-gemini.sh --uninstall

# OpenClaw
./install-openclaw.sh --uninstall
```

Or simply delete the `biodsa-agent-development/` directory from your tool's skills folder.

## Related

- [BioDSA](https://github.com/RyanWangZf/BioDSA) — The framework these skills teach agents to use ([Nature BME Paper](https://www.nature.com/articles/s41551-025-01587-2))
- [biodsa.github.io](https://biodsa.github.io) — Project website
- [Keiji AI](https://keiji.ai) — Platform for biomedical AI agents
- [BioDSA-1K](https://huggingface.co/datasets/zifeng-ai/BioDSA-1K) | [TrialReviewBench](https://huggingface.co/datasets/zifeng-ai/TrialReviewBench) | [DeepEvidence](https://huggingface.co/datasets/zifeng-ai/DeepEvidence) — Benchmark datasets
