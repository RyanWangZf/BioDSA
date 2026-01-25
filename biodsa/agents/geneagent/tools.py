"""
LangChain tool wrappers for the GeneAgent.

These tools wrap the gene set analysis APIs to provide domain database access
for the self-verification workflow. Tools are used by the verification worker
to fact-check claims about gene functions and biological processes.

Reference: https://github.com/ncbi-nlp/GeneAgent
"""
from typing import Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

# Import the underlying API functions
from biodsa.tools.gene_set import (
    get_pathway_for_gene_set,
    get_enrichment_for_gene_set,
    get_interactions_for_gene_set,
    get_complex_for_gene_set,
    get_gene_summary_for_single_gene,
    get_disease_for_single_gene,
    get_domain_for_single_gene,
)

# Import PubMed search if available
try:
    from biodsa.tools.pubmed.pubmed_api import search_pubmed, fetch_pubmed_details
    PUBMED_AVAILABLE = True
except ImportError:
    PUBMED_AVAILABLE = False


# =============================================================================
# Input Schemas
# =============================================================================

class GeneSetInput(BaseModel):
    """Input schema for gene set tools."""
    gene_set: str = Field(
        description="A gene set separated only by comma (no whitespace). Example: 'BRCA1,TP53,EGFR'"
    )


class SingleGeneInput(BaseModel):
    """Input schema for single gene tools."""
    gene_name: str = Field(
        description="A single gene name to search. Example: 'BRCA1'"
    )
    specie: str = Field(
        default="Homo",
        description="Species name. Options: 'Homo' (human) or 'Mus' (mouse)"
    )


class SingleGeneSimpleInput(BaseModel):
    """Input schema for single gene tools without species parameter."""
    gene_name: str = Field(
        description="A single gene name to search. Example: 'BRCA1'"
    )


class PubMedSearchInput(BaseModel):
    """Input schema for PubMed search."""
    term: str = Field(
        description="Search query for PubMed. Can include gene names, biological processes, etc."
    )


# =============================================================================
# Gene Set Tools (operate on multiple genes)
# =============================================================================

class GetPathwayForGeneSetTool(BaseTool):
    """Tool to get biological pathways for a gene set."""
    
    name: str = "get_pathway_for_gene_set"
    description: str = """Get top-5 biological pathway names for a gene set.
    
Queries multiple databases including KEGG, Reactome, BioPlanet, and MSigDB Hallmark via Enrichr.
Returns pathway terms, overlapping genes, and source database.

Input: Gene set separated only by comma (no whitespace), e.g., "BRCA1,TP53,EGFR"
"""
    args_schema: Type[BaseModel] = GeneSetInput
    
    def _run(self, gene_set: str) -> str:
        """Execute pathway search."""
        try:
            result = get_pathway_for_gene_set(gene_set)
            return f"Pathway analysis results for {gene_set}:\n{result}"
        except Exception as e:
            return f"Error getting pathways: {str(e)}"


class GetEnrichmentForGeneSetTool(BaseTool):
    """Tool to get GO enrichment for a gene set."""
    
    name: str = "get_enrichment_for_gene_set"
    description: str = """Get top-5 enrichment function names for a gene set.
    
Uses g:Profiler API for comprehensive Gene Ontology enrichment analysis.
Returns enriched biological processes, molecular functions, and cellular components.

Input: Gene set separated only by comma (no whitespace), e.g., "BRCA1,TP53,EGFR"
"""
    args_schema: Type[BaseModel] = GeneSetInput
    
    def _run(self, gene_set: str) -> str:
        """Execute enrichment analysis."""
        try:
            result = get_enrichment_for_gene_set(gene_set)
            return f"Enrichment analysis results for {gene_set}:\n{result}"
        except Exception as e:
            return f"Error getting enrichment: {str(e)}"


class GetInteractionsForGeneSetTool(BaseTool):
    """Tool to get protein-protein interactions for a gene set."""
    
    name: str = "get_interactions_for_gene_set"
    description: str = """Get protein-protein interaction information for a gene set.
    
Queries PubTator3 API for up to 50 protein-protein interactions.
Useful for understanding gene networks and interaction partners.

Input: Gene set separated only by comma (no whitespace), e.g., "BRCA1,TP53,EGFR"
"""
    args_schema: Type[BaseModel] = GeneSetInput
    
    def _run(self, gene_set: str) -> str:
        """Execute interaction search."""
        try:
            result = get_interactions_for_gene_set(gene_set)
            return f"Protein-protein interactions for {gene_set}:\n{result}"
        except Exception as e:
            return f"Error getting interactions: {str(e)}"


