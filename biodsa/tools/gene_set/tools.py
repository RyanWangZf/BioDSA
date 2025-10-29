from typing import Literal, Type, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import json

from biodsa.tools.gene_set.get_pathway_for_gene_set import get_pathway_for_gene_set
from biodsa.tools.gene_set.get_enrichment_for_gene_set import get_enrichment_for_gene_set
from biodsa.tools.gene_set.get_interactions_for_gene_set import get_interactions_for_gene_set
from biodsa.tools.gene_set.get_complex_for_gene_set import get_complex_for_gene_set
from biodsa.tools.gene_set.get_gene_summary_for_single_gene import get_gene_summary_for_single_gene
from biodsa.tools.gene_set.get_disease_for_single_gene import get_disease_for_single_gene
from biodsa.tools.gene_set.get_domain_for_single_gene import get_domain_for_single_gene

__all__ = [
    "GetPathwayForGeneSetTool",
    "GetEnrichmentForGeneSetTool",
    "GetInteractionsForGeneSetTool",
    "GetComplexForGeneSetTool",
    "GetGeneSummaryForSingleGeneTool",
    "GetDiseaseForSingleGeneTool",
    "GetDomainForSingleGeneTool",
    "GetPathwayForGeneSetToolInput",
    "GetEnrichmentForGeneSetToolInput",
    "GetInteractionsForGeneSetToolInput",
    "GetComplexForGeneSetToolInput",
    "GetGeneSummaryForSingleGeneToolInput",
    "GetDiseaseForSingleGeneToolInput",
    "GetDomainForSingleGeneToolInput",
]

# =====================================================
# Tool 1: Get Pathway for Gene Set
# =====================================================
class GetPathwayForGeneSetToolInput(BaseModel):
    """Input schema for GetPathwayForGeneSetTool."""
    gene_set: str = Field(
        ...,
        description="A gene set separated only by comma ',' (no whitespace). For example: 'BRCA1,TP53,EGFR'."
    )


class GetPathwayForGeneSetTool(BaseTool):
    """
    Tool to get biological pathway annotations for a gene set.
    
    This tool queries multiple pathway databases (KEGG, Reactome, BioPlanet, MSigDB Hallmark)
    via Enrichr API and returns the top-5 enriched pathways with overlapping genes.
    """
    name: str = "get_pathway_for_gene_set"
    description: str = (
        "Get top-5 biological pathway names for a given gene set. "
        "Queries KEGG, Reactome, BioPlanet, and MSigDB Hallmark databases. "
        "Returns pathway terms, overlapping genes, and source database. "
        "Useful for understanding biological pathways associated with a set of genes."
    )
    args_schema: Type[BaseModel] = GetPathwayForGeneSetToolInput
    
    def _run(self, gene_set: str) -> str:
        """Execute the tool to get pathway annotations."""
        results = get_pathway_for_gene_set(gene_set)
        return results


# =====================================================
# Tool 2: Get Enrichment for Gene Set
# =====================================================
class GetEnrichmentForGeneSetToolInput(BaseModel):
    """Input schema for GetEnrichmentForGeneSetTool."""
    gene_set: str = Field(
        ...,
        description="A gene set separated only by comma ',' (no whitespace). For example: 'BRCA1,TP53,EGFR'."
    )


class GetEnrichmentForGeneSetTool(BaseTool):
    """
    Tool to perform functional enrichment analysis for a gene set.
    
    This tool uses g:Profiler API to perform enrichment analysis across multiple
    functional databases including GO, KEGG, Reactome, and more.
    """
    name: str = "get_enrichment_for_gene_set"
    description: str = (
        "Get top-5 enrichment function names for a gene set, including biological regulation, "
        "signaling, and metabolism. Uses g:Profiler for comprehensive enrichment analysis. "
        "Returns enriched terms with statistics and gene overlaps."
    )
    args_schema: Type[BaseModel] = GetEnrichmentForGeneSetToolInput
    
    def _run(self, gene_set: str) -> str:
        """Execute the tool to get enrichment analysis."""
        results = get_enrichment_for_gene_set(gene_set)
        return results


# =====================================================
# Tool 3: Get Interactions for Gene Set
# =====================================================
class GetInteractionsForGeneSetToolInput(BaseModel):
    """Input schema for GetInteractionsForGeneSetTool."""
    gene_set: str = Field(
        ...,
        description="A gene set delimited with comma. For example: 'BRCA1,TP53,EGFR'."
    )


class GetInteractionsForGeneSetTool(BaseTool):
    """
    Tool to get protein-protein interaction information for a gene set.
    
    This tool queries the PubTator3 API to retrieve protein-protein interactions
    for the given genes, returning up to 50 interactions.
    """
    name: str = "get_interactions_for_gene_set"
    description: str = (
        "Get information on interacting genes for a given gene set. "
        "Returns protein-protein interactions from literature mining via PubTator3. "
        "Useful for understanding gene networks and interaction partners."
    )
    args_schema: Type[BaseModel] = GetInteractionsForGeneSetToolInput
    
    def _run(self, gene_set: str) -> str:
        """Execute the tool to get gene interactions."""
        results = get_interactions_for_gene_set(gene_set)
        return results


