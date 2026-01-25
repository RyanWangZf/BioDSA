<p align="center">
  <img src="./figs/biodsa_logo.svg" alt="BioDSA Logo" width="500">
</p>

# BioDSA: Biomedical Data Science Agents

**BioDSA** is a modular, open-source framework for building, reproducing, and evaluating biomedical data science agents. It is designed for AI agent research, prioritizing clean abstractions, rapid prototyping, and systematic benchmarking to accelerate R&D of AI agents for biomedicine.

**Key Features:**
- 🧱 **Modular Base Agent** - Extend `BaseAgent` with built-in LLM support (OpenAI, Anthropic, Azure, Google), sandboxed execution, and retry handling
- 🔀 **LangGraph Workflows** - Define agent logic as composable state graphs with conditional edges for complex multi-step reasoning
- 🧩 **Plug-and-Play Tools** - Ready-to-use wrappers for PubMed, ClinicalTrials.gov, cBioPortal, gene databases, and more
- 🐳 **Sandboxed Execution** - Execute generated code safely in Docker containers with resource monitoring and artifact collection
- 📊 **Comprehensive Benchmarks** - Evaluate agents on BioDSA-1K, BioDSBench, HLE-Medicine, LabBench, SuperGPQA, and more

## 🎯 Specialized Agents

BioDSA has been used to build and benchmark several specialized agents for biomedical research tasks:

### DSWizard - Biomedical Data Science Agent

Two-phase agent (planning → implementation) for reliable data analysis on biomedical datasets. Achieved **0.74 Pass@1** on BioDSBench, **2× higher** than vanilla prompting.

