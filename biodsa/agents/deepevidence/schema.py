# Map of knowledge base to tools
from typing import Literal
from biodsa.tools.pubmed.tools import (
    FetchPaperAnnotationsTool, 
    FindEntitiesTool, 
    SearchPapersTool, 
    GetPaperReferencesTool
)
from biodsa.tools.gene_set.tools import (
    GetPathwayForGeneSetTool,
    GetEnrichmentForGeneSetTool,
    GetInteractionsForGeneSetTool,
    GetComplexForGeneSetTool,
    GetGeneSummaryForSingleGeneTool,
    GetDiseaseForSingleGeneTool,
    GetDomainForSingleGeneTool,
)

__all__ = [
    "KNOWLEDGE_BASE_TO_TOOLS_MAP",
    "KnowledgeBase",
    "KNOWLEDGE_BASE_LIST",
]

# Define the literal type for knowledge bases
KnowledgeBase = Literal["pubmed_papers", "clinicaltrials"]

# Keep the list for runtime validation and iteration
KNOWLEDGE_BASE_LIST = [
    "pubmed_papers",
    "clinicaltrials",
    "gene_set",
]

KNOWLEDGE_BASE_TO_TOOLS_MAP = {
    "pubmed_papers": [FetchPaperAnnotationsTool(), FindEntitiesTool(), SearchPapersTool(), GetPaperReferencesTool()],
    "clinicaltrials": [],
    "gene_set": [GetPathwayForGeneSetTool(), GetEnrichmentForGeneSetTool(), GetInteractionsForGeneSetTool(), GetComplexForGeneSetTool(), GetGeneSummaryForSingleGeneTool(), GetDiseaseForSingleGeneTool(), GetDomainForSingleGeneTool()],
}