# =====================================================
# Tool 4: Get Complex for Gene Set
# =====================================================
class GetComplexForGeneSetToolInput(BaseModel):
    """Input schema for GetComplexForGeneSetTool."""
    gene_set: str = Field(
        ...,
        description="A gene set delimited only with comma ',' (no whitespace). For example: 'BRCA1,TP53,EGFR'."
    )


class GetComplexForGeneSetTool(BaseTool):
    """
    Tool to get protein complex information for a gene set.
    
    This tool queries the PubTator3 API to retrieve protein complex information,
    including complex protocol IDs and corresponding complex names.
    """
    name: str = "get_complex_for_gene_set"
    description: str = (
        "Get information on all possible protein complex protocol IDs and corresponding "
        "complex names for a given gene set. Returns complex annotations from PubTator3. "
        "Useful for identifying protein complexes that genes may participate in."
    )
    args_schema: Type[BaseModel] = GetComplexForGeneSetToolInput
    
    def _run(self, gene_set: str) -> str:
        """Execute the tool to get protein complex information."""
        results = get_complex_for_gene_set(gene_set)
        return results


# =====================================================
# Tool 5: Get Gene Summary for Single Gene
# =====================================================
class GetGeneSummaryForSingleGeneToolInput(BaseModel):
    """Input schema for GetGeneSummaryForSingleGeneTool."""
    gene_name: str = Field(
        ...,
        description="A single gene name to search. For example: 'BRCA1'."
    )
    specie: Literal["Homo", "Mus"] = Field(
        ...,
        description="Species name. Either 'Homo' (human) or 'Mus' (mouse)."
    )


class GetGeneSummaryForSingleGeneTool(BaseTool):
    """
    Tool to get comprehensive summary information for a single gene.
    
    This tool queries NCBI Gene database via E-utilities to retrieve gene summary
    information including function, location, aliases, and other metadata.
    """
    name: str = "get_gene_summary_for_single_gene"
    description: str = (
        "Get summary information on a single gene including function, location, aliases, "
        "and other metadata. Queries NCBI Gene database for comprehensive gene information. "
        "Supports human (Homo) and mouse (Mus) species."
    )
    args_schema: Type[BaseModel] = GetGeneSummaryForSingleGeneToolInput
    
    def _run(self, gene_name: str, specie: Literal["Homo", "Mus"]) -> str:
        """Execute the tool to get gene summary."""
        results = get_gene_summary_for_single_gene(gene_name, specie)
        if results is None:
            return f"No summary found for gene '{gene_name}' in species '{specie}'."
        # Convert dict to formatted JSON string for better readability
        return json.dumps(results, indent=2)


# =====================================================
# Tool 6: Get Disease for Single Gene
# =====================================================
class GetDiseaseForSingleGeneToolInput(BaseModel):
    """Input schema for GetDiseaseForSingleGeneTool."""
    gene_name: str = Field(
        ...,
        description="A single gene name to search. For example: 'BRCA1'."
    )


class GetDiseaseForSingleGeneTool(BaseTool):
    """
    Tool to get disease associations for a single gene.
    
    This tool queries the PubTator API to retrieve disease associations for a gene,
    including disease IDs and corresponding disease names from literature.
    """
    name: str = "get_disease_for_single_gene"
    description: str = (
        "Get information on related diseases for a given gene, including disease IDs "
        "and corresponding disease names. Queries PubTator API for gene-disease associations "
        "from literature mining. Returns up to 100 disease associations."
    )
    args_schema: Type[BaseModel] = GetDiseaseForSingleGeneToolInput
    
    def _run(self, gene_name: str) -> str:
        """Execute the tool to get disease associations."""
        results = get_disease_for_single_gene(gene_name)
        return results


# =====================================================
# Tool 7: Get Domain for Single Gene
# =====================================================
class GetDomainForSingleGeneToolInput(BaseModel):
    """Input schema for GetDomainForSingleGeneTool."""
    gene_name: str = Field(
        ...,
        description="A single gene name to search. For example: 'BRCA1'."
    )


class GetDomainForSingleGeneTool(BaseTool):
    """
    Tool to get protein domain information for a single gene.
    
    This tool queries the PubTator API's conserved domain database (CDD) to retrieve
    information about protein domains, including domain IDs and names.
    """
    name: str = "get_domain_for_single_gene"
    description: str = (
        "Get information on related biological protein domains for a given gene, "
        "including domain IDs and corresponding domain names. Queries PubTator CDD API "
        "for conserved domain information. Returns up to 10 domain annotations."
    )
    args_schema: Type[BaseModel] = GetDomainForSingleGeneToolInput
    
    def _run(self, gene_name: str) -> str:
        """Execute the tool to get protein domain information."""
        results = get_domain_for_single_gene(gene_name)
        return results

