"""
GeneAgent: Self-verification Language Agent for Gene Set Analysis

GeneAgent is a language agent that autonomously interacts with domain-specific
databases to annotate functions for gene sets. It implements a cascade 
self-verification mechanism to reduce hallucination and provide evidence-based
insights into gene function.

Based on:
@article{jin2024geneagent,
  title={GeneAgent: Self-verification Language Agent for Gene Set Analysis using Domain Databases},
  author={Jin, Qiao and others},
  year={2024}
}

Reference: https://github.com/ncbi-nlp/GeneAgent

Example usage:
    ```python
    from biodsa.agents.geneagent import GeneAgent
    
    agent = GeneAgent(
        model_name="gpt-4o",
        api_type="azure",
        api_key="your-api-key",
        endpoint="your-endpoint"
    )
    
    gene_set = "ERBB2,ERBB4,FGFR2,FGFR4,HRAS,KRAS"
    
    results = agent.go(gene_set)
    print(results.final_response)
    ```
"""

from biodsa.agents.geneagent.agent import GeneAgent
from biodsa.agents.geneagent.state import (
    GeneAgentState,
    VerificationWorkerState,
    GeneSetAnalysis,
    VerificationClaim,
    VerificationReport,
)
from biodsa.agents.geneagent.tools import (
    GetPathwayForGeneSetTool,
    GetEnrichmentForGeneSetTool,
    GetInteractionsForGeneSetTool,
    GetComplexForGeneSetTool,
    GetGeneSummaryForSingleGeneTool,
    GetDiseaseForSingleGeneTool,
    GetDomainForSingleGeneTool,
    GetPubMedArticlesTool,
    get_geneagent_tools,
    get_gene_set_tools,
    get_single_gene_tools,
)

__all__ = [
    # Main agent
    "GeneAgent",
    # State classes
    "GeneAgentState",
    "VerificationWorkerState",
    "GeneSetAnalysis",
    "VerificationClaim",
    "VerificationReport",
    # Tools
    "GetPathwayForGeneSetTool",
    "GetEnrichmentForGeneSetTool",
    "GetInteractionsForGeneSetTool",
    "GetComplexForGeneSetTool",
    "GetGeneSummaryForSingleGeneTool",
    "GetDiseaseForSingleGeneTool",
    "GetDomainForSingleGeneTool",
    "GetPubMedArticlesTool",
    "get_geneagent_tools",
    "get_gene_set_tools",
    "get_single_gene_tools",
]
