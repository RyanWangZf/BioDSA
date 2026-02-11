<p align="center">
  <a href="https://keiji.ai">
    <img src="./figs/keiji_logo_stacked_horizontal.svg" alt="Keiji AI" width="200">
  </a>
</p>

<p align="center">
  <a href="https://www.nature.com/articles/s41551-025-01587-2"><img src="https://img.shields.io/badge/Nature%20BME-Paper-blue" alt="Nature BME"></a>
  <a href="https://biodsa.github.io"><img src="https://img.shields.io/badge/Website-biodsa.github.io-green" alt="Website"></a>
  <a href="https://keiji.ai"><img src="https://img.shields.io/badge/Platform-keiji.ai-orange" alt="Platform"></a>
  <a href="https://huggingface.co/datasets/zifeng-ai/BioDSA-1K"><img src="https://img.shields.io/badge/🤗-BioDSA--1K-yellow" alt="BioDSA-1K"></a>
  <a href="https://huggingface.co/datasets/zifeng-ai/DeepEvidence"><img src="https://img.shields.io/badge/🤗-DeepEvidence-yellow" alt="DeepEvidence"></a>
</p>

# BioDSA: Vibe-Prototype AI Agents for Biomedicine

**BioDSA** is an open-source framework for rapidly prototyping, optimizing, and benchmarking AI agents for biomedical tasks — from data analysis and literature research to clinical trial matching and drug discovery.

Describe what you want in natural language. Get a working agent in minutes.

---

## Motivation

Building AI agents for biomedicine is hard. A typical agent needs LLM orchestration, access to domain-specific knowledge bases (PubMed, ChEMBL, ClinicalTrials.gov, ...), safe code execution, multi-step reasoning, and structured output — all wired together correctly. Starting from scratch every time is slow and error-prone.

**BioDSA solves this by providing:**

- A **`BaseAgent` foundation** with built-in LLM support (OpenAI, Anthropic, Azure, Google), Docker-sandboxed code execution, and retry handling — so you focus on the agent logic, not the plumbing
- **LangGraph workflows** for composing agent logic as state graphs with conditional edges — supporting ReAct loops, multi-stage pipelines, and multi-agent orchestration
- **17+ biomedical knowledge base integrations** (PubMed, ChEMBL, UniProt, Open Targets, Ensembl, cBioPortal, Reactome, ...) as plug-and-play tools
- **10 benchmarks with 1,900+ tasks** for systematic evaluation
- A **[skill library](biodsa-agent-dev-skills/)** that teaches AI coding assistants (Cursor, Claude Code, Codex, Gemini, OpenClaw) the full architecture — so they can vibe-prototype new agents that follow all codebase conventions

---

## Implemented Agents

8 specialized agents have been built and published on BioDSA, spanning data analysis, deep research, literature review, clinical matching, and more:

