# BioDSA: Biomedical Data Science Agents

This codebase provides a complete suite for running biomedical data science agents with sandboxed execution environments. The implementation is based on research from two papers:

1. **BioDSA-1K: Benchmarking Data Science Agents for Biomedical Research** ([arXiv:2505.16100](https://arxiv.org/abs/2505.16100))
2. **Can Large Language Models Replace Data Scientists in Biomedical Research?** ([arXiv:2410.21591](https://arxiv.org/abs/2410.21591))

## Update Log
- **2025-11-25**: Major codebase refactoring and enhancement
  - Restructured agent architecture for improved modularity and extensibility
  - Added multiple agent implementations: `CoderAgent`, `ReactAgent`, and `DSWizardAgent` with specialized capabilities
  - Introduced sandboxed execution environment with Docker integration for secure code execution
  - Implemented comprehensive tool wrapper system for PubMed, Clinical Trials, and code execution
  - Added memory graph system with BM25 indexing for enhanced context management
  - Integrated benchmarks: BioDSA-1K, BioDSBench-Python, BioDSBench-R, HLE-Medicine, LabBench, SuperGPQA, TrialPanorama.
  - Enhanced `ExecutionResults` API with PDF report generation, artifact management, and JSON export
  - Included example cBioPortal datasets for quick start and testing
  - Improved documentation with detailed setup guides, usage examples, and API references

## 🚀 Quick Start

Here's a minimal example to get started with BioDSA agents:

```python
import os
from biodsa.agents import CoderAgent

# Initialize the agent
agent = CoderAgent(
    model_name="gpt-5",
    api_type="openai",
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Register a dataset for analysis
agent.register_dataset("./biomedical_data/cBioPortal/datasets/acbc_mskcc_2015")

# Execute a data science task
results = agent.go("Create a bar plot showing the distribution of samples per table")

# View results
print(results)

# Download generated artifacts (figures, tables, etc.)
results.download_artifacts(output_dir="output_artifacts")

# Generate structured PDF report
results.to_pdf(output_dir="reports")
```

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/BioDSA.git
cd BioDSA
```

### 2. Set Up Python Environment

We recommend using Python 3.12. Install dependencies using `pipenv`:

```bash
# Install pipenv if you haven't already
pip install pipenv

# Install dependencies
pipenv install

# Activate the virtual environment
pipenv shell
```

### 3. Set Environment Variables

Create a `.env` file in the root directory with your API credentials:

```bash
# For OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# For Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_key_here
AZURE_OPENAI_ENDPOINT=your_azure_endpoint_here

# For Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_key_here

# For Google Gemini
GOOGLE_API_KEY=your_google_key_here
```

## 🐳 Sandbox Setup

BioDSA uses Docker containers to provide isolated execution environments for running data analysis code safely.

### Prerequisites

- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Engine
- Ensure Docker daemon is running

### Build the Python Sandbox

```bash
cd biodsa_env/python_sandbox
./build_sandbox.sh
```

This script builds a Docker image named `biodsa-sandbox-py:latest` with:
- Python 3.12
- Common data science libraries (pandas, matplotlib, seaborn, scikit-learn, etc.)
- Statistical analysis tools (statsmodels, lifelines, etc.)
- Jupyter notebook support

The build process runs in the background and logs output to `build.log`. You can monitor progress:

```bash
tail -f biodsa_env/python_sandbox/build.log
```

**Verify Installation:**

```bash
docker images | grep biodsa-sandbox-py
```

You should see an image named `biodsa-sandbox-py` with the `latest` tag.

### R Sandbox (Future Support)

R sandbox support is currently under development. Stay tuned for updates!

## 🎯 Usage

```python
from biodsa.agents import CoderAgent

agent = CoderAgent(
    model_name="gpt-5",
    api_type="openai",
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Register dataset
agent.register_dataset("biomedical_data/cBioPortal/datasets/acbc_mskcc_2015")

# Execute task
results = agent.go("Perform survival analysis and create Kaplan-Meier plot")
```


### Working with Execution Results

The `ExecutionResults` object provides multiple ways to interact with analysis outputs:

```python
# Execute analysis
results = agent.go("Your data science task")

# Pretty print results
print(results)  # Shows formatted execution history and results

# Download artifacts (plots, tables, etc.)
artifact_files = results.download_artifacts(output_dir="my_outputs")
print(f"Downloaded {len(artifact_files)} artifacts")

# Export to JSON
results.to_json("results.json")

# Generate PDF report with embedded figures
pdf_path = results.to_pdf(output_dir="reports")
print(f"PDF report saved to: {pdf_path}")

# Access components directly
print(f"Messages: {len(results.message_history)}")
print(f"Code executions: {len(results.code_execution_results)}")
print(f"Final response: {results.final_response}")
```

### Managing Sandbox Lifecycle

```python
# Clear the workspace and stop the sandbox
agent.clear_workspace()
```

## 📊 Benchmarks

BioDSA includes three benchmark datasets for evaluating agent performance:

### 1. BioDSA-1K

**1,029 hypothesis validation tasks** from real biomedical studies.

- **Location**: `benchmarks/BioDSA-1K/`
- **Format**: Parquet file with hypothesis-evidence pairs
- **Full dataset**: [HuggingFace - BioDSA-1K](https://huggingface.co/datasets/zifeng-ai/BioDSA-1K)

**Structure**: Each task includes:
- Hypothesis statement
- Supporting evidence
- Data tables
- Analysis plan
- Ground truth labels

### 2. BioDSBench-Python

**128 Python coding tasks** for biomedical data analysis.

- **Location**: `benchmarks/BioDSBench-Python/`
- **Format**: JSONL with task descriptions and table schemas
- **Full dataset**: [HuggingFace - BioDSBench](https://huggingface.co/datasets/zifeng-ai/BioDSBench)

### 3. BioDSBench-R

**165 R coding tasks** for biomedical data analysis.

- **Location**: `benchmarks/BioDSBench-R/`
- **Format**: JSONL with task descriptions and table schemas
- **Full dataset**: [HuggingFace - BioDSBench](https://huggingface.co/datasets/zifeng-ai/BioDSBench)

## 💾 Data

### cBioPortal Datasets

The `biomedical_data/cBioPortal/` directory contains example datasets from [cBioPortal](https://www.cbioportal.org/):

- Clinical patient data
- Clinical sample data
- Mutation data (MAF format)
- Copy number alteration data
- Structural variant data
- Gene panel information

**Example dataset structure:**
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

**Download more datasets:**
- Portal: https://www.cbioportal.org/datasets
- DataHub: https://github.com/cBioPortal/datahub

## 🔧 Advanced Configuration

### Custom Sandbox Configuration

```python
agent = CoderAgent(
    model_name="gpt-5",
    api_type="openai",
    api_key=os.environ.get("OPENAI_API_KEY"),
    sandbox_image="biodsa-sandbox-py:latest",  # Custom image
    workdir="/workdir"  # Custom working directory in container
)
```

### Memory and Resource Monitoring

Execution results include resource usage metrics:

```python
results = agent.go("Your task")

for execution in results.code_execution_results:
    print(f"Exit code: {execution.get('exit_code')}")
    print(f"Runtime: {execution.get('running_time')}s")
    print(f"Peak memory: {execution.get('peak_memory_mb')}MB")
```

## 📝 Example Scripts

Check the `scripts/` directory for complete examples:

```bash
# Run the coder agent example
python scripts/run_coder_agent.py
```

## 📚 Citation

If you use BioDSA in your research, please cite our papers:

```bibtex
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
