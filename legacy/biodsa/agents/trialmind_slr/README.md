# TrialMind-SLR Agent

A systematic literature review (SLR) agent that implements a 4-stage workflow for conducting comprehensive literature reviews in biomedical research.

## Overview

TrialMind-SLR automates the systematic literature review process through four sequential stages:

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│  1. Literature      │     │  2. Literature      │     │  3. Data            │     │  4. Evidence        │
│     Search          │────▶│     Screening       │────▶│     Extraction      │────▶│     Synthesis       │
│                     │     │                     │     │                     │     │                     │
│  • PICO extraction  │     │  • Eligibility      │     │  • Study chars      │     │  • Aggregate        │
│  • Query generation │     │    criteria         │     │  • Outcomes         │     │  • Quality assess   │
│  • PubMed search    │     │  • Study screening  │     │  • Safety data      │     │  • Generate report  │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘     └─────────────────────┘
```

## Features

- **PICO-based Search**: Automatically extracts Population, Intervention, Comparison, and Outcome elements from research questions
- **PubMed Integration**: Searches PubMed/MEDLINE for relevant literature
- **Automated Screening**: Generates eligibility criteria and screens studies systematically
- **Structured Data Extraction**: Extracts key data points from included studies
- **Evidence Synthesis**: Aggregates findings and generates comprehensive SLR reports

## Installation

The agent is part of the BioDSA package. Ensure you have the required dependencies:

```bash
pip install biopython  # For PubMed access
```

## Usage

### Basic Example

```python
from biodsa.agents.trialmind_slr import TrialMindSLRAgent

# Initialize the agent
agent = TrialMindSLRAgent(
    model_name="gpt-4o",
    api_type="azure",
    api_key="your-api-key",
    endpoint="your-endpoint"
)

# Run the SLR
result = agent.go(
    research_question="What is the efficacy of CAR-T cell therapy in relapsed/refractory lymphoma?",
    target_outcomes=["overall_response", "complete_response", "overall_survival"]
)

# Access results
print(result.final_report)
print(f"Studies included: {result.included_studies}")
```

### With PICO Elements

```python
result = agent.go(
    research_question="Efficacy of immunotherapy in melanoma",
    target_outcomes=["overall_survival", "progression_free_survival"],
    pico_elements={
        "population": ["advanced melanoma", "metastatic melanoma"],
        "intervention": ["checkpoint inhibitor", "pembrolizumab", "nivolumab"],
        "comparison": ["chemotherapy", "ipilimumab"],
        "outcomes": ["overall survival", "response rate"]
    }
)
```

### Command Line

```bash
python run_trialmindslr.py
```

## Workflow Stages

### Stage 1: Literature Search

- Analyzes the research question to extract PICO elements
- Generates optimized PubMed search queries
- Retrieves potentially relevant studies from PubMed

**Tools used:**
- `pubmed_search`: Search PubMed with Boolean queries
- `fetch_abstracts`: Retrieve full abstracts for PMIDs

### Stage 2: Literature Screening

- Generates eligibility criteria based on PICO elements
- Screens each study against inclusion/exclusion criteria
- Classifies studies as Include, Exclude, or Uncertain

**Tools used:**
- `generate_eligibility_criteria`: Create screening criteria
- `screen_study`: Evaluate study against criteria

### Stage 3: Data Extraction

- Extracts structured data from included studies
- Captures study design, population, interventions, outcomes
- Notes data quality and missing information

**Tools used:**
- `extract_study_data`: Extract data fields from abstracts

### Stage 4: Evidence Synthesis

- Aggregates findings across all included studies
- Assesses quality of evidence
- Generates final SLR report following PRISMA guidelines

**Tools used:**
- `synthesize_evidence`: Aggregate findings by outcome
- `generate_slr_report`: Produce final report

## Output

The agent produces:

1. **PRISMA Flow Summary**: Study counts at each stage
2. **Study Characteristics Table**: Summary of included studies
3. **Evidence Synthesis**: Aggregated findings by outcome
4. **Final Report**: Markdown-formatted SLR report

### Accessing Results

```python
result = agent.go(research_question="...")

# PRISMA numbers
prisma = result.get_prisma_summary()
print(f"Identified: {prisma['identified']}")
print(f"Included: {prisma['included']}")

# Full report
print(result.final_report)

# Token usage
print(f"Tokens used: {result.total_input_tokens + result.total_output_tokens}")
```

## Configuration

```python
agent = TrialMindSLRAgent(
    model_name="gpt-4o",            # LLM model
    api_type="azure",               # API provider
    api_key="...",                  # API key
    endpoint="...",                 # API endpoint
    max_search_results=50,          # Max papers from PubMed search (default: 50)
    max_studies_to_screen=100,      # Max studies to screen (default: 100)
    max_studies_to_include=50,      # Max studies to include (default: 50)
    llm_timeout=120,                # Timeout in seconds
)
```

### Quick Demo Mode

For quick demos with reduced token usage and runtime, set `max_search_results` to a low value:

```python
agent = TrialMindSLRAgent(
    model_name="gpt-4o",
    api_type="azure",
    api_key="...",
    endpoint="...",
    max_search_results=10,          # Only retrieve 10 papers for quick demo
)
```

## Limitations

- Currently uses PubMed only (EMBASE, Cochrane not yet supported)
- Abstract-level screening (full-text not yet supported)
- Mock data used when PubMed API is unavailable
- Quantitative meta-analysis not yet implemented

## References

Based on the TrialMind framework for accelerating clinical evidence synthesis:

```bibtex
@article{wang2024accelerating,
  title={Accelerating Clinical Evidence Synthesis with Large Language Models},
  author={Wang, Zifeng and Cao, Lang and Danek, Benjamin and Jin, Qiao and Lu, Zhiyong and Sun, Jimeng},
  journal={npj Digital Medicine},
  year={2025}
}
```

Additional references:

- Moher D, et al. Preferred reporting items for systematic reviews and meta-analyses: the PRISMA statement. BMJ. 2009
- Cochrane Handbook for Systematic Reviews of Interventions
