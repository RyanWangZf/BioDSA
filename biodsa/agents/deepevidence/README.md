# DeepEvidence Agent

DeepEvidence is a hierarchical multi-agent system designed for comprehensive biomedical literature research and evidence synthesis. It leverages deep knowledge graph exploration to systematically gather, analyze, and synthesize evidence from multiple biomedical knowledge bases.

## Overview

DeepEvidence addresses the challenge of conducting thorough biomedical research by implementing a three-tier architecture:

1. **Orchestrator Agent**: Coordinates the overall research strategy, decides which knowledge bases to explore, and synthesizes findings
2. **BFS (Breadth-First Search) Agent**: Explores broad connections across entities in knowledge graphs to discover related concepts
3. **DFS (Depth-First Search) Agent**: Performs deep dives into specific knowledge paths to extract detailed information

This hierarchical approach enables:
- **Systematic exploration** of complex biomedical relationships across multiple knowledge bases
- **Evidence graph construction** that captures entities and their relationships discovered during research
- **Multi-scale search** combining broad exploration (BFS) with deep investigation (DFS)
- **Memory persistence** through an evidence graph that accumulates knowledge across search rounds

## Key Features

### Multi-Knowledge Base Integration

DeepEvidence can seamlessly query and integrate information from diverse biomedical resources:

- **PubMed Papers**: Scientific literature with entity extraction and annotation
- **Genes**: Gene information from multiple databases (NCBI, MyGene)
- **Diseases**: Disease ontologies and clinical information (MONDO, Disease Ontology)
- **Drugs**: Drug databases (DrugBank, ChEMBL, PubChem)
- **Clinical Trials**: ClinicalTrials.gov data
- **Variants**: Genetic variant information (MyVariant)
- **Targets**: Therapeutic target information (Open Targets)
- **Pathways**: Biological pathway data (Reactome, KEGG)
- **Compounds**: Chemical compound information
- **Web Search**: General web search for supplementary information

### Evidence Graph

DeepEvidence builds a persistent knowledge graph during research that:
- Captures entities (papers, genes, diseases, drugs, etc.) and their relationships
- Enables retrieval of previously discovered information
- Supports iterative refinement of research questions
- Provides visualization capabilities (HTML/PDF/image formats)

### Hierarchical Search Strategy

The orchestrator intelligently dispatches search tasks:
- **BFS mode**: Discovers related entities and broad connections
- **DFS mode**: Deep investigation of specific hypotheses or relationships
- **Adaptive budgeting**: Configurable search depth and action rounds

## Architecture

```
┌─────────────────────────────────────────┐
│     Orchestrator Agent                  │
│  - Strategy coordination                │
│  - Knowledge base selection             │
│  - Evidence synthesis                   │
└────────┬────────────────────┬───────────┘
         │                    │
    ┌────▼────┐          ┌────▼────┐
    │ BFS     │          │ DFS     │
    │ Agent   │          │ Agent   │
    └────┬────┘          └────┬────┘
         │                    │
         └────────┬───────────┘
                  │
         ┌────────▼────────┐
         │ Knowledge Base  │
         │ Tools & APIs    │
         └─────────────────┘
```

## Usage

### Basic Example

```python
import os
from biodsa.agents import DeepEvidenceAgent

# Initialize the agent
agent = DeepEvidenceAgent(
    model_name="gpt-5",
    api_type="openai",
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Execute a research query
results = agent.go(
    "What are the mechanisms of resistance to EGFR inhibitors in lung cancer?",
    knowledge_bases=["pubmed_papers", "gene", "disease", "drug"]
)

# View results
print(results)

# Access the evidence graph
print(f"Discovered {len(results.evidence_graph_data.get('entities', []))} entities")
print(f"Found {len(results.evidence_graph_data.get('relations', []))} relationships")

# Export interactive HTML visualization
results.export_evidence_graph_html("evidence_graph.html")

# Download generated artifacts
results.download_artifacts(output_dir="output_artifacts")

# Generate comprehensive PDF report with evidence graph
results.to_pdf(output_dir="reports")

# Clean up
agent.clear_workspace()
```

### Selecting Knowledge Bases

You can customize which knowledge bases the agent uses:

```python
# Use only papers and gene databases
results = agent.go(
    "What genes are associated with Alzheimer's disease?",
    knowledge_bases=["pubmed_papers", "gene", "disease"]
)

# Use clinical trial and drug information
results = agent.go(
    "What are the latest treatments for melanoma?",
    knowledge_bases=["clinical_trials", "drug", "disease"]
)

# Use all available knowledge bases (default)
results = agent.go(
    "Comprehensive analysis of CAR-T therapy mechanisms",
    knowledge_bases=None  # Uses all: pubmed_papers, gene, disease, drug, etc.
)
```

### Light Mode (Without Evidence Graph)

For simpler queries that don't require persistent memory:

```python
agent = DeepEvidenceAgent(
    model_name="gpt-5",
    api_type="openai",
    api_key=os.environ.get("OPENAI_API_KEY"),
    light_mode=True  # Disables evidence graph
)

results = agent.go("Quick literature review on CRISPR applications")
```

