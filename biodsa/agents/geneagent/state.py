"""
State definitions for the GeneAgent.

GeneAgent is a self-verification language agent for gene set analysis that 
autonomously interacts with domain-specific databases to verify and refine
its analysis of gene sets.

Based on:
@article{jin2024geneagent,
  title={GeneAgent: Self-verification Language Agent for Gene Set Analysis using Domain Databases},
  author={Jin, Qiao and others},
  year={2024}
}

Reference: https://github.com/ncbi-nlp/GeneAgent
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Annotated, Sequence, Literal
from langgraph.graph.message import add_messages, BaseMessage


class VerificationClaim(BaseModel):
    """A claim to be verified against domain databases."""
    claim: str = Field(description="The claim text to verify")
    verified: bool = Field(default=False, description="Whether the claim has been verified")
    verification_result: str = Field(default="", description="The verification result/evidence")
    supported: Optional[bool] = Field(default=None, description="Whether the claim is supported by evidence")


class GeneSetAnalysis(BaseModel):
    """Initial analysis result for a gene set."""
    process_name: str = Field(default="", description="The proposed biological process name")
    summary: str = Field(default="", description="The full analysis summary")
    raw_response: str = Field(default="", description="Raw LLM response")


class VerificationReport(BaseModel):
    """Report from verifying claims against databases."""
    claims: List[VerificationClaim] = Field(
        default_factory=list,
        description="List of claims and their verification results"
    )
    summary: str = Field(default="", description="Summary of verification findings")
    

class GeneAgentState(BaseModel):
    """State for the GeneAgent gene set analysis workflow.
    
    The workflow follows the cascade verification approach:
    1. Generate initial analysis (process name + summary)
    2. Generate and verify topic claims (about the process name)
    3. Update process name based on verification
    4. Generate and verify analysis claims (about gene functions)
    5. Generate final refined summary
    """
    
    # Message history for LangGraph
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Input
    gene_set: str = Field(default="", description="Comma-separated gene names (e.g., 'BRCA1,TP53,EGFR')")
    gene_list: List[str] = Field(default_factory=list, description="Parsed list of gene names")
    
    # Stage 1: Initial Analysis
    initial_analysis: Optional[GeneSetAnalysis] = Field(
        default=None,
        description="Initial process name and summary from first LLM call"
    )
    
    # Stage 2: Topic Verification (verify process name)
    topic_claims: List[str] = Field(
        default_factory=list,
        description="Claims about the process name to verify"
    )
    topic_verification_report: str = Field(
        default="",
        description="Compiled verification results for topic claims"
    )
    updated_process_name: str = Field(
        default="",
        description="Process name after topic verification"
    )
    updated_summary: str = Field(
        default="",
        description="Summary after topic verification"
    )
    
    # Stage 3: Analysis Verification (verify gene analysis)
    analysis_claims: List[str] = Field(
        default_factory=list,
        description="Claims about gene functions to verify"
    )
    analysis_verification_report: str = Field(
        default="",
        description="Compiled verification results for analysis claims"
    )
    
    # Stage 4: Final Output
    final_process_name: str = Field(
        default="",
        description="Final refined process name"
    )
    final_summary: str = Field(
        default="",
        description="Final refined analysis summary"
    )
    
    # Verification tracking
    current_claim_index: int = Field(
        default=0,
        description="Index of current claim being verified"
    )
    verification_stage: Literal["topic", "analysis", "complete"] = Field(
        default="topic",
        description="Current verification stage"
    )
    
    # Metadata
    model_name: str = Field(default="", description="LLM model used")
    total_claims_verified: int = Field(default=0, description="Total claims verified")
    total_api_calls: int = Field(default=0, description="Total API calls made for verification")


class VerificationWorkerState(BaseModel):
    """State for the verification worker sub-agent.
    
    The worker verifies a single claim by calling domain database tools
    and compiling evidence.
    """
    
    # Message history
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Input
    claim: str = Field(default="", description="The claim to verify")
    gene_set: str = Field(default="", description="The gene set context")
    
    # Output
    verification_result: str = Field(default="", description="The verification report")
    is_complete: bool = Field(default=False, description="Whether verification is complete")
    loop_count: int = Field(default=0, description="Number of verification loops")
    max_loops: int = Field(default=20, description="Maximum verification loops")
