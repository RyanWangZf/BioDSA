"""
TrialGPT Agent for patient-to-clinical-trial matching.

Based on the TrialGPT framework:
Jin, Q., et al. (2024). Matching patients to clinical trials with large language models.
Nature Communications.

This module provides an AI agent that:
1. Extracts key clinical information from patient notes
2. Searches ClinicalTrials.gov for actively recruiting trials
3. Evaluates patient eligibility against trial criteria
4. Produces a ranked list of suitable trials with rationales

Example usage:
    ```python
    from biodsa.agents.trialgpt import TrialGPTAgent
    
    agent = TrialGPTAgent(
        model_name="gpt-4o",
        api_type="openai",
        api_key="your-api-key",
        endpoint="https://api.openai.com/v1"
    )
    
    patient_note = '''
    58-year-old female with metastatic non-small cell lung cancer.
    EGFR mutation positive. Previously treated with erlotinib with progression.
    ECOG PS 1. No brain metastases.
    '''
    
    results = agent.go(patient_note)
    print(results.final_response)
    ```
"""

from biodsa.agents.trialgpt.agent import TrialGPTAgent
from biodsa.agents.trialgpt.state import (
    TrialGPTAgentState,
    PatientInfo,
    TrialCandidate,
    TrialMatchResult,
    RankedTrial,
)
from biodsa.agents.trialgpt.tools import (
    ClinicalTrialSearchTool,
    TrialDetailsTool,
    PatientTrialMatchTool,
    get_trialgpt_tools,
)

__all__ = [
    # Main agent
    "TrialGPTAgent",
    # State classes
    "TrialGPTAgentState",
    "PatientInfo",
    "TrialCandidate",
    "TrialMatchResult",
    "RankedTrial",
    # Tools
    "ClinicalTrialSearchTool",
    "TrialDetailsTool",
    "PatientTrialMatchTool",
    "get_trialgpt_tools",
]