## Advanced Configuration

### Search Budget Parameters

Control the depth and extent of research:

```python
agent = DeepEvidenceAgent(
    model_name="gpt-5",
    api_type="openai",
    api_key=os.environ.get("OPENAI_API_KEY"),
    main_search_rounds_budget=5,        # Max BFS/DFS search rounds
    main_action_rounds_budget=20,       # Max orchestrator actions
    subagent_action_rounds_budget=5     # Max actions per BFS/DFS agent
)
```

**Budget Parameters Explained:**
- `main_search_rounds_budget`: How many times the orchestrator can call BFS/DFS agents
- `main_action_rounds_budget`: Total number of actions the orchestrator can take
- `subagent_action_rounds_budget`: How many tools each BFS/DFS agent can call

### Dual Model Configuration

Use a smaller model for BFS/DFS agents to reduce costs:

```python
agent = DeepEvidenceAgent(
    # Main orchestrator model (high capability)
    model_name="gpt-5",
    api_type="openai",
    api_key=os.environ.get("OPENAI_API_KEY"),
    
    # BFS/DFS sub-agent model (cost-effective)
    small_model_name="gpt-4o-mini",
    small_model_api_type="openai",
    small_model_api_key=os.environ.get("OPENAI_API_KEY"),
)
```

### Custom Evidence Graph Storage

Specify a custom directory for evidence graph cache:

```python
agent = DeepEvidenceAgent(
    model_name="gpt-5",
    api_type="openai",
    api_key=os.environ.get("OPENAI_API_KEY"),
    evidence_graph_cache_dir="/path/to/custom/cache"
)
```

### Azure OpenAI Configuration

```python
agent = DeepEvidenceAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    model_kwargs={
        "max_completion_tokens": 5000,
        "reasoning_effort": "medium",
    }
)
```

## Working with Results

### Execution Results API

The `DeepEvidenceExecutionResults` object extends the base `ExecutionResults` with evidence graph capabilities:

```python
results = agent.go("Your research question")

# Access standard execution information
print(f"Total iterations: {len(results.message_history)}")
print(f"Code executions: {len(results.code_execution_results)}")
print(f"Final response: {results.final_response}")

# Token usage tracking
print(f"Input tokens: {results.total_input_tokens}")
print(f"Output tokens: {results.total_output_tokens}")

# Evidence graph data
print(f"Entities discovered: {len(results.evidence_graph_data.get('entities', []))}")
print(f"Relations found: {len(results.evidence_graph_data.get('relations', []))}")

# Explore specific entities
for entity in results.evidence_graph_data.get('entities', [])[:5]:
    print(f"- {entity['name']} ({entity['entityType']})")
```

### Evidence Graph Visualization

Export the evidence graph in multiple formats:

```python
# Interactive HTML visualization (recommended)
results.export_evidence_graph_html("evidence_graph.html")

# PDF visualization (requires playwright)
results.export_evidence_graph_pdf("graph.html", "graph.pdf")

# Export as JSON for programmatic access
results.to_json("results.json")
```

### Generate Comprehensive Report

Create a PDF report with embedded evidence graph:

```python
pdf_path = results.to_pdf(
    output_dir="reports",
    filename="research_report.pdf",
    include_artifacts=True
)
print(f"Report saved to: {pdf_path}")
```

The PDF includes:
- User query and metadata
- Agent exploration process
- Results and analysis with figures
- Evidence graph visualization
- Code execution details

## Example Research Queries

### Drug Discovery

```python
results = agent.go(
    "What are the latest FDA-approved immunotherapy drugs for melanoma "
    "and their mechanisms of action?",
    knowledge_bases=["clinical_trials", "drug", "disease", "target"]
)
```

### Gene-Disease Association

```python
results = agent.go(
    "Identify novel genetic variants associated with Type 2 diabetes "
    "and their functional implications",
    knowledge_bases=["gene", "disease", "variant", "pubmed_papers"]
)
```

### Pathway Analysis

```python
results = agent.go(
    "Map the signaling pathways involved in cancer stem cell maintenance "
    "and potential therapeutic targets",
    knowledge_bases=["pathway", "gene", "drug", "pubmed_papers"]
)
```

### Clinical Trial Analysis

```python
results = agent.go(
    "Summarize ongoing Phase III trials for Alzheimer's disease treatment "
    "and their primary endpoints",
    knowledge_bases=["clinical_trials", "disease", "drug"]
)
```

## Knowledge Base Details

### Available Knowledge Bases

| Knowledge Base | Description | Key Tools |
|---------------|-------------|-----------|
| `pubmed_papers` | Scientific literature | Search, fetch content, entity extraction, annotations |
| `gene` | Gene information | Search genes, fetch details (NCBI, MyGene) |
| `disease` | Disease ontologies | Search diseases, fetch details (MONDO, DO) |
| `drug` | Drug databases | Search drugs, fetch details (DrugBank, ChEMBL) |
| `variant` | Genetic variants | Search variants, fetch details (MyVariant) |
| `clinical_trials` | Clinical trials data | Search trials, fetch trial details |
| `target` | Therapeutic targets | Search targets, fetch details (Open Targets) |
| `pathway` | Biological pathways | Search pathways, fetch details (Reactome, KEGG) |
| `compound` | Chemical compounds | Search compounds, fetch details |
| `web_search` | General web search | Search the web for supplementary information |