class GetComplexForGeneSetTool(BaseTool):
    """Tool to get protein complex information for a gene set."""
    
    name: str = "get_complex_for_gene_set"
    description: str = """Get protein complex information for a gene set.
    
Returns complex protocol IDs and corresponding complex names from PubTator3 API.
Useful for identifying known protein complexes containing the genes.

Input: Gene set separated only by comma (no whitespace), e.g., "BRCA1,TP53,EGFR"
"""
    args_schema: Type[BaseModel] = GeneSetInput
    
    def _run(self, gene_set: str) -> str:
        """Execute complex search."""
        try:
            result = get_complex_for_gene_set(gene_set)
            return f"Protein complex information for {gene_set}:\n{result}"
        except Exception as e:
            return f"Error getting complex info: {str(e)}"


# =============================================================================
# Single Gene Tools (operate on individual genes)
# =============================================================================

class GetGeneSummaryForSingleGeneTool(BaseTool):
    """Tool to get summary information for a single gene."""
    
    name: str = "get_gene_summary_for_single_gene"
    description: str = """Get comprehensive summary information for a single gene.
    
Queries NCBI Gene database via E-utilities.
Returns function, location, aliases, and other metadata.
Supports human (Homo) and mouse (Mus) species.

Input: Single gene name and optional species (default: Homo)
"""
    args_schema: Type[BaseModel] = SingleGeneInput
    
    def _run(self, gene_name: str, specie: str = "Homo") -> str:
        """Execute gene summary search."""
        try:
            result = get_gene_summary_for_single_gene(gene_name, specie)
            if result is None:
                return f"No gene summary found for {gene_name} in {specie}"
            return f"Gene summary for {gene_name} ({specie}):\n{result}"
        except Exception as e:
            return f"Error getting gene summary: {str(e)}"


class GetDiseaseForSingleGeneTool(BaseTool):
    """Tool to get disease associations for a single gene."""
    
    name: str = "get_disease_for_single_gene"
    description: str = """Get disease associations for a single gene.
    
Returns up to 100 disease IDs and corresponding disease names.
Queries PubTator API for gene-disease associations from literature mining.

Input: Single gene name
"""
    args_schema: Type[BaseModel] = SingleGeneSimpleInput
    
    def _run(self, gene_name: str) -> str:
        """Execute disease association search."""
        try:
            result = get_disease_for_single_gene(gene_name)
            if result is None:
                return f"No disease associations found for {gene_name}"
            return f"Disease associations for {gene_name}:\n{result}"
        except Exception as e:
            return f"Error getting disease associations: {str(e)}"


class GetDomainForSingleGeneTool(BaseTool):
    """Tool to get protein domain information for a single gene."""
    
    name: str = "get_domain_for_single_gene"
    description: str = """Get protein domain information for a single gene.
    
Returns up to 10 domain IDs and corresponding domain names.
Queries PubTator CDD API for conserved domain information.

Input: Single gene name
"""
    args_schema: Type[BaseModel] = SingleGeneSimpleInput
    
    def _run(self, gene_name: str) -> str:
        """Execute domain search."""
        try:
            result = get_domain_for_single_gene(gene_name)
            if result is None:
                return f"No domain information found for {gene_name}"
            return f"Protein domains for {gene_name}:\n{result}"
        except Exception as e:
            return f"Error getting domain info: {str(e)}"


# =============================================================================
# PubMed Search Tool
# =============================================================================

