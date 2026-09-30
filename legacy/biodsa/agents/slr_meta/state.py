"""
State definitions for the SLR-Meta agent.

SLR-Meta conducts systematic literature review and meta-analysis by searching
both PubMed and ClinicalTrials.gov, then screening, extracting, and synthesizing
clinical evidence (including quantitative meta-analysis when appropriate).
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Annotated, Sequence
from langgraph.graph.message import add_messages, BaseMessage


# =============================================================================
# PICO and search
# =============================================================================

class PICOElements(BaseModel):
    """PICO (Population, Intervention, Comparison, Outcome) elements."""
    population: List[str] = Field(default_factory=list, description="Population/condition terms")
    intervention: List[str] = Field(default_factory=list, description="Intervention/treatment terms")
    comparison: List[str] = Field(default_factory=list, description="Comparator terms")
    outcomes: List[str] = Field(default_factory=list, description="Outcome terms")


class StudyReference(BaseModel):
    """A reference to a study from PubMed."""
    pmid: str = Field(description="PubMed ID")
    title: str = Field(default="", description="Study title")
    abstract: str = Field(default="", description="Study abstract")
    url: str = Field(default="", description="PubMed URL")
    source: str = Field(default="pubmed", description="Source: pubmed or ctgov")


class CTGovTrialReference(BaseModel):
    """A reference to a trial from ClinicalTrials.gov."""
    nct_id: str = Field(description="NCT ID")
    title: str = Field(default="", description="Brief title")
    conditions: str = Field(default="", description="Conditions")
    interventions: str = Field(default="", description="Interventions")
    brief_summary: str = Field(default="", description="Brief summary")
    url: str = Field(default="", description="ClinicalTrials.gov URL")
    study_status: str = Field(default="", description="Overall status")
    phase: str = Field(default="", description="Phase")
    enrollment: Optional[int] = Field(default=None, description="Enrollment count")
    source: str = Field(default="ctgov", description="Source identifier")


# =============================================================================
# Screening and extraction
# =============================================================================

class EligibilityCriterion(BaseModel):
    """A single eligibility criterion."""
    id: str = Field(description="Criterion ID")
    description: str = Field(description="Criterion description")
    category: str = Field(default="inclusion", description="inclusion or exclusion")


class ScreenedStudy(BaseModel):
    """A study/trial after screening."""
    identifier: str = Field(description="PMID or NCT ID")
    title: str = Field(default="", description="Title")
    abstract_or_summary: str = Field(default="", description="Abstract or brief summary")
    source: str = Field(default="pubmed", description="pubmed or ctgov")
    overall_eligibility: str = Field(default="include", description="include, exclude, uncertain")
    eligibility_score: float = Field(default=0.0, description="Eligibility score 0-1")
    exclusion_reasons: List[str] = Field(default_factory=list)


class StudyExtraction(BaseModel):
    """Extracted data from a single study/trial."""
    identifier: str = Field(description="PMID or NCT ID")
    title: str = Field(default="", description="Title")
    source: str = Field(default="pubmed", description="pubmed or ctgov")
    study_design: str = Field(default="", description="e.g. RCT, cohort")
    sample_size: Optional[int] = Field(default=None)
    population: str = Field(default="", description="Population description")
    intervention: str = Field(default="", description="Intervention")
    comparator: str = Field(default="", description="Comparator")
    primary_outcome: str = Field(default="", description="Primary outcome")
    efficacy_results: List[Dict[str, Any]] = Field(default_factory=list)
    safety_results: List[Dict[str, Any]] = Field(default_factory=list)
    follow_up: str = Field(default="", description="Follow-up duration")


# =============================================================================
# Meta-analysis and synthesis
# =============================================================================

class MetaAnalysisOutcome(BaseModel):
    """Quantitative meta-analysis result for one outcome."""
    outcome_name: str = Field(description="Outcome name")
    outcome_type: str = Field(default="efficacy", description="efficacy or safety")
    n_studies: int = Field(default=0, description="Number of studies included")
    pooled_estimate: Optional[float] = Field(default=None, description="Pooled effect (e.g. OR, RR, mean diff)")
    ci_lower: Optional[float] = Field(default=None, description="Lower 95% CI")
    ci_upper: Optional[float] = Field(default=None, description="Upper 95% CI")
    heterogeneity_i2: Optional[float] = Field(default=None, description="I² for heterogeneity")
    summary: str = Field(default="", description="Narrative summary")
    individual_effects: List[Dict[str, Any]] = Field(default_factory=list)


class EvidenceSynthesis(BaseModel):
    """Evidence synthesis and meta-analysis summary."""
    total_studies_included: int = Field(default=0)
    total_patients: int = Field(default=0)
    narrative_synthesis: str = Field(default="", description="Narrative synthesis text")
    meta_analysis_outcomes: List[MetaAnalysisOutcome] = Field(default_factory=list)
    quality_assessment: str = Field(default="", description="Quality/risk of bias summary")
    conclusions: str = Field(default="", description="Conclusions")
    limitations: List[str] = Field(default_factory=list)


# =============================================================================
# Main agent state
# =============================================================================

class SLRMetaAgentState(BaseModel):
    """State for the SLR-Meta agent workflow."""

    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Input
    research_question: str = Field(default="", description="Research question")
    target_outcomes: List[str] = Field(default_factory=list, description="Target outcomes")
    pico_elements: Optional[PICOElements] = Field(default=None)

    # Stage 1: Dual-source search
    search_queries_pubmed: List[str] = Field(default_factory=list, description="PubMed queries used")
    search_queries_ctgov: List[Dict[str, Any]] = Field(default_factory=list, description="CT.gov query params")
    identified_studies: List[StudyReference] = Field(default_factory=list, description="Studies from PubMed")
    ctgov_trials: List[CTGovTrialReference] = Field(default_factory=list, description="Trials from CT.gov")
    search_summary: str = Field(default="", description="Search stage summary")

    # Stage 2: Screening
    eligibility_criteria: List[EligibilityCriterion] = Field(default_factory=list)
    screened_studies: List[ScreenedStudy] = Field(default_factory=list)
    included_studies: List[ScreenedStudy] = Field(default_factory=list)
    excluded_studies: List[ScreenedStudy] = Field(default_factory=list)
    screening_summary: str = Field(default="")

    # Stage 3: Data extraction
    study_extractions: List[StudyExtraction] = Field(default_factory=list)
    extraction_summary: str = Field(default="")

    # Stage 4: Synthesis and meta-analysis
    evidence_synthesis: Optional[EvidenceSynthesis] = Field(default=None)
    synthesis_summary: str = Field(default="")
    final_report: str = Field(default="", description="Final SLR + meta-analysis report")

    # Workflow control
    workflow_stage: str = Field(default="search", description="search, screening, extraction, synthesis, completed")
    workflow_status: str = Field(default="initializing")
    total_input_tokens: int = Field(default=0)
    total_output_tokens: int = Field(default=0)
