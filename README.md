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

# BioDSA: Biomedical Data Science Agents

**BioDSA** is a modular, open-source framework for building, reproducing, and evaluating biomedical data science agents. It is designed for AI agent research, prioritizing clean abstractions, rapid prototyping, and systematic benchmarking to accelerate R&D of AI agents for biomedicine.

## Key Features

- **Modular Base Agent** — Extend `BaseAgent` with built-in LLM support (OpenAI, Anthropic, Azure, Google), sandboxed execution, and retry handling
- **LangGraph Workflows** — Define agent logic as composable state graphs with conditional edges for complex multi-step reasoning
- **Plug-and-Play Tools** — Ready-to-use wrappers for PubMed, ClinicalTrials.gov, cBioPortal, gene databases, and 15+ more
- **Sandboxed Execution** — Execute generated code safely in Docker containers with resource monitoring and artifact collection
- **Comprehensive Benchmarks** — Evaluate agents on BioDSA-1K, BioDSBench, HLE-Medicine, LabBench, SuperGPQA, and more
- **AI-Assisted Development** — [Skill library](biodsa-agent-dev-skills/) that teaches AI coding agents (Cursor, Claude Code, Codex, Gemini, OpenClaw) to build new agents on this framework

## Specialized Agents

| Agent | Type | Description | Paper | Docs |
|-------|------|-------------|-------|------|
| **DSWizard** | Single | Two-phase data science agent (planning then implementation) for biomedical data analysis | [Nature BME](https://www.nature.com/articles/s41551-025-01587-2) | [README](biodsa/agents/dswizard/README.md) \| [Tutorial](tutorials/dswizard_agent.ipynb) |
| **DeepEvidence** | Multi-agent | Hierarchical orchestrator + BFS/DFS sub-agents for deep research across 17+ knowledge bases | [arXiv](https://arxiv.org/abs/2601.11560) | [README](biodsa/agents/deepevidence/README.md) \| [Tutorial](tutorials/deepevidence_agent.ipynb) |
| **TrialMind-SLR** | Multi-stage | Systematic literature review with 4-stage workflow (search, screen, extract, synthesize) | [npj Digit. Med.](https://www.nature.com/articles/s41746-025-01840-7) | [README](biodsa/agents/trialmind_slr/README.md) \| [Tutorial](tutorials/trialmind_slr_agent.ipynb) |
| **InformGen** | Multi-stage | Clinical document generation with iterative write-review-revise workflow | [JAMIA](https://academic.oup.com/jamia/advance-article-abstract/doi/10.1093/jamia/ocaf174/8304363) | [README](biodsa/agents/informgen/README.md) \| [Tutorial](tutorials/informgen_agent.ipynb) |
| **TrialGPT** | Multi-stage | Patient-to-trial matching with retrieval and eligibility scoring | [Nature Comm.](https://www.nature.com/articles/s41467-024-53081-z) | [README](biodsa/agents/trialgpt/README.md) \| [Tutorial](tutorials/trialgpt_agent.ipynb) |
| **AgentMD** | Pipeline | Clinical risk prediction using large-scale toolkit of 2,164+ clinical calculators | [Nature Comm.](https://www.nature.com/articles/s41467-025-64430-x) | [README](biodsa/agents/agentmd/README.md) \| [Tutorial](tutorials/agentmd_agent.ipynb) |
| **GeneAgent** | Single | Self-verification agent for gene set analysis with database-backed claim verification | [Nature Methods](https://www.nature.com/articles/s41592-025-02748-6) | [README](biodsa/agents/geneagent/README.md) \| [Tutorial](tutorials/geneagent.ipynb) |
| **Virtual Lab** | Multi-participant | Multi-agent meeting system for AI-powered scientific research discussions | [Nature](https://www.nature.com/articles/s41586-025-09442-9) | [README](biodsa/agents/virtuallab/README.md) \| [Tutorial](tutorials/virtuallab_agent.ipynb) |

## Quick Start

### Installation

```bash
git clone https://github.com/RyanWangZf/BioDSA.git
cd BioDSA
pip install pipenv && pipenv install && pipenv shell
```

### Set API Keys

Create a `.env` file:

```bash
OPENAI_API_KEY=your_key_here
# Or use: AZURE_OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY
```

### Run Your First Agent

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

results.to_pdf(output_dir="reports")
```

## Vibe-Prototype New Agents

Use AI coding assistants (Cursor, Claude Code, Codex CLI, Gemini CLI, OpenClaw) to rapidly prototype new agents. The [biodsa-agent-dev-skills/](biodsa-agent-dev-skills/) library teaches your AI assistant the full BioDSA architecture so it can produce working agents that follow all codebase conventions.

**Two supported workflows:**

1. **From reference materials** — Provide a paper or design docs, and the AI builds the agent
2. **Benchmark-driven** — Point to datasets in `benchmarks/`, and the AI builds an agent with an evaluation script

### Install Skills

```bash
./install-cursor.sh        # Cursor (project-level)
./install-claude-code.sh   # Claude Code (global)
./install-codex.sh         # Codex CLI (global)
./install-gemini.sh        # Gemini CLI (global)
./install-openclaw.sh      # OpenClaw (global)
```

All installers support `--project`, `--uninstall`, `--dry-run`, and `--verbose` flags.

Then describe what you want in natural language:

```
"Here is a paper on drug repurposing. Build an agent that implements it
 and evaluate on benchmarks/HLE-medicine/"
```

See the [skill library README](biodsa-agent-dev-skills/README.md) for full details.

## Repository Structure

```
BioDSA/
├── biodsa/                          # Core framework
│   ├── agents/                      # Agent implementations
│   │   ├── base_agent.py            # BaseAgent foundation class
│   │   ├── state.py                 # Shared agent state
│   │   ├── dswizard/                # DSWizard agent
│   │   ├── deepevidence/            # DeepEvidence agent
│   │   ├── trialmind_slr/           # TrialMind-SLR agent
│   │   ├── informgen/               # InformGen agent
│   │   ├── trialgpt/                # TrialGPT agent
│   │   ├── agentmd/                 # AgentMD agent
│   │   ├── geneagent/               # GeneAgent agent
│   │   └── virtuallab/              # Virtual Lab agent
│   ├── tools/                       # Low-level API tools (17+ knowledge bases)
│   ├── tool_wrappers/               # LangChain tool wrappers
│   ├── sandbox/                     # Docker sandbox & ExecutionResults
│   └── memory/                      # Memory graph system
├── benchmarks/                      # Evaluation datasets (10 benchmarks, 1900+ tasks)
├── biodsa-agent-dev-skills/         # Skill library source files (7 markdown guides)
├── install-cursor.sh                # Install skills for Cursor
├── install-claude-code.sh           # Install skills for Claude Code
├── install-codex.sh                 # Install skills for Codex CLI
├── install-gemini.sh                # Install skills for Gemini CLI
├── install-openclaw.sh              # Install skills for OpenClaw
├── install-common.sh                # Shared install logic
├── tutorials/                       # Jupyter notebook tutorials
├── scripts/                         # Example run scripts
├── biodsa_env/                      # Docker sandbox build files
├── tests/                           # Tool and integration tests
└── biomedical_data/                 # Example datasets
```

## Benchmarks

10 benchmarks covering hypothesis validation, code generation, reasoning, QA, and evidence synthesis. See [benchmarks/README.md](benchmarks/README.md).

| Benchmark | Tasks | Type |
|-----------|-------|------|
| BioDSA-1K | 1,029 | Hypothesis validation |
| BioDSBench (Python + R) | 293 | Code generation |
| HLE-Biomedicine / Medicine | 70 | Hard reasoning QA |
| LabBench | 75 | Literature & database QA |
| SuperGPQA | 172 | Expert-level QA |
| TrialPanoramaBench | 50 | Evidence synthesis |
| TRQA-lit | 172 | Translational research QA |

## Sandbox Setup

BioDSA executes agent-generated code in isolated Docker containers. See [biodsa_env/README.md](biodsa_env/README.md).

```bash
cd biodsa_env/python_sandbox
./build_sandbox.sh
```

Without Docker, agents fall back to local `exec()` execution (not recommended for production).

## Documentation

- **Tutorials**: Jupyter notebooks in [tutorials/](tutorials/) for each agent
- **Example Scripts**: Complete examples in [scripts/](scripts/)
- **Agent Docs**: Detailed READMEs in `biodsa/agents/*/README.md`
- **Skill Library**: [biodsa-agent-dev-skills/](biodsa-agent-dev-skills/) for AI-assisted development
- **Benchmarks**: [benchmarks/README.md](benchmarks/README.md) for evaluation datasets

## Citation

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

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

## Links

- **Homepage**: [biodsa.github.io](https://biodsa.github.io)
- **GitHub**: [github.com/RyanWangZf/BioDSA](https://github.com/RyanWangZf/BioDSA)
- **Platform**: [Keiji AI](https://keiji.ai)
- **Datasets**: [BioDSA-1K](https://huggingface.co/datasets/zifeng-ai/BioDSA-1K) | [TrialReviewBench](https://huggingface.co/datasets/zifeng-ai/TrialReviewBench) | [DeepEvidence](https://huggingface.co/datasets/zifeng-ai/DeepEvidence)
