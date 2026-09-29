# GeneAgent: Self-verification Language Agent for Gene Set Analysis

GeneAgent is a language agent that autonomously interacts with domain-specific databases to annotate functions for gene sets. At the core of GeneAgent's functionality is a **self-verification mechanism** that uses external databases to verify and refine its analysis, reducing hallucination and enabling reliable, evidence-based insights.

## Reference

This implementation is based on the original GeneAgent:

> Wang, Z., Jin, Q., Wei, C.H., et al. (2025). GeneAgent: self-verification language agent for gene-set analysis using domain databases. *Nature Methods*, 22, 1677–1685.

📄 **Paper**: [Nature Methods](https://www.nature.com/articles/s41592-025-02748-6) | **Original Repository**: [github.com/ncbi-nlp/GeneAgent](https://github.com/ncbi-nlp/GeneAgent)

## How It Works

GeneAgent implements a **cascade verification** workflow:

```
┌─────────────────────────────────────────────────────────┐
│                    GeneAgent Workflow                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. INITIAL ANALYSIS                                    │
│     └─ Generate process name + summary for gene set     │
│                                                          │
│  2. TOPIC VERIFICATION                                  │
│     ├─ Generate claims about the process name           │
│     └─ Verify each claim using domain databases         │
│                                                          │
│  3. TOPIC UPDATE                                        │
│     └─ Refine process name based on evidence            │
│                                                          │
│  4. ANALYSIS VERIFICATION                               │
│     ├─ Generate claims about gene functions             │
│     └─ Verify each claim using domain databases         │
│                                                          │
│  5. FINAL SUMMARY                                       │
│     └─ Generate refined summary with evidence support   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Features

- **Multi-API Support:** Works with Azure OpenAI, OpenAI, Anthropic (Claude), and Google (Gemini)
- **Self-Verification:** Automatically verifies claims using domain-specific databases
- **Configurable:** Adjustable verification depth, temperature, and output format
- **Evidence-Based:** All claims are backed by database evidence

## Quick Start

```python
from biodsa.agents.geneagent import GeneAgent

# Initialize the agent
agent = GeneAgent(
    model_name="gpt-4o",
    api_type="azure",  # or "openai", "anthropic", "google"
    api_key="your-api-key",
    endpoint="your-endpoint"
)

# Analyze a gene set
gene_set = "ERBB2,ERBB4,FGFR2,FGFR4,HRAS,KRAS"
results = agent.go(gene_set)

# Print the final analysis
print(results.final_response)
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | str | required | LLM model name (e.g., "gpt-4o", "claude-3-opus") |
| `api_type` | str | required | API provider: "azure", "openai", "anthropic", "google" |
| `api_key` | str | required | API key for the provider |
| `endpoint` | str | required | API endpoint URL |
| `max_verification_rounds` | int | 20 | Max tool calls per claim verification |
| `max_claims_per_stage` | int | None | Max claims to verify per stage (None = all). Set to 1-3 for quick demos |
| `temperature` | float | 1.0 | LLM temperature for generation |
| `include_verification_reports` | bool | True | Include verification reports in output |

## Quick Demo Mode

For faster demos with reduced API calls, limit the number of claims verified:

```python
agent = GeneAgent(
    model_name="gpt-4o",
    api_type="azure",
    api_key="your-key",
    endpoint="your-endpoint",
    max_claims_per_stage=2,      # Only verify 2 claims per stage
    max_verification_rounds=5,   # Limit tool calls per claim
)
```

## Supported LLM Models

### Azure OpenAI
```python
agent = GeneAgent(
    model_name="gpt-4o",  # or "gpt-4", "gpt-4o-mini"
    api_type="azure",
    api_key="your-azure-key",
    endpoint="https://your-resource.openai.azure.com/"
)
```

### OpenAI
```python
agent = GeneAgent(
    model_name="gpt-4o",
    api_type="openai",
    api_key="your-openai-key",
    endpoint="https://api.openai.com/v1"
)
```

### Anthropic (Claude)
```python
agent = GeneAgent(
    model_name="claude-3-opus-20240229",
    api_type="anthropic",
    api_key="your-anthropic-key",
    endpoint="https://api.anthropic.com"
)
```

### Google (Gemini)
```python
agent = GeneAgent(
    model_name="gemini-pro",
    api_type="google",
    api_key="your-google-key",
    endpoint=""  # Not needed for Google
)
```

## Domain Database Tools

GeneAgent uses 8 tools to verify claims against domain databases:

### Gene Set Tools (Multiple Genes)

| Tool | Description | Data Source |
|------|-------------|-------------|
| `get_pathway_for_gene_set` | Biological pathways | KEGG, Reactome, BioPlanet via Enrichr |
| `get_enrichment_for_gene_set` | GO enrichment | g:Profiler |
| `get_interactions_for_gene_set` | Protein interactions | PubTator3 PPI API |
| `get_complex_for_gene_set` | Protein complexes | PubTator3 Complex API |

### Single Gene Tools

| Tool | Description | Data Source |
|------|-------------|-------------|
| `get_gene_summary_for_single_gene` | Gene function summary | NCBI Gene |
| `get_disease_for_single_gene` | Disease associations | PubTator |
| `get_domain_for_single_gene` | Protein domains | PubTator CDD |
| `get_pubmed_articles` | Literature evidence | PubMed |

## Input Format

Gene sets should be provided as comma-separated strings **without spaces**:

```python
# ✅ Correct
gene_set = "BRCA1,TP53,EGFR"

# ✅ Also correct (list format)
gene_set = ["BRCA1", "TP53", "EGFR"]

# ❌ Incorrect (spaces will be removed automatically, but avoid)
gene_set = "BRCA1, TP53, EGFR"
```

## Example Output

```
Process: MAPK Signaling Pathway

The proteins encoded by the genes ERBB2, ERBB4, FGFR2, FGFR4, HRAS, and KRAS 
are all integral components of the MAPK signaling pathway, which is crucial 
for cell growth, differentiation, and survival.

ERBB2 and ERBB4 are members of the epidermal growth factor receptor (EGFR) 
family of receptor tyrosine kinases (RTKs). ERBB2 is unique in that it has 
no known ligands, and it prefers to form heterodimers with other EGFR family 
members, enhancing their kinase activity. ERBB4 is activated by neuregulins 
and other factors and induces a variety of cellular responses including 
mitogenesis and differentiation.

FGFR2 and FGFR4 are part of the fibroblast growth factor receptor (FGFR) 
family of RTKs. They are activated by fibroblast growth factors, leading to 
receptor dimerization and autophosphorylation. This triggers downstream 
signaling pathways that regulate cellular processes such as proliferation, 
differentiation, and migration.

HRAS and KRAS are GTPases that act as molecular switches in RTK signaling. 
They are activated by guanine nucleotide exchange factors (GEFs) that catalyze 
the exchange of GDP for GTP. Once activated, RAS proteins can interact with a 
variety of effector proteins to propagate the signal downstream.
```

## Advanced Usage

### Access Verification Reports

```python
results = agent.go(gene_set, verbose=True)

# Full response includes verification reports
print(results.final_response)

# Access message history
for msg in results.message_history:
    print(f"{msg['role']}: {msg['content'][:100]}...")
```

### Use Tools Individually

```python
from biodsa.agents.geneagent import (
    GetPathwayForGeneSetTool,
    GetGeneSummaryForSingleGeneTool,
)

# Get pathways for a gene set
pathway_tool = GetPathwayForGeneSetTool()
pathways = pathway_tool._run(gene_set="BRCA1,TP53,EGFR")
print(pathways)

# Get summary for a single gene
summary_tool = GetGeneSummaryForSingleGeneTool()
summary = summary_tool._run(gene_name="BRCA1", specie="Homo")
print(summary)
```

## API Rate Limits

The tools query external APIs with various rate limits:

- **Enrichr:** Generally permissive
- **g:Profiler:** Generally permissive  
- **PubTator3 API:** ~3 requests/second recommended
- **NCBI E-utilities:** ~3 requests/second recommended

GeneAgent includes automatic rate limiting (0.5s delay between verification rounds).

## Comparison with Original GeneAgent

| Feature | Original | BioDSA Implementation |
|---------|----------|----------------------|
| API calls | Direct OpenAI SDK | LangChain (multi-provider) |
| Workflow | Imperative Python | LangGraph state machine |
| Tool calling | OpenAI Functions | LangChain Tools |
| State management | Ad-hoc variables | Pydantic models |
| Error handling | Basic try/catch | Retry with exponential backoff |
| Output | Text files | ExecutionResults object |

## Files

```
biodsa/agents/geneagent/
├── __init__.py    # Module exports
├── agent.py       # Main GeneAgent class with LangGraph workflow
├── state.py       # State definitions
├── prompt.py      # All prompt templates
├── tools.py       # LangChain tool wrappers
└── README.md      # This file
```

## Disclaimer

This tool shows the results of research conducted using the GeneAgent methodology. The information produced is not intended for direct diagnostic use or medical decision-making without review and oversight by a clinical or genomics professional.
