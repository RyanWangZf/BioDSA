# SLR-Meta Agent

Systematic literature review and meta-analysis agent that searches **PubMed** and **ClinicalTrials.gov** to synthesize clinical evidence for a given research question.

## Overview

SLR-Meta conducts a 4-stage workflow:

1. **Dual-source literature search** — Queries PubMed (published literature) and ClinicalTrials.gov (registered trials) using PICO-based terms.
2. **Screening** — Applies eligibility criteria to titles/abstracts and trial summaries; classifies studies as include/exclude/uncertain.
3. **Data extraction** — Extracts structured data (design, population, intervention, outcomes, effect estimates) from included records.
4. **Evidence synthesis & meta-analysis** — Produces narrative synthesis and, when data allow, quantitative meta-analysis (pooled estimates, heterogeneity), then a final report.

## Usage

```python
import os
from biodsa.agents.slr_meta import SLRMetaAgent

agent = SLRMetaAgent(
    model_name="gpt-4o",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    max_search_results=20,   # PubMed
    max_ctgov_results=20,    # ClinicalTrials.gov
)

results = agent.go(
    research_question="What is the efficacy and safety of CAR-T cell therapy in relapsed/refractory B-cell lymphoma?",
    target_outcomes=["overall_response_rate", "complete_response", "overall_survival", "cytokine_release_syndrome"]
)

print(results.final_report)
# results.identified_pubmed, results.identified_ctgov, results.included_studies
```

## Tools

- **PubMed**: `pubmed_search`, `fetch_abstracts` (from TrialMind-SLR)
- **ClinicalTrials.gov**: `ctgov_search` (conditions, terms, interventions, phase, recruiting_status)
- **Screening**: `generate_eligibility_criteria`, `screen_study`
- **Extraction**: `extract_study_data`
- **Synthesis**: `synthesize_evidence`, `meta_analysis`, `generate_slr_report`

## Output

`agent.go()` returns `SLRMetaExecutionResults` with:

- `final_response` / `final_report`: Full SLR + meta-analysis report
- `identified_pubmed`: Number of studies from PubMed
- `identified_ctgov`: Number of trials from ClinicalTrials.gov
- `included_studies`: Number of studies/trials included after screening
- `message_history`: Full conversation trace

## Run script

From repo root:

```bash
python run_slr_meta.py
```

See `run_slr_meta.py` for required environment variables (e.g. `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`).
