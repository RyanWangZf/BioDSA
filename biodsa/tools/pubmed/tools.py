from typing import Literal, List, Dict, Any, Type, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import pandas as pd
import json

from biodsa.tools.pubmed.pubmed_api import pubmed_api_get_paper_references
from biodsa.tools.pubmed.pubtator_api import (
    pubtator_api_fetch_paper_annotations,
    pubtator_api_find_entities,
    pubtator_api_search_papers,
)
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper

__all__ = [
    "GetPaperReferencesTool",
    "FetchPaperAnnotationsTool",
    "FindEntitiesTool",
    "SearchPapersTool",
    "GetPaperReferencesToolInput",
    "FetchPaperAnnotationsToolInput",
    "FindEntitiesToolInput",
    "SearchPapersToolInput",
]

# =====================================================
# Tool 1: Get Paper References
# =====================================================
class GetPaperReferencesToolInput(BaseModel):
    """Input schema for GetPaperReferencesTool."""
    pmids: List[str] = Field(
        ..., 
        description="List of PubMed IDs (PMIDs) to get references for."
    )
    batch_size: int = Field(
        default=100,
        description="Number of PMIDs to process in each main batch."
    )
    mini_batch_size: int = Field(
        default=20,
        description="Size of each sub-batch for threading."
    )
    max_workers: int = Field(
        default=4,
        description="Number of threads for concurrent processing."
    )
    rate_limit: float = Field(
        default=3.0,
        description="Maximum requests per second."
    )


class GetPaperReferencesTool(BaseTool):
    """
    Tool to get paper references (citation relations) for a list of PMIDs.
    
    This tool retrieves articles that the input papers cite, returning citation 
    relations with source and target PMIDs. Uses multi-threaded processing for efficiency.
    """
    name: str = "get_paper_references"
    description: str = (
        "Get paper references (citations) for a list of PubMed IDs. "
        "Returns citation relations showing which papers the input papers cite. "
        "Useful for finding related work and building citation networks."
    )
    args_schema: Type[BaseModel] = GetPaperReferencesToolInput
    sandbox: ExecutionSandboxWrapper = None
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox

    def _run(
        self,
        pmids: List[str],
        batch_size: int = 100,
        mini_batch_size: int = 20,
        max_workers: int = 4,
        rate_limit: float = 3.0
    ) -> List[Dict[str, Any]]:
        """Execute the tool to get paper references."""
        search_results = pubmed_api_get_paper_references(
            pmids=pmids,
            batch_size=batch_size,
            mini_batch_size=mini_batch_size,
            max_workers=max_workers,
            rate_limit=rate_limit
        )
        search_results_str = json.dumps(search_results, indent=4)
        return search_results_str


# =====================================================
# Tool 2: Fetch Paper Annotations
# =====================================================
class FetchPaperAnnotationsToolInput(BaseModel):
    """Input schema for FetchPaperAnnotationsTool."""
    pmids: List[str] = Field(
        ...,
        description="List of PubMed IDs (PMIDs) to fetch annotations for."
    )
    batch_size: int = Field(
        default=50,
        description="Maximum number of PMIDs per API request."
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed requests."
    )
    max_requests_per_second: float = Field(
        default=3.0,
        description="Maximum number of requests per second."
    )


class FetchPaperAnnotationsTool(BaseTool):
    """
    Tool to fetch biomedical entity annotations from PubTator3 for a list of papers.
    
    This tool retrieves annotated entities (genes, diseases, chemicals, variants, etc.)
    and their relations from PubMed papers using the PubTator3 API.
    """
    name: str = "fetch_paper_annotations"
    description: str = (
        "Fetch biomedical entity annotations from PubTator3 for a list of PubMed IDs. "
        "Returns annotated entities (genes, diseases, chemicals, variants, species, cell lines) "
        "and their relations from the papers. Useful for extracting structured biomedical knowledge."
    )
    args_schema: Type[BaseModel] = FetchPaperAnnotationsToolInput
    
    def _run(
        self,
        pmids: List[str],
        batch_size: int = 50,
        max_retries: int = 3,
        max_requests_per_second: float = 3.0
    ) -> List[Dict[str, Any]]:
        """Execute the tool to fetch paper annotations."""
        search_results = pubtator_api_fetch_paper_annotations(
            pmids=pmids,
            batch_size=batch_size,
            max_retries=max_retries,
            max_requests_per_second=max_requests_per_second
        )
        # TODO: upload the search results to the sandbox
        # convert the search results to str
        search_results_str = json.dumps(search_results, indent=4)
        return search_results_str

