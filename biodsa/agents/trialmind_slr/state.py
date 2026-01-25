"""
State definitions for the TrialMind-SLR agent.

TrialMind-SLR is a systematic literature review agent that implements
a 4-stage workflow:
1. Literature Search - PICO-based PubMed search
2. Literature Screening - Eligibility criteria generation and prediction
3. Data Extraction - Extract relevant data from included studies
4. Evidence Synthesis - Aggregate and summarize findings
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Annotated, Sequence
from langgraph.graph.message import add_messages, BaseMessage


# =============================================================================
# PICO Components
# =============================================================================

class PICOElements(BaseModel):
    """PICO (Population, Intervention, Comparison, Outcome) elements."""
    population: List[str] = Field(
        default_factory=list,
        description="Population/condition terms (e.g., 'Lymphoma', 'Multiple Myeloma')"
    )
    intervention: List[str] = Field(
        default_factory=list,
        description="Intervention/treatment terms (e.g., 'CAR-T', 'Immunotherapy')"
    )
    comparison: List[str] = Field(
        default_factory=list,
        description="Comparator treatments (e.g., 'chemotherapy', 'standard care')"
    )
    outcomes: List[str] = Field(
        default_factory=list,
        description="Outcome terms (e.g., 'overall survival', 'complete response')"
    )


class SearchQuery(BaseModel):
    """A structured search query for PubMed."""
    query_string: str = Field(description="The complete PubMed search query string")
    description: str = Field(default="", description="Description of what this query targets")
    source: str = Field(default="generated", description="Source: 'generated' or 'user_provided'")


# =============================================================================
# Study and Literature Data
# =============================================================================

class StudyReference(BaseModel):
    """A reference to a study found in literature search."""
    pmid: str = Field(description="PubMed ID")
    title: str = Field(description="Study title")
    authors: str = Field(default="", description="Authors list")
    journal: str = Field(default="", description="Journal name")
    year: str = Field(default="", description="Publication year")
    abstract: str = Field(default="", description="Study abstract")
    doi: str = Field(default="", description="DOI if available")
    url: str = Field(default="", description="PubMed URL")


class EligibilityCriterion(BaseModel):
    """A single eligibility criterion for screening."""
    id: str = Field(description="Unique criterion ID (e.g., 'C1', 'C2')")
    description: str = Field(description="The criterion description")
    category: str = Field(
        default="inclusion",
        description="Category: 'inclusion' or 'exclusion'"
    )
    priority: str = Field(
        default="required",
        description="Priority: 'required' or 'preferred'"
    )


class EligibilityPrediction(BaseModel):
    """Eligibility prediction for a study against a single criterion."""
    criterion_id: str = Field(description="The criterion ID")
    prediction: str = Field(
        description="Prediction: 'eligible', 'not_eligible', or 'uncertain'"
    )
    confidence: float = Field(
        default=0.0,
        description="Confidence score (0-1)"
    )
    rationale: str = Field(default="", description="Rationale for the prediction")
    evidence: str = Field(default="", description="Evidence from the study supporting the prediction")


class ScreenedStudy(BaseModel):
    """A study with eligibility screening results."""
    pmid: str = Field(description="PubMed ID")
    title: str = Field(description="Study title")
    abstract: str = Field(default="", description="Study abstract")
    predictions: List[EligibilityPrediction] = Field(
        default_factory=list,
        description="Eligibility predictions for each criterion"
    )
    overall_eligibility: str = Field(
        default="uncertain",
        description="Overall eligibility: 'include', 'exclude', or 'uncertain'"
    )
    eligibility_score: float = Field(
        default=0.0,
        description="Aggregated eligibility score (0-1)"
    )
    exclusion_reasons: List[str] = Field(
        default_factory=list,
        description="Reasons for exclusion if applicable"
    )
    rank: int = Field(default=0, description="Ranking among included studies")


# =============================================================================
# Data Extraction
# =============================================================================

class ExtractedField(BaseModel):
    """A single extracted data field from a study."""
    name: str = Field(description="Field name (e.g., 'sample_size', 'treatment_duration')")
    value: Any = Field(description="Extracted value")
    unit: str = Field(default="", description="Unit if applicable")
    source_text: str = Field(default="", description="Source text from the study")
    confidence: float = Field(default=1.0, description="Extraction confidence (0-1)")


class StudyExtraction(BaseModel):
    """Extracted data from a single study."""
    pmid: str = Field(description="PubMed ID")
    title: str = Field(description="Study title")
    study_design: str = Field(default="", description="Study design (e.g., 'RCT', 'cohort')")
    sample_size: Optional[int] = Field(default=None, description="Total sample size")
    population: str = Field(default="", description="Population description")
    intervention: str = Field(default="", description="Intervention description")
    comparator: str = Field(default="", description="Comparator description")
    follow_up: str = Field(default="", description="Follow-up duration")
    primary_outcome: str = Field(default="", description="Primary outcome")
    extracted_fields: List[ExtractedField] = Field(
        default_factory=list,
        description="All extracted data fields"
    )
    quality_score: float = Field(default=0.0, description="Study quality score")


# =============================================================================
# Evidence Synthesis
# =============================================================================

class OutcomeResult(BaseModel):
    """Result for a specific outcome across studies."""
    outcome_name: str = Field(description="Name of the outcome")
    outcome_type: str = Field(default="efficacy", description="Type: 'efficacy' or 'safety'")
    studies_reporting: int = Field(default=0, description="Number of studies reporting this outcome")
    pooled_estimate: Optional[float] = Field(default=None, description="Pooled effect estimate")
    pooled_ci_lower: Optional[float] = Field(default=None, description="Lower CI bound")
    pooled_ci_upper: Optional[float] = Field(default=None, description="Upper CI bound")
    heterogeneity: str = Field(default="", description="Heterogeneity assessment")
    summary: str = Field(default="", description="Narrative summary of findings")
    individual_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Results from individual studies"
    )


class EvidenceSynthesis(BaseModel):
    """Complete evidence synthesis results."""
    total_studies_included: int = Field(default=0, description="Total studies included")
    total_patients: int = Field(default=0, description="Total patients across studies")
    study_designs: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of study designs"
    )
    efficacy_outcomes: List[OutcomeResult] = Field(
        default_factory=list,
        description="Efficacy outcome results"
    )
    safety_outcomes: List[OutcomeResult] = Field(
        default_factory=list,
        description="Safety outcome results"
    )
    subgroup_analyses: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Subgroup analysis results"
    )
    quality_assessment: str = Field(
        default="",
        description="Overall quality assessment summary"
    )
    conclusions: str = Field(default="", description="Main conclusions")
    limitations: List[str] = Field(
        default_factory=list,
        description="Limitations of the review"
    )


# =============================================================================
# Main Agent State
# =============================================================================

class TrialMindSLRAgentState(BaseModel):
    """Main state for the TrialMind-SLR agent workflow."""
    
    # Message history
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # ==========================================================================
    # Input Configuration
    # ==========================================================================
    
    # Research question
    research_question: str = Field(
        default="",
        description="The research question guiding the SLR"
    )
    
    # PICO elements (can be provided or auto-generated)
    pico_elements: Optional[PICOElements] = Field(
        default=None,
        description="PICO elements for the review"
    )
    
    # User-provided eligibility criteria (optional)
    user_eligibility_criteria: List[Dict[str, str]] = Field(
        default_factory=list,
        description="User-provided eligibility criteria"
    )
    
    # Target outcomes to extract
    target_outcomes: List[str] = Field(
        default_factory=list,
        description="Target outcomes to extract and synthesize"
    )
    
    # ==========================================================================
    # Stage 1: Literature Search
    # ==========================================================================
    
    search_queries: List[SearchQuery] = Field(
        default_factory=list,
        description="Generated or provided search queries"
    )
    
    identified_studies: List[StudyReference] = Field(
        default_factory=list,
        description="Studies identified from search"
    )
    
    total_studies_found: int = Field(
        default=0,
        description="Total number of studies found"
    )
    
    search_summary: str = Field(
        default="",
        description="Summary of the literature search"
    )
    
    # ==========================================================================
    # Stage 2: Literature Screening
    # ==========================================================================
    
    eligibility_criteria: List[EligibilityCriterion] = Field(
        default_factory=list,
        description="Eligibility criteria for screening"
    )
    
    screened_studies: List[ScreenedStudy] = Field(
        default_factory=list,
        description="Studies after screening with eligibility predictions"
    )
    
    included_studies: List[ScreenedStudy] = Field(
        default_factory=list,
        description="Studies included after screening"
    )
    
    excluded_studies: List[ScreenedStudy] = Field(
        default_factory=list,
        description="Studies excluded with reasons"
    )
    
    screening_summary: str = Field(
        default="",
        description="Summary of the screening process"
    )
    
    # ==========================================================================
    # Stage 3: Data Extraction
    # ==========================================================================
    
    extraction_template: List[str] = Field(
        default_factory=list,
        description="Fields to extract from each study"
    )
    
    study_extractions: List[StudyExtraction] = Field(
        default_factory=list,
        description="Extracted data from included studies"
    )
    
    extraction_summary: str = Field(
        default="",
        description="Summary of data extraction"
    )
    
    # ==========================================================================
    # Stage 4: Evidence Synthesis
    # ==========================================================================
    
    evidence_synthesis: Optional[EvidenceSynthesis] = Field(
        default=None,
        description="Evidence synthesis results"
    )
    
    synthesis_summary: str = Field(
        default="",
        description="Narrative synthesis summary"
    )
    
    # ==========================================================================
    # Final Output
    # ==========================================================================
    
    final_report: str = Field(
        default="",
        description="The final SLR report"
    )
    
    # ==========================================================================
    # Workflow Control
    # ==========================================================================
    
    workflow_stage: str = Field(
        default="search",
        description="Current stage: 'search', 'screening', 'extraction', 'synthesis', 'completed'"
    )
    
    workflow_status: str = Field(
        default="initializing",
        description="Status within current stage"
    )
    
    # ==========================================================================
    # Token Tracking
    # ==========================================================================
    
    total_input_tokens: int = Field(default=0, description="Total input tokens used")
    total_output_tokens: int = Field(default=0, description="Total output tokens used")
