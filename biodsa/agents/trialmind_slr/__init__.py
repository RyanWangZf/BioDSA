"""
TrialMind-SLR: Systematic Literature Review Agent

A 4-stage workflow agent for conducting systematic literature reviews:
1. Literature Search - PICO-based PubMed search
2. Literature Screening - Eligibility criteria and study screening
3. Data Extraction - Structured data extraction from studies
4. Evidence Synthesis - Aggregation and report generation

Example:
    >>> from biodsa.agents.trialmind_slr import TrialMindSLRAgent
    >>> 
    >>> agent = TrialMindSLRAgent(
    ...     model_name="gpt-4o",
    ...     api_type="azure",
    ...     api_key="your-key",
    ...     endpoint="your-endpoint"
    ... )
    >>> 
    >>> results = agent.go(
    ...     research_question="What is the efficacy of CAR-T in lymphoma?",
    ...     target_outcomes=["overall_response", "complete_response"]
    ... )
    >>> 
    >>> print(results.final_report)
"""

from biodsa.agents.trialmind_slr.agent import (
    TrialMindSLRAgent,
    TrialMindSLRExecutionResults,
)
from biodsa.agents.trialmind_slr.state import (
    TrialMindSLRAgentState,
    PICOElements,
    SearchQuery,
    StudyReference,
    EligibilityCriterion,
    ScreenedStudy,
    StudyExtraction,
    EvidenceSynthesis,
)
from biodsa.agents.trialmind_slr.tools import (
    PubMedSearchTool,
    FetchAbstractsTool,
    GenerateCriteriaTool,
    ScreenStudyTool,
    ExtractDataTool,
    SynthesizeEvidenceTool,
    GenerateSLRReportTool,
    get_all_trialmind_slr_tools,
)

__all__ = [
    # Main agent
    "TrialMindSLRAgent",
    "TrialMindSLRExecutionResults",
    # State
    "TrialMindSLRAgentState",
    "PICOElements",
    "SearchQuery",
    "StudyReference",
    "EligibilityCriterion",
    "ScreenedStudy",
    "StudyExtraction",
    "EvidenceSynthesis",
    # Tools
    "PubMedSearchTool",
    "FetchAbstractsTool",
    "GenerateCriteriaTool",
    "ScreenStudyTool",
    "ExtractDataTool",
    "SynthesizeEvidenceTool",
    "GenerateSLRReportTool",
    "get_all_trialmind_slr_tools",
]