class GetPubMedArticlesTool(BaseTool):
    """Tool to search PubMed for relevant articles."""
    
    name: str = "get_pubmed_articles"
    description: str = """Search PubMed for articles related to a query.
    
Returns top 5 relevant articles with PMIDs, titles, and abstracts.
Useful for finding literature evidence about gene functions and biological processes.

Input: Search query (can include gene names, biological processes, etc.)
"""
    args_schema: Type[BaseModel] = PubMedSearchInput
    
    def _run(self, term: str) -> str:
        """Execute PubMed search."""
        try:
            if PUBMED_AVAILABLE:
                # Use the biodsa pubmed API
                results = search_pubmed(term, max_results=5)
                if not results:
                    return f"No PubMed articles found for query: {term}"
                
                # Format results
                output_parts = []
                for pmid in results:
                    details = fetch_pubmed_details([pmid])
                    if details:
                        article = details[0]
                        output_parts.append(
                            f"PMID: {pmid}\n"
                            f"Title: {article.get('title', 'N/A')}\n"
                            f"Abstract: {article.get('abstract', 'N/A')[:500]}...\n"
                        )
                return "\n".join(output_parts) if output_parts else f"No details found for query: {term}"
            else:
                # Fallback: use the original GeneAgent approach with requests
                return self._pubmed_search_fallback(term)
        except Exception as e:
            return f"Error searching PubMed: {str(e)}"
    
    def _pubmed_search_fallback(self, term: str) -> str:
        """Fallback PubMed search using direct API calls."""
        import requests
        from xml.etree import ElementTree
        
        base_url_pubmed = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        search_url = f"{base_url_pubmed}/esearch.fcgi"
        fetch_url = f"{base_url_pubmed}/efetch.fcgi"
        
        search_params = {
            "db": "pubmed",
            "term": term,
            "retmode": "xml",
            "retmax": "5",
            "sort": "relevance"
        }
        
        search_response = requests.get(search_url, params=search_params)
        try:
            search_results = ElementTree.fromstring(search_response.content)
            id_list = [id_tag.text for id_tag in search_results.findall('.//Id')]
        except ElementTree.ParseError as e:
            return f"Error parsing search results: {e}"
        
        if not id_list:
            return f"No articles found for the query: {term}"
        
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml"
        }
        fetch_response = requests.get(fetch_url, params=fetch_params)
        
        try:
            articles = ElementTree.fromstring(fetch_response.content)
        except ElementTree.ParseError as e:
            return f"Error parsing fetch results: {e}"
        
        results = []
        for article in articles.findall('.//PubmedArticle'):
            pmid_elem = article.find('.//PMID')
            pmid = pmid_elem.text if pmid_elem is not None else "No PMID available"
            title_elem = article.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else "No title available"
            abstract_elem = article.find('.//Abstract/AbstractText')
            abstract_text = abstract_elem.text if abstract_elem is not None else "No abstract available"
            results.append(f"PMID: {pmid}\nTitle: {title}\nAbstract: {abstract_text}\n")
        
        return "".join(results)


# =============================================================================
# Tool Collection Functions
# =============================================================================

def get_geneagent_tools() -> List[BaseTool]:
    """Get all tools for the GeneAgent verification worker.
    
    Returns the full set of tools used in the original GeneAgent:
    - get_complex_for_gene_set
    - get_disease_for_single_gene
    - get_domain_for_single_gene
    - get_enrichment_for_gene_set
    - get_pathway_for_gene_set
    - get_interactions_for_gene_set
    - get_gene_summary_for_single_gene
    - get_pubmed_articles
    """
    return [
        GetComplexForGeneSetTool(),
        GetDiseaseForSingleGeneTool(),
        GetDomainForSingleGeneTool(),
        GetEnrichmentForGeneSetTool(),
        GetPathwayForGeneSetTool(),
        GetInteractionsForGeneSetTool(),
        GetGeneSummaryForSingleGeneTool(),
        GetPubMedArticlesTool(),
    ]


def get_gene_set_tools() -> List[BaseTool]:
    """Get only the gene set tools (operate on multiple genes)."""
    return [
        GetComplexForGeneSetTool(),
        GetEnrichmentForGeneSetTool(),
        GetPathwayForGeneSetTool(),
        GetInteractionsForGeneSetTool(),
    ]


def get_single_gene_tools() -> List[BaseTool]:
    """Get only the single gene tools (operate on individual genes)."""
    return [
        GetGeneSummaryForSingleGeneTool(),
        GetDiseaseForSingleGeneTool(),
        GetDomainForSingleGeneTool(),
    ]
