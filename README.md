<p align="center">
  <img src="./figs/biodsa_logo.svg" alt="BioDSA Logo" width="500">
</p>


# BioDSA: Biomedical Data Science Agents

BioDSA is an extensible library of data science agents designed for biomedical research. It provides a unified framework for building, deploying, and extending AI agents that can analyze biomedical data, search knowledge graphs, and synthesize scientific evidence.

The library is designed to be modular—you can use the existing research agents for your biomedical analysis tasks, or extend the base agent classes to develop new specialized agents for your specific needs.

## 🔬 Research Agents

### DSWizard

**DSWizard** (Data Science Wizard) is a two-phase agent designed for reliable biomedical data analysis. It operates by first creating a detailed analysis plan in natural language, then converting that plan into executable Python code.

📄 **Paper**: [BioDSA-1K: Benchmarking Data Science Agents for Biomedical Research](https://arxiv.org/abs/2505.16100) and [Can Large Language Models Replace Data Scientists in Biomedical Research?](https://arxiv.org/abs/2410.21591)

📖 **Documentation**: [biodsa/agents/dswizard/README.md](biodsa/agents/dswizard/README.md)

📓 **Tutorial**: [tutorials/dswizard_agent.ipynb](tutorials/dswizard_agent.ipynb)

**Key Features**:
- Two-phase planning and implementation approach
- Dataset exploration before committing to analysis strategy
- Structured analysis plans with quality control steps
- Sandboxed Python code execution

```python
from biodsa.agents import DSWizardAgent

agent = DSWizardAgent(model_name="gpt-5", api_type="openai", api_key="...")
agent.register_workspace("./biomedical_data/cBioPortal/datasets/acbc_mskcc_2015")
results = agent.go("Perform survival analysis comparing TP53 mutant vs wild-type patients")
```

---

### DeepEvidence

**DeepEvidence** is a hierarchical multi-agent system for comprehensive biomedical literature research and evidence synthesis. It leverages deep knowledge graph exploration to systematically gather, analyze, and synthesize evidence from 17+ biomedical knowledge bases.

📄 **Paper**: DeepEvidence: Empowering Biomedical Discovery with Deep Knowledge Graph Research (In submission)

📖 **Documentation**: [biodsa/agents/deepevidence/README.md](biodsa/agents/deepevidence/README.md)

📓 **Tutorial**: [tutorials/deepevidence_agent.ipynb](tutorials/deepevidence_agent.ipynb)

**Key Features**:
- Orchestrator + BFS/DFS subagent architecture for multi-scale search
- Integration with PubMed, ChEMBL, ClinicalTrials.gov, Gene Ontology, and more
- Persistent evidence graph with entity and relationship tracking
- Interactive HTML visualization of discovered knowledge

```python
from biodsa.agents import DeepEvidenceAgent

agent = DeepEvidenceAgent(model_name="gpt-5", api_type="openai", api_key="...")
results = agent.go(
    "What are the mechanisms of resistance to EGFR inhibitors in lung cancer?",
    knowledge_bases=["pubmed_papers", "gene", "disease", "drug"]
)
results.export_evidence_graph_html("evidence_graph.html")
```

---

## 🧱 Base Agents

BioDSA provides extensible base agent classes that you can use directly or extend for custom applications:

### CoderAgent

📓 **Tutorial**: [tutorials/coder_agent.ipynb](tutorials/coder_agent.ipynb)

A direct code generation agent that writes and executes Python/R code in a sandboxed environment.

```python
from biodsa.agents import CoderAgent

agent = CoderAgent(model_name="gpt-5", api_type="openai", api_key="...")
agent.register_workspace("./data")
results = agent.go("Create a bar plot of sample distribution")
```

### ReactAgent

A ReAct-style (Reasoning + Acting) agent that uses tool calling for iterative problem solving.

```python
from biodsa.agents import ReactAgent

agent = ReactAgent(model_name="gpt-5", api_type="openai", api_key="...")
agent.register_workspace("./data")
results = agent.go("Analyze the mutation patterns in the dataset")
```

---

## 📝 Update Log

### 2025-12-23: DeepEvidence Agent Release

- Added `DeepEvidenceAgent` for comprehensive biomedical literature research and evidence synthesis
- Implemented hierarchical multi-agent architecture with Orchestrator + BFS/DFS subagents
- Integrated 17+ biomedical knowledge bases: PubMed, ChEMBL, ClinicalTrials.gov, Gene Ontology, HPO, KEGG, NCBI, OpenFDA, Open Genes, ProteinAtlas, PubChem, PubTator, Reactome, StringDB, UMLS, UniProt, and more
- Developed unified modality-wise search tools for cross-knowledge-graph entity bridging
- Added persistent evidence graph with entity/relationship tracking and interactive HTML visualization
- Created DeepEvidence benchmark suite: Cohort Optimization, Safety Criteria, Dose Design, Drug Discovery, Drug Repurposing, Endpoint Selection, Evidence Gap Analysis, and Sample Size Estimation

### 2025-11-25: Major Codebase Refactoring

- Restructured agent architecture for improved modularity and extensibility
- Added base agent implementations: `CoderAgent`, `ReactAgent`, `DSWizardAgent`
- Introduced sandboxed execution environment with Docker integration
- Implemented comprehensive tool wrapper system for PubMed, Clinical Trials, and code execution
- Added memory graph system with BM25 indexing for enhanced context management
- Integrated benchmarks: BioDSA-1K, BioDSBench, HLE-Medicine, LabBench, SuperGPQA, TrialPanorama
- Enhanced `ExecutionResults` API with PDF report generation, artifact management, and JSON export
- Included example cBioPortal datasets for quick start and testing

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/BioDSA.git
cd BioDSA
```

### 2. Set Up Python Environment

We recommend using Python 3.12. Install dependencies using `pipenv`:

```bash
pip install pipenv
pipenv install
pipenv shell
```

### 3. Set Environment Variables

Create a `.env` file with your API credentials:

```bash
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint

# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_key

# Google Gemini
GOOGLE_API_KEY=your_google_key
```

### 4. Run Your First Agent

```python
import os
from biodsa.agents import CoderAgent

agent = CoderAgent(
    model_name="gpt-5",
    api_type="openai",
    api_key=os.environ.get("OPENAI_API_KEY")
)

agent.register_workspace("./biomedical_data/cBioPortal/datasets/acbc_mskcc_2015")
results = agent.go("Create a bar plot showing the distribution of samples per table")

print(results)
results.download_artifacts(output_dir="output_artifacts")
results.to_pdf(output_dir="reports")
```

---

## 🐳 Sandbox Setup

BioDSA supports two execution modes for agent-generated code: **Docker sandbox** (recommended) and **local execution** (fallback).

### Execution Modes

| Mode | Docker Required | Security | Artifacts | Use Case |
|------|-----------------|----------|-----------|----------|
| **Docker Sandbox** | ✅ Yes | ✅ Isolated container | ✅ Full support | Production, untrusted code |
| **Local Execution** | ❌ No | ⚠️ Runs in your Python process | ⚠️ Limited | Quick testing, trusted code |

### Without Docker (Local Execution)

If Docker is not available, agents automatically fall back to **local execution mode**:

- Code runs directly in your Python process using `exec()`
- Variables persist across executions within the same session
- Matplotlib plots are captured automatically
- **Limitations:**
  - No process isolation—code has full access to your system
  - Generated files are saved to your current working directory
  - Some artifact download features (e.g., `download_artifacts()`) are unavailable
  - Not recommended for untrusted or LLM-generated code in production

### With Docker (Recommended)

For secure, isolated code execution, set up the Docker sandbox:

#### Prerequisites

- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Engine
- Ensure Docker daemon is running

#### Build the Python Sandbox

```bash
cd biodsa_env/python_sandbox
./build_sandbox.sh
```

This builds a Docker image `biodsa-sandbox-py:latest` with:
- Python 3.12
- Data science libraries (pandas, matplotlib, seaborn, scikit-learn, etc.)
- Statistical analysis tools (statsmodels, lifelines, etc.)

Monitor build progress:

```bash
tail -f biodsa_env/python_sandbox/build.log
```

Verify installation:

```bash
docker images | grep biodsa-sandbox-py
```

---

## 📊 Benchmarks

BioDSA includes comprehensive benchmark datasets for evaluating agent performance on biomedical data science tasks.

📖 **Full Documentation**: [benchmarks/README.md](benchmarks/README.md)

**Available Benchmarks**:

| Benchmark | Description | Tasks |
|-----------|-------------|-------|
| BioDSA-1K | Hypothesis validation from real biomedical studies | 1,029 |
| BioDSBench-Python | Python coding tasks for biomedical analysis | 128 |
| BioDSBench-R | R coding tasks for biomedical analysis | 165 |
| DeepEvidence | Evidence synthesis and knowledge graph research | Multiple task types |
| HLE-Biomedicine | Hard biomedical reasoning questions | 102 |
| HLE-Medicine | Hard medical reasoning questions | 30 |
| LabBench | Literature QA and database QA | 75 |
| SuperGPQA | Expert-level biology and medicine questions | 264 |

---

## 💾 Data

### cBioPortal Datasets

The `biomedical_data/cBioPortal/` directory contains example datasets from [cBioPortal](https://www.cbioportal.org/):

```
biomedical_data/cBioPortal/datasets/acbc_mskcc_2015/
├── data_clinical_patient.csv
├── data_clinical_sample.csv
├── data_mutations.csv
├── data_cna.csv
├── data_sv.csv
├── data_gene_panel_matrix.csv
├── available_table_paths.json
└── LICENSE
```

**Download more datasets**:
- Portal: https://www.cbioportal.org/datasets
- DataHub: https://github.com/cBioPortal/datahub

---

## 🔧 Advanced Configuration

### Custom Sandbox Configuration

```python
agent = CoderAgent(
    model_name="gpt-5",
    api_type="openai",
    api_key=os.environ.get("OPENAI_API_KEY"),
    sandbox_image="biodsa-sandbox-py:latest",
    workdir="/workdir"
)
```

### Working with Execution Results

```python
results = agent.go("Your task")

# Access components
print(f"Messages: {len(results.message_history)}")
print(f"Code executions: {len(results.code_execution_results)}")
print(f"Final response: {results.final_response}")

# Export
results.to_json("results.json")
results.to_pdf(output_dir="reports")
results.download_artifacts(output_dir="outputs")

# Resource monitoring
for execution in results.code_execution_results:
    print(f"Runtime: {execution.get('running_time')}s")
    print(f"Peak memory: {execution.get('peak_memory_mb')}MB")
```

### Managing Sandbox Lifecycle

```python
agent.clear_workspace()  # Clear workspace and stop sandbox
```

---

## 📝 Example Scripts

Check the `scripts/` directory for complete examples:

```bash
python scripts/run_coder_agent.py
python scripts/run_dswizard_agent.py
python scripts/run_deepevidence_agent.py
python scripts/run_react_agent.py
```

---

## 📚 Citation

If you use BioDSA in your research, please cite our papers:

```bibtex
@article{wang2025deepevidence,
  title={DeepEvidence: Empowering Biomedical Discovery with Deep Knowledge Graph Research},
  author={Wang, Zifeng and Chen, Zheng and Yang, Ziwei and Wang, Xuan and Jin, Qiao and Peng, Yifan and Lu, Zhiyong and Sun, Jimeng
},
  journal={arxiv Preprint},
  year={2025}
}

@article{wang2025biodsa1k,
  title={BioDSA-1K: Benchmarking Data Science Agents for Biomedical Research},
  author={Wang, Zifeng and Danek, Benjamin and Sun, Jimeng},
  journal={arXiv preprint arXiv:2505.16100},
  year={2025}
}

@article{wang2024llm,
  title={Can Large Language Models Replace Data Scientists in Biomedical Research?},
  author={Wang, Zifeng and Danek, Benjamin and Yang, Ziwei and Chen, Zheng and Sun, Jimeng},
  journal={arXiv preprint arXiv:2410.21591},
  year={2024}
}
```

---

## 📄 License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.