📄 [Nature BME Paper](https://www.nature.com/articles/s41551-025-01587-2) | 📖 [Documentation](biodsa/agents/dswizard/README.md) | 📓 [Tutorial](tutorials/dswizard_agent.ipynb)

```python
from biodsa.agents import DSWizardAgent
agent = DSWizardAgent(model_name="gpt-5", api_type="openai", api_key="...")
agent.register_workspace("./data/cBioPortal/datasets/acbc_mskcc_2015")
results = agent.go("Perform survival analysis for TP53 mutant vs wild-type patients")
```

### DeepEvidence - Deep Research Agent

Hierarchical multi-agent system (orchestrator + BFS/DFS subagents) for comprehensive biomedical literature research and evidence synthesis across 17+ knowledge bases. Achieved **2×-10× higher performance** than vanilla LLM baselines (e.g., 40% vs 3.3% on HLE-Medicine).

📄 [arXiv Paper](https://arxiv.org/abs/2601.11560) | 📖 [Documentation](biodsa/agents/deepevidence/README.md) | 📓 [Tutorial](tutorials/deepevidence_agent.ipynb)

```python
from biodsa.agents import DeepEvidenceAgent
agent = DeepEvidenceAgent(model_name="gpt-5", api_type="openai", api_key="...")
results = agent.go(
    "What are resistance mechanisms to EGFR inhibitors in lung cancer?",
    knowledge_bases=["pubmed_papers", "gene", "disease", "drug"]
)
results.export_evidence_graph_html("evidence_graph.html")
```

### Other Specialized Agents

- **[TrialMind-SLR](biodsa/agents/trialmind_slr/README.md)** - Systematic literature review agent for clinical trial design
- **[InformGen](biodsa/agents/informgen/README.md)** - Patient information sheet generation for clinical trials  
- **[TrialGPT](biodsa/agents/trialgpt/README.md)** - Clinical trial eligibility screening agent

---

## 🧱 Building Your Own Agent

BioDSA provides base agent classes and components that you can extend to create custom agents:

### BaseAgent - Foundation Class

All agents inherit from `BaseAgent`, which provides:
- Multi-provider LLM support (OpenAI, Anthropic, Azure, Google)
- Sandboxed code execution with Docker
- Workspace and dataset management
- Retry logic, timeout handling, and token tracking

### Example Base Agents

**CoderAgent** - Direct code generation with sandboxed execution ([Tutorial](tutorials/coder_agent.ipynb))

```python
from biodsa.agents import CoderAgent
agent = CoderAgent(model_name="gpt-5", api_type="openai", api_key="...")
agent.register_workspace("./data")
results = agent.go("Create a bar plot of sample distribution")
```

**ReactAgent** - ReAct-style reasoning and action with tool calling

```python
from biodsa.agents import ReactAgent
agent = ReactAgent(model_name="gpt-5", api_type="openai", api_key="...")
agent.register_workspace("./data")
results = agent.go("Analyze the mutation patterns in the dataset")
```

### Creating Custom Agents

Extend `BaseAgent` and define your workflow as a LangGraph state graph:

```python
from biodsa.agents import BaseAgent
from langgraph.graph import StateGraph, END

class MyCustomAgent(BaseAgent):
    def _create_agent_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("step_1", self._first_step)
        workflow.add_node("step_2", self._second_step)
        workflow.add_edge("step_1", "step_2")
        workflow.add_edge("step_2", END)
        workflow.set_entry_point("step_1")
        return workflow.compile()
    
    def go(self, query: str):
        return self.agent_graph.invoke({"messages": [query]})
```

See the [specialized agents](#-specialized-agents) above for real-world examples of custom agents built with BioDSA.

---

## 📝 Update Log

- **2026-01-25**: Added three new clinical trial agents (`TrialMind-SLR`, `InformGen`, `TrialGPT`) with complete documentation, tutorials, and example outputs; restructured README and documentation
- **2025-12-23**: DeepEvidence agent release with hierarchical multi-agent architecture, 17+ knowledge base integrations, persistent evidence graph, and interactive HTML visualization
- **2025-11-25**: Major refactoring with modular agent architecture, Docker sandbox integration, memory graph system with BM25 indexing, comprehensive benchmarks (BioDSA-1K, BioDSBench, HLE-Medicine, LabBench, SuperGPQA), and enhanced ExecutionResults API

---

## 🚀 Quick Start

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

# Initialize agent
agent = DSWizardAgent(
    model_name="gpt-5",
    api_type="openai",
    api_key=os.environ["OPENAI_API_KEY"]
)

# Register dataset
agent.register_workspace("./biomedical_data/cBioPortal/datasets/acbc_mskcc_2015")

# Execute analysis
results = agent.go("Perform survival analysis for TP53 mutant vs wild-type patients")

# Export results
results.to_pdf(output_dir="reports")
results.download_artifacts(output_dir="artifacts")
```

**Next Steps**: Explore [tutorials/](tutorials/), check [benchmarks/](benchmarks/), or build your own agent by extending `BaseAgent`.

---

## 🔧 Framework Components

BioDSA provides a modular architecture with plug-and-play components:

| Component | Description |
|-----------|-------------|
| **Single & Multi-Agent** | Tool calling execution and hierarchical orchestration patterns |
| **Memory Graph** | BM25-indexed context with persistent entity/relationship tracking |
| **MCP Tools** | Model Context Protocol integrations for extensible tool ecosystems |
| **Docker Sandbox** | Isolated containers with Python 3.12, data science libraries, and resource monitoring |
| **Knowledge APIs** | Unified connectors for PubMed, ClinicalTrials.gov, ChEMBL, UniProt, Open Targets, cBioPortal, and 15+ more |
| **LangGraph Workflows** | Composable state graphs with conditional edges for complex reasoning patterns |

---

## 🐳 Sandbox Setup

BioDSA executes agent-generated code in isolated Docker containers for security. If Docker is unavailable, it falls back to local execution (not recommended for production).

### Docker Setup (Recommended)

**Prerequisites**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and ensure it's running.

**Build the sandbox image**:

```bash
cd biodsa_env/python_sandbox
./build_sandbox.sh
```

This creates `biodsa-sandbox-py:latest` with Python 3.12 and data science libraries (pandas, matplotlib, seaborn, scikit-learn, statsmodels, lifelines).

**Verify**:

```bash
docker images | grep biodsa-sandbox-py
```

### Local Execution (Fallback)

Without Docker, agents run code directly in your Python process using `exec()`. This provides no isolation and is **not recommended for untrusted code**. Some features like `download_artifacts()` may be limited.

---

## 📊 Benchmarks

BioDSA includes comprehensive benchmarks for evaluating agent performance on biomedical tasks. See [benchmarks/README.md](benchmarks/README.md) for full documentation.

| Benchmark | Tasks | Description |
|-----------|-------|-------------|
| **BioDSA-1K** | 1,029 | Hypothesis validation from real biomedical studies |
| **BioDSBench** | 293 | Python (128) and R (165) coding for biomedical analysis |
| **DeepEvidence** | Multiple | Evidence synthesis and knowledge graph research |
| **HLE-Biomedicine/Medicine** | 132 | Hard reasoning questions in biology and medicine |
| **LabBench** | 75 | Literature QA and database QA |
| **SuperGPQA** | 264 | Expert-level biology and medicine questions |

**Datasets**: [🤗 HuggingFace](https://huggingface.co/datasets/zifeng-ai/BioDSBench)

---

## 💾 Example Data

BioDSA includes example datasets from [cBioPortal](https://www.cbioportal.org/) in `biomedical_data/cBioPortal/datasets/`. Each dataset contains clinical, mutation, CNA, and structural variant data.

**Download more**: [cBioPortal Datasets](https://www.cbioportal.org/datasets) | [DataHub](https://github.com/cBioPortal/datahub)

---

## 📚 Documentation

- **Tutorials**: Jupyter notebooks in [tutorials/](tutorials/) for each agent
- **Example Scripts**: Complete examples in [scripts/](scripts/)
- **Agent Docs**: Detailed READMEs in `biodsa/agents/*/README.md`
- **API Reference**: See docstrings in source code

---

## 📚 Citation

If you use BioDSA in your research, please cite our papers:

**DeepEvidence (Deep Research Agent)**:
```bibtex
@article{wang2026deepevidence,
  title={DeepEvidence: Empowering Biomedical Discovery with Deep Knowledge Graph Research},
  author={Wang, Zifeng and Chen, Zheng and Yang, Ziwei and Wang, Xuan and Jin, Qiao and Peng, Yifan and Lu, Zhiyong and Sun, Jimeng},
  journal={arXiv preprint arXiv:2601.11560},
  year={2026}
}
```

**DSWizard (Data Science Agent)**:
```bibtex
@article{wang2026reliable,
  title={Making large language models reliable data science programming copilots for biomedical research},
  author={Wang, Zifeng and Danek, Benjamin and Yang, Ziwei and Chen, Zheng and Sun, Jimeng},
  journal={Nature Biomedical Engineering},
  year={2026},
  doi={10.1038/s41551-025-01587-2}
}
```

**BioDSA-1K Benchmark**:
```bibtex
@article{wang2025biodsa1k,
  title={BioDSA-1K: Benchmarking Data Science Agents for Biomedical Research},
  author={Wang, Zifeng and Danek, Benjamin and Sun, Jimeng},
  journal={arXiv preprint arXiv:2505.16100},
  year={2025}
}
```

---

## 📄 License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

---

## 🔗 Links

- **Homepage**: [biodsa.ai](https://biodsa.ai)
- **GitHub**: [github.com/RyanWangZf/BioDSA](https://github.com/RyanWangZf/BioDSA)
- **Datasets**: [HuggingFace](https://huggingface.co/datasets/zifeng-ai/BioDSBench)
- **Commercial Platform**: [TrialMind by Keiji AI](https://keiji.ai/product)
