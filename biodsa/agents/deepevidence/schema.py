# Map of knowledge base to tools
from typing import Literal
from biodsa.tool_wrappers.pubmed.tools import (
    FetchPaperAnnotationsTool,
    FindEntitiesTool,
    SearchPapersTool,
    GetPaperReferencesTool,
    FetchPaperContentTool,
    FindRelatedEntitiesTool
)
from biodsa.tool_wrappers.clinical_trials.tools import (
    SearchTrialsTool,
    FetchTrialDetailsTool,
)
from biodsa.tool_wrappers.biothings.tools import (
    SearchVariantsTool,
    FetchVariantDetailsTool,
)
from biodsa.tool_wrappers.websearch.tools import WebSearchTool

# Unified tools
from biodsa.agents.deepevidence.tool_wrappers.drugs.tools import (
    UnifiedDrugSearchTool,
    UnifiedDrugDetailsFetchTool,
)
from biodsa.agents.deepevidence.tool_wrappers.diseases.tools import (
    UnifiedDiseaseSearchTool,
    UnifiedDiseaseDetailsFetchTool,
)
from biodsa.agents.deepevidence.tool_wrappers.genes.tools import (
    UnifiedGeneSearchTool,
    UnifiedGeneDetailsFetchTool,
)
from biodsa.agents.deepevidence.tool_wrappers.targets.tools import (
    UnifiedTargetSearchTool,
    UnifiedTargetDetailsFetchTool,
)

__all__ = [
    "KNOWLEDGE_BASE_TO_TOOLS_MAP",
    "KnowledgeBase",
    "KNOWLEDGE_BASE_LIST",
]

# Define the literal type for knowledge bases
KnowledgeBase = Literal["pubmed_papers", "gene", "disease", "drug", "variant", "clinical_trials", "web_search", "target"]

# Keep the list for runtime validation and iteration
KNOWLEDGE_BASE_LIST = [
    "pubmed_papers",
    "gene",
    "disease",
    "drug",
    "variant",
    "clinical_trials",
    "web_search",
    "target"
]

KNOWLEDGE_BASE_TO_TOOLS_MAP = {
    "pubmed_papers": [
        FetchPaperAnnotationsTool, 
        FindEntitiesTool, 
        SearchPapersTool, 
        GetPaperReferencesTool, 
        FetchPaperContentTool, 
        FindRelatedEntitiesTool
        ],
    "clinical_trials": [SearchTrialsTool, FetchTrialDetailsTool],
    "disease": [UnifiedDiseaseSearchTool, UnifiedDiseaseDetailsFetchTool],
    "gene": [
        UnifiedGeneSearchTool,
        UnifiedGeneDetailsFetchTool
    ],
    "drug": [UnifiedDrugSearchTool, UnifiedDrugDetailsFetchTool],
    "target": [UnifiedTargetSearchTool, UnifiedTargetDetailsFetchTool],
    "variant": [SearchVariantsTool, FetchVariantDetailsTool],
    "web_search": [WebSearchTool],
}