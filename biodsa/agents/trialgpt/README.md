# TrialGPT Agent

An AI agent for matching patients to clinical trials based on the TrialGPT framework.

## Overview

The TrialGPT agent implements a two-stage workflow for patient-to-trial matching:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Patient Note  │────▶│   TrialGPT-     │────▶│   TrialGPT-     │────▶ Ranked Trials
│                 │     │   Retrieval     │     │   Matching      │     with Rationales
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Stage 1: Retrieval

- Extracts key clinical information from patient notes (demographics, diagnosis, biomarkers, treatments, etc.)
- Searches ClinicalTrials.gov for actively recruiting trials using multiple query strategies
- Filters and selects 10-30 candidate trials for detailed evaluation

### Stage 2: Matching/Ranking

- Retrieves full eligibility criteria for each candidate trial
- Systematically evaluates patient against inclusion/exclusion criteria
- Assigns eligibility scores and recommendations (ELIGIBLE, LIKELY_ELIGIBLE, UNCERTAIN, LIKELY_INELIGIBLE, INELIGIBLE)
- Produces a ranked list with detailed rationales

## Usage

```python
from biodsa.agents.trialgpt import TrialGPTAgent

# Initialize the agent
agent = TrialGPTAgent(
    model_name="gpt-4o",
    api_type="openai",  # or "azure", "anthropic", "google"
    api_key="your-api-key",
    endpoint="https://api.openai.com/v1"
)

# Define patient clinical note
patient_note = """
58-year-old African-American woman presents to the ER with episodic 
pressing/burning anterior chest pain that began two days earlier for 
the first time in her life.

Medical History:
- Stage IIIB non-small cell lung cancer (adenocarcinoma)
- EGFR mutation positive (exon 19 deletion)
- Previously treated with erlotinib for 14 months, now with disease progression
- ECOG Performance Status: 1
- No brain metastases
- No significant cardiac history

Labs:
- Creatinine: 0.9 mg/dL
- Platelets: 180,000/μL
- ANC: 3,500/μL
"""

# Run the agent
results = agent.go(patient_note)

# Access the results
print(results.final_response)      # Final ranked trials with rationales
print(results.message_history)     # Full conversation history
```

## Output

The `agent.go()` method returns an `ExecutionResults` object containing:

- `final_response`: The final ranked list of trials with detailed rationales
- `message_history`: Complete conversation history from both stages
- `sandbox`: None (this agent uses API tools, not code execution)
- `code_execution_results`: Empty list (no code execution)

The final response includes:

1. **Extracted Patient Profile**: Structured summary of patient's clinical information
2. **Search Strategy**: Queries used to find relevant trials
3. **Candidate Trials**: Initial list of potentially relevant trials
4. **Eligibility Assessments**: Detailed evaluation of each trial
5. **Ranked Recommendations**: Final ranked list with eligibility scores and clinical rationale

## Tools

The agent uses the following tools:

| Tool | Description |
|------|-------------|
| `clinical_trial_search` | Search ClinicalTrials.gov for trials matching conditions, interventions, mutations, etc. |
| `get_trial_details` | Fetch complete eligibility criteria and study details for specific NCT IDs |
| `evaluate_eligibility` | Structured framework for systematic eligibility assessment |

## Configuration

```python
agent = TrialGPTAgent(
    model_name="gpt-4o",           # LLM model to use
    api_type="openai",             # API provider
    api_key="...",                 # API key
    endpoint="...",                # API endpoint
    max_retrieval_rounds=5,        # Max tool calls in retrieval stage
    max_matching_rounds=10,        # Max tool calls in matching stage
)
```

## Architecture

```
TrialGPTAgent
├── Retrieval Stage (StateGraph)
│   ├── retrieval_agent_node
│   │   └── Uses: clinical_trial_search, get_trial_details
│   └── tool_node
│
├── Extract Summary Node
│
└── Matching Stage (StateGraph)
    ├── matching_agent_node
    │   └── Uses: get_trial_details, evaluate_eligibility
    └── tool_node
```

## State Schema

The agent maintains the following state:

- `patient_note`: Original clinical note
- `patient_info`: Extracted patient information
- `candidate_trials`: Retrieved candidate trials
- `match_results`: Detailed matching results
- `ranked_trials`: Final ranked recommendations
- `messages`: Conversation history

See `state.py` for complete schema definitions.

## Reference

This agent is based on the TrialGPT framework:

> Jin, Q., Wang, Z., Floudas, C.S., et al. (2024). Matching Patients to Clinical Trials with Large Language Models. Nature Communications.

### BibTeX

```bibtex
@article{jin2024matching,
  title={Matching Patients to Clinical Trials with Large Language Models},
  author={Jin, Qiao and Wang, Zifeng and Floudas, Charalampos S and Chen, Fangyuan and Gong, Changlin and Bracken-Clarke, Dara and Xue, Elisabetta and Yang, Yifan and Sun, Jimeng and Lu, Zhiyong},
  journal={Nature Communications},
  year={2024}
}
```