# =====================================================
# Tool 3: Find Entities
# =====================================================
class FindEntitiesToolInput(BaseModel):
    """Input schema for FindEntitiesTool."""
    query_text: str = Field(
        ...,
        description="A single search term (partial entity name) to find entities in PubTator3. Example: 'remdesivir', 'COVID', 'BRCA1'."
    )
    concept_type: Optional[Literal["GENE", "DISEASE", "CHEMICAL", "VARIANT", "SPECIES", "CELLLINE"]] = Field(
        default=None,
        description="Restrict results to a specific entity type. If None, searches across all types."
    )
    limit: int = Field(
        default=10,
        description="Maximum number of results to return."
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed requests."
    )
    max_requests_per_second: float = Field(
        default=3.0,
        description="Maximum number of requests per second."
    )


class FindEntitiesTool(BaseTool):
    """
    Tool to find and autocomplete biomedical entity names in PubTator3.
    
    This tool provides entity name suggestions based on partial text input,
    useful for finding entity IDs and normalized names.
    """
    name: str = "find_entities"
    description: str = (
        "Find and autocomplete biomedical entity names in the PubTator3 database. "
        "Returns entity suggestions with IDs, normalized names, and types. "
        "Useful for entity disambiguation and finding correct entity identifiers for search."
    )
    args_schema: Type[BaseModel] = FindEntitiesToolInput
    
    def _run(
        self,
        query_text: str,
        concept_type: Optional[Literal["GENE", "DISEASE", "CHEMICAL", "VARIANT", "SPECIES", "CELLLINE"]] = None,
        limit: int = 10,
        max_retries: int = 3,
        max_requests_per_second: float = 3.0
    ) -> Optional[pd.DataFrame]:
        """Execute the tool to find entities."""
        results = pubtator_api_find_entities(
            query_text=query_text,
            concept_type=concept_type,
            limit=limit,
            max_retries=max_retries,
            max_requests_per_second=max_requests_per_second
        )
        if len(results) == 0:
            return "No entities found. Please try again with different query."
        else:
            if isinstance(results, pd.DataFrame):
                results_str = results.to_markdown()
                return results_str
            else:
                return "No entities found. Please try again with different query."

# =====================================================
# Tool 4: Search Papers
# =====================================================
class SearchPapersToolInput(BaseModel):
    """Input schema for SearchPapersTool."""
    boolean_query_text: Optional[str] = Field(
        default=None,
        description=(
            "Boolean query with entity IDs/types, keywords, AND/OR operators, and parentheses. "
            "Examples: '@CHEMICAL_remdesivir', '@CHEMICAL_Doxorubicin AND @DISEASE_Neoplasms', "
            "'(@DISEASE_COVID_19 AND complications) OR @DISEASE_Post_Acute_COVID_19_Syndrome'"
        )
    )
    relation_query: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Relation-based search dictionary with keys: 'relation_type' (TREAT, CAUSE, INTERACT, etc.), "
            "'entity1' (entity ID or type), 'entity2' (entity ID or type). "
            "Example: {'relation_type': 'TREAT', 'entity1': '@CHEMICAL_Doxorubicin', 'entity2': '@DISEASE_Neoplasms'}"
        )
    )
    page: int = Field(
        default=1,
        description="Page number for pagination."
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed requests."
    )
    max_requests_per_second: float = Field(
        default=3.0,
        description="Maximum number of requests per second."
    )


class SearchPapersTool(BaseTool):
    """
    Tool to search for PubMed articles using boolean or relation-based queries.
    
    Supports two search modes:
    1. Boolean queries with entity IDs, entity types, and free-text keywords
    2. Relation-based queries to find papers discussing specific entity relationships
    """
    name: str = "search_papers"
    description: str = (
        "Search for PubMed articles using boolean queries or relation-based queries. "
        "Boolean mode: Use entity IDs (@CHEMICAL_remdesivir), entity types, keywords, and AND/OR operators. "
        "Relation mode: Search by entity relationships (TREAT, CAUSE, INTERACT, etc.). "
        "Returns paper metadata including PMID, title, journal, date, and highlighted text snippets."
    )
    args_schema: Type[BaseModel] = SearchPapersToolInput
    sandbox: ExecutionSandboxWrapper = None

    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        boolean_query_text: Optional[str] = None,
        relation_query: Optional[Dict[str, Any]] = None,
        page: int = 1,
        max_retries: int = 3,
        max_requests_per_second: float = 3.0
    ) -> Optional[pd.DataFrame]:
        """Execute the tool to search papers."""
        search_results = pubtator_api_search_papers(
            boolean_query_text=boolean_query_text,
            relation_query=relation_query,
            page=page,
            max_retries=max_retries,
            max_requests_per_second=max_requests_per_second
        )
        # TODO: upload the search results to the sandbox
        if search_results is not None:
            md_str = search_results.to_markdown()
            return md_str
        else:
            return "No search results found. Please try again with different query."