| Agent | Type | Description | Paper | Docs |
|-------|------|-------------|-------|------|
| **DSWizard** | Single | Two-phase data science agent (planning → implementation) for biomedical data analysis | [Nature BME](https://www.nature.com/articles/s41551-025-01587-2) | [README](biodsa/agents/dswizard/README.md) \| [Tutorial](tutorials/dswizard_agent.ipynb) |
| **DeepEvidence** | Multi-agent | Hierarchical orchestrator + BFS/DFS sub-agents for deep research across 17+ knowledge bases | [arXiv](https://arxiv.org/abs/2601.11560) | [README](biodsa/agents/deepevidence/README.md) \| [Tutorial](tutorials/deepevidence_agent.ipynb) |
| **TrialMind-SLR** | Multi-stage | Systematic literature review with 4-stage workflow (search, screen, extract, synthesize) | [npj Digit. Med.](https://www.nature.com/articles/s41746-025-01840-7) | [README](biodsa/agents/trialmind_slr/README.md) \| [Tutorial](tutorials/trialmind_slr_agent.ipynb) |
| **InformGen** | Multi-stage | Clinical document generation with iterative write-review-revise workflow | [JAMIA](https://academic.oup.com/jamia/advance-article-abstract/doi/10.1093/jamia/ocaf174/8304363) | [README](biodsa/agents/informgen/README.md) \| [Tutorial](tutorials/informgen_agent.ipynb) |
| **TrialGPT** | Multi-stage | Patient-to-trial matching with retrieval and eligibility scoring | [Nature Comm.](https://www.nature.com/articles/s41467-024-53081-z) | [README](biodsa/agents/trialgpt/README.md) \| [Tutorial](tutorials/trialgpt_agent.ipynb) |
| **AgentMD** | Pipeline | Clinical risk prediction using large-scale toolkit of 2,164+ clinical calculators | [Nature Comm.](https://www.nature.com/articles/s41467-025-64430-x) | [README](biodsa/agents/agentmd/README.md) \| [Tutorial](tutorials/agentmd_agent.ipynb) |
| **GeneAgent** | Single | Self-verification agent for gene set analysis with database-backed claim verification | [Nature Methods](https://www.nature.com/articles/s41592-025-02748-6) | [README](biodsa/agents/geneagent/README.md) \| [Tutorial](tutorials/geneagent.ipynb) |
| **Virtual Lab** | Multi-participant | Multi-agent meeting system for AI-powered scientific research discussions | [Nature](https://www.nature.com/articles/s41586-025-09442-9) | [README](biodsa/agents/virtuallab/README.md) \| [Tutorial](tutorials/virtuallab_agent.ipynb) |

---

## Flow: From Idea to Working Agent

BioDSA supports two paths — **manual** (write code yourself) and **vibe-prototyping** (let an AI coding assistant build it for you).

### Path A: Vibe-Prototype with AI Assistants

```
 ┌──────────────────────────────────────────────────────────────┐
 │  1. INSTALL SKILLS                                          │
 │     ./install-cursor.sh   (or claude-code/codex/gemini)     │
 └──────────────────┬───────────────────────────────────────────┘
                    ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  2. DESCRIBE YOUR AGENT                                     │
 │     "Build an agent that searches PubMed and ClinicalTrials │
 │      to find competing trials for a drug candidate"         │
 │                                                             │
 │     Optionally attach: reference paper, design docs,        │
 │     or point to a benchmark dataset                         │
 └──────────────────┬───────────────────────────────────────────┘
                    ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  3. REVIEW THE DESIGN PROPOSAL                              │
 │     AI proposes: pattern, workflow diagram, tools, state     │
 │     You: confirm, adjust, or ask questions                  │
 └──────────────────┬───────────────────────────────────────────┘
                    ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  4. AI GENERATES THE AGENT                                  │
 │     biodsa/agents/<name>/                                   │
 │       ├── agent.py, state.py, prompt.py, tools.py           │
 │       ├── README.md + DESIGN.md (with Mermaid diagrams)     │
 │     run_<name>.py                                           │
 └──────────────────┬───────────────────────────────────────────┘
                    ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  5. RUN & ITERATE                                           │
 │     python run_<name>.py                                    │
 │     Evaluate on benchmarks, refine prompts/tools/logic      │
 └──────────────────────────────────────────────────────────────┘
```

#### Install Skills

```bash
./install-cursor.sh        # Cursor (project-level)
./install-claude-code.sh   # Claude Code (global)
./install-codex.sh         # Codex CLI (global)
./install-gemini.sh        # Gemini CLI (global)
./install-openclaw.sh      # OpenClaw (global)
```

All installers support `--project`, `--uninstall`, `--dry-run`, and `--verbose` flags.

<details>
<summary>Manual installation & uninstall</summary>

Copy the `.md` files from `biodsa-agent-dev-skills/` to your tool's skills directory:

| Tool | Target Directory |
| ---- | ---------------- |
| Cursor | `<project>/.cursor/skills/biodsa-agent-development/` |
| Claude Code (global) | `~/.claude/skills/biodsa-agent-development/` |
| Claude Code (project) | `<project>/.claude/skills/biodsa-agent-development/` |
| Codex CLI (global) | `~/.codex/skills/biodsa-agent-development/` |
| Gemini CLI (global) | `~/.gemini/skills/biodsa-agent-development/` |
| OpenClaw (global) | `~/.openclaw/skills/biodsa-agent-development/` |

To uninstall, run any installer with `--uninstall`, or delete the `biodsa-agent-development/` folder from your tool's skills directory.

</details>

#### Example Prompts

```
"Create an agent called DrugRepurposing that searches PubMed, ChEMBL,
 and Open Targets for drug repurposing opportunities."

"Here is a paper on clinical evidence synthesis (~/papers/synthesis.pdf).
 Build the agent and evaluate it on benchmarks/TrialPanoramaBench/"

"Build a multi-agent system where an orchestrator delegates gene analysis
 to a BFS sub-agent and pathway analysis to a DFS sub-agent."

"I want to benchmark a literature QA agent on LabBench — build and evaluate it."
```

### Path B: Build Manually

```bash
git clone https://github.com/RyanWangZf/BioDSA.git
cd BioDSA
pip install pipenv && pipenv install && pipenv shell
```

Create a `.env` file with your API keys:

```bash
OPENAI_API_KEY=your_key_here
# Or: AZURE_OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY
```

Then extend `BaseAgent` and define your workflow as a LangGraph state graph:

```python
import os
from biodsa.agents import DSWizardAgent

agent = DSWizardAgent(
    model_name="gpt-5",
    api_type="openai",
    api_key=os.environ["OPENAI_API_KEY"]
)

agent.register_workspace("./biomedical_data/cBioPortal/datasets/acbc_mskcc_2015")
results = agent.go("Perform survival analysis for TP53 mutant vs wild-type patients")
```

See [tutorials/](tutorials/) for Jupyter notebooks covering each agent.

---

## Output Example

Every agent returns an `ExecutionResults` object with a structured trace of the full run:

```python
results = agent.go("Analyze TP53 mutation patterns in breast cancer")

# The agent's final answer
print(results.final_response)

# Full conversation trace (all LLM calls, tool outputs, reasoning steps)
print(results.message_history)

# Any code the agent wrote and executed in the sandbox
print(results.code_execution_results)

# Export a PDF report with figures, code, and narrative
results.to_pdf(output_dir="reports")

# Export structured JSON
results.to_json(output_path="results/analysis.json")

# Download generated artifacts (plots, tables, etc.)
results.download_artifacts(output_dir="artifacts")
```

The PDF report includes the agent's reasoning, executed code blocks, generated figures, and final conclusions — ready to share with collaborators.

### Benchmarking

Evaluate agents on 10 benchmarks covering hypothesis validation, code generation, reasoning, and evidence synthesis:

| Benchmark | Tasks | Type |
|-----------|-------|------|
| BioDSA-1K | 1,029 | Hypothesis validation |
| BioDSBench (Python + R) | 293 | Code generation |
| HLE-Biomedicine / Medicine | 70 | Hard reasoning QA |
| LabBench | 75 | Literature & database QA |
| SuperGPQA | 172 | Expert-level QA |
| TrialPanoramaBench | 50 | Evidence synthesis |
| TRQA-lit | 172 | Translational research QA |

See [benchmarks/README.md](benchmarks/README.md) for dataset details and loading instructions.

---

## Repository Structure

```
BioDSA/
├── biodsa/                          # Core framework
│   ├── agents/                      #   Agent implementations (8 published + base classes)
│   ├── tools/                       #   Low-level API tools (17+ knowledge bases)
│   ├── tool_wrappers/               #   LangChain tool wrappers
│   ├── sandbox/                     #   Docker sandbox & ExecutionResults
│   └── memory/                      #   Memory graph system
├── benchmarks/                      # 10 evaluation benchmarks (1,900+ tasks)
├── tutorials/                       # Jupyter notebook tutorials for each agent
├── scripts/                         # Example run scripts
├── biodsa-agent-dev-skills/         # Skill library for AI coding assistants
├── install-*.sh                     # One-command installers (Cursor, Claude, Codex, Gemini, OpenClaw)
├── biodsa_env/                      # Docker sandbox build files
├── tests/                           # Tool and integration tests
└── biomedical_data/                 # Example datasets (cBioPortal, Open Targets)
```

---

## Reference

If you use BioDSA in your research, please cite:

```bibtex
@article{wang2026reliable,
  title={Making large language models reliable data science programming copilots for biomedical research},
  author={Wang, Zifeng and Danek, Benjamin and Yang, Ziwei and Chen, Zheng and Sun, Jimeng},
  journal={Nature Biomedical Engineering},
  year={2026},
  doi={10.1038/s41551-025-01587-2}
}

@article{wang2026deepevidence,
  title={DeepEvidence: Empowering Biomedical Discovery with Deep Knowledge Graph Research},
  author={Wang, Zifeng and Chen, Zheng and Yang, Ziwei and Wang, Xuan and Jin, Qiao and Peng, Yifan and Lu, Zhiyong and Sun, Jimeng},
  journal={arXiv preprint arXiv:2601.11560},
  year={2026}
}
```

**Documentation**: [tutorials/](tutorials/) | [biodsa-agent-dev-skills/](biodsa-agent-dev-skills/) | [benchmarks/](benchmarks/) | [biodsa_env/](biodsa_env/)

**Links**: [biodsa.github.io](https://biodsa.github.io) | [Keiji AI](https://keiji.ai) | [BioDSA-1K](https://huggingface.co/datasets/zifeng-ai/BioDSA-1K) | [DeepEvidence](https://huggingface.co/datasets/zifeng-ai/DeepEvidence) | [TrialReviewBench](https://huggingface.co/datasets/zifeng-ai/TrialReviewBench)

**License**: [LICENSE](LICENSE)
