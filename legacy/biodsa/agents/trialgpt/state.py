"""
State definitions for the TrialGPT agent.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Annotated, Sequence
from langgraph.graph.message import add_messages, BaseMessage


class PatientInfo(BaseModel):
    """Extracted patient information from clinical notes."""
    age: Optional[int] = Field(default=None, description="Patient age in years")
    sex: Optional[str] = Field(default=None, description="Patient sex (Male/Female)")
    conditions: List[str] = Field(default_factory=list, description="List of diagnosed conditions/diseases")
    interventions: List[str] = Field(default_factory=list, description="Current or prior treatments/interventions")
    biomarkers: Dict[str, str] = Field(default_factory=dict, description="Biomarker status (e.g., {'EGFR': 'positive'})")
    mutations: List[str] = Field(default_factory=list, description="Known genetic mutations")
    prior_therapies: List[str] = Field(default_factory=list, description="Prior lines of therapy")
    comorbidities: List[str] = Field(default_factory=list, description="Comorbid conditions")
    ecog_status: Optional[int] = Field(default=None, description="ECOG performance status (0-5)")
    lab_values: Dict[str, str] = Field(default_factory=dict, description="Key laboratory values")
    raw_note: str = Field(default="", description="Original patient note")


class TrialCandidate(BaseModel):
    """A candidate clinical trial with basic information."""
    nct_id: str = Field(description="NCT identifier")
    title: str = Field(description="Study title")
    conditions: str = Field(description="Target conditions")
    interventions: str = Field(description="Interventions being studied")
    phase: str = Field(default="", description="Trial phase")
    status: str = Field(default="", description="Recruitment status")
    eligibility_criteria: str = Field(default="", description="Full eligibility criteria text")
    brief_summary: str = Field(default="", description="Brief study summary")
    locations: str = Field(default="", description="Study locations")
    url: str = Field(default="", description="ClinicalTrials.gov URL")


class TrialMatchResult(BaseModel):
    """Result of matching a patient to a specific trial."""
    nct_id: str = Field(description="NCT identifier")
    title: str = Field(description="Study title")
    eligibility_score: float = Field(description="Eligibility score (0-1, higher is better match)")
    inclusion_matches: List[str] = Field(default_factory=list, description="Matched inclusion criteria")
    inclusion_concerns: List[str] = Field(default_factory=list, description="Inclusion criteria concerns")
    exclusion_flags: List[str] = Field(default_factory=list, description="Potential exclusion criteria violations")
    rationale: str = Field(description="Detailed rationale for the eligibility assessment")
    recommendation: str = Field(description="ELIGIBLE, LIKELY_ELIGIBLE, UNCERTAIN, LIKELY_INELIGIBLE, or INELIGIBLE")


class RankedTrial(BaseModel):
    """A trial with final ranking information."""
    rank: int = Field(description="Ranking position (1 is best)")
    nct_id: str = Field(description="NCT identifier")
    title: str = Field(description="Study title")
    eligibility_score: float = Field(description="Eligibility score")
    relevance_score: float = Field(description="Disease/treatment relevance score")
    overall_score: float = Field(description="Combined overall score")
    recommendation: str = Field(description="Eligibility recommendation")
    summary_rationale: str = Field(description="Brief summary of why this trial is ranked here")
    url: str = Field(default="", description="ClinicalTrials.gov URL")


class TrialGPTAgentState(BaseModel):
    """State for the TrialGPT agent workflow."""
    
    # Message history
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Input
    patient_note: str = Field(default="", description="Original patient clinical note")
    
    # Stage 1: Retrieval outputs
    patient_info: Optional[PatientInfo] = Field(default=None, description="Extracted patient information")
    search_queries: List[str] = Field(default_factory=list, description="Generated search queries for trial retrieval")
    candidate_trials: List[TrialCandidate] = Field(default_factory=list, description="Retrieved candidate trials")
    retrieval_summary: str = Field(default="", description="Summary of the retrieval stage")
    
    # Stage 2: Matching/Ranking outputs
    match_results: List[TrialMatchResult] = Field(default_factory=list, description="Detailed matching results for each trial")
    ranked_trials: List[RankedTrial] = Field(default_factory=list, description="Final ranked list of trials")
    ranking_summary: str = Field(default="", description="Summary of the ranking rationale")
    
    # Metadata
    total_trials_searched: int = Field(default=0, description="Total number of trials searched")
    total_trials_retrieved: int = Field(default=0, description="Number of trials after initial retrieval")
    total_trials_ranked: int = Field(default=0, description="Number of trials in final ranking")