### Tool Categories by Knowledge Base

Each knowledge base provides specialized tools:

**PubMed Papers:**
- `SearchPapersTool`: Find relevant papers by keywords
- `FetchPaperContentTool`: Retrieve full paper abstracts and metadata
- `FetchPaperAnnotationsTool`: Get biomedical entity annotations
- `FindEntitiesTool`: Extract entities from text
- `FindRelatedEntitiesTool`: Discover entity relationships
- `GetPaperReferencesTool`: Fetch citation network

**Gene/Disease/Drug:**
- `UnifiedGeneSearchTool`: Search across gene databases
- `UnifiedGeneDetailsFetchTool`: Retrieve detailed gene information
- Similar unified interfaces for diseases and drugs

## Memory and Caching

### Evidence Graph Persistence

By default, DeepEvidence creates a persistent evidence graph:

```python
# The evidence graph is stored in cache between runs
agent = DeepEvidenceAgent(
    model_name="gpt-5",
    api_type="openai",
    api_key=os.environ.get("OPENAI_API_KEY"),
    evidence_graph_cache_dir="/path/to/cache"  # Persists across sessions
)

# First query builds initial graph
results1 = agent.go("What causes Parkinson's disease?")

# Second query can reference previously discovered entities
results2 = agent.go("How do these Parkinson's genes interact?")
```

### Clearing the Cache

```python
# Clear cache before each query (default behavior)
results = agent.go("Your query", clear_evidence_graph_cache=True)

# Preserve cache between queries
results = agent.go("Your query", clear_evidence_graph_cache=False)
```

## Performance Considerations

### Token Usage

Track and optimize token consumption:

```python
results = agent.go("Your research query")

total_cost = (
    results.total_input_tokens * INPUT_TOKEN_COST +
    results.total_output_tokens * OUTPUT_TOKEN_COST
)
print(f"Estimated cost: ${total_cost:.2f}")
```

### Search Budget Optimization

For cost-sensitive applications:

```python
# Minimal configuration
agent = DeepEvidenceAgent(
    model_name="gpt-4o-mini",
    api_type="openai",
    api_key=os.environ.get("OPENAI_API_KEY"),
    main_search_rounds_budget=2,
    main_action_rounds_budget=10,
    subagent_action_rounds_budget=3,
    light_mode=True  # Disable evidence graph
)
```

For comprehensive research:

```python
# Maximum exploration
agent = DeepEvidenceAgent(
    model_name="gpt-5",
    api_type="openai",
    api_key=os.environ.get("OPENAI_API_KEY"),
    main_search_rounds_budget=10,
    main_action_rounds_budget=30,
    subagent_action_rounds_budget=8
)
```

## Troubleshooting

### UMLS Integration

Some tools require a UMLS API key:

```bash
# Add to your .env file
UMLS_API_KEY=your_umls_api_key_here
```

Get your UMLS API key from: https://uts.nlm.nih.gov/uts/

### Docker Sandbox

DeepEvidence uses Docker for code execution. Ensure Docker is running:

```bash
docker ps
```

If the sandbox fails, check the build:

```bash
cd biodsa_env/python_sandbox
./build_sandbox.sh
```

### Memory Issues

For large evidence graphs, increase Docker memory limits:

```bash
# Docker Desktop: Settings → Resources → Memory
# Recommended: 8GB or more
```

## Citation

If you use DeepEvidence in your research, please cite:

```bibtex
@article{wang2025deepevidence,
  title={DeepEvidence: Empowering Biomedical Discovery with Deep Knowledge Graph Research},
  author={Wang, Zifeng and Chen, Zheng and Yang, Ziwei and Wang, Xuan and Jin, Qiao and Peng, Yifan and Lu, Zhiyong and Sun, Jimeng
},
  journal={arxiv Preprint},
  year={2025}
}
```

## Example Script

See `scripts/run_deepevidence_agent.py` for a complete working example:

```python
from biodsa.agents import DeepEvidenceAgent

agent = DeepEvidenceAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    subagent_action_rounds_budget=5,
    main_search_rounds_budget=2,
    main_action_rounds_budget=15,
)

execution_results = agent.go(
    "Summarizing the cutting-edge immunotherapy drugs in late clinical trial "
    "phase or have been approved for NSCLC?",
    knowledge_bases=["pubmed_papers", "clinical_trials", "drug", "disease"],
)

print(execution_results.to_json())
execution_results.to_pdf(output_dir="test_artifacts")
agent.clear_workspace()
```

## Related Agents

- **[CoderAgent](../coder_agent.py)**: Direct code generation for data analysis tasks
- **[ReactAgent](../react_agent.py)**: ReAct-style reasoning and action agent
- **[DSWizardAgent](../dswizard/)**: Two-phase planning and implementation agent

DeepEvidence is specialized for comprehensive literature research and evidence synthesis, while other agents focus on data analysis and coding tasks.

