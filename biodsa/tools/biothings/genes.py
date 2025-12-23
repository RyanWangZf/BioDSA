"""Add tools for gene search and information retrieval from MyGene.info."""

import asyncio
import logging
from typing import Any, Optional
from urllib.parse import quote
import pandas as pd
from pydantic import BaseModel, Field

# internal imports
from .utils import request_api as request_api
from .schema import GeneInfo, GeneItem

MYGENE_BASE_URL = "https://mygene.info/v3"
MYGENE_QUERY_URL = f"{MYGENE_BASE_URL}/query"
MYGENE_GET_URL = f"{MYGENE_BASE_URL}/gene"


# ================================================
# Schemas
# ================================================

class GeneSearchRequest(BaseModel):
    """Search request for genes."""
    search: Optional[str] = Field(
        default=None,
        description="General search term to query across all fields"
    )
    symbol: Optional[str] = Field(
        default=None,
        description="Gene symbol (e.g., TP53, BRCA1)"
    )
    name: Optional[str] = Field(
        default=None,
        description="Gene name"
    )
    entrezgene: Optional[str] = Field(
        default=None,
        description="Entrez gene ID"
    )
    ensembl_gene: Optional[str] = Field(
        default=None,
        description="Ensembl gene ID"
    )
    species: Optional[str] = Field(
        default="human",
        description="Species (default: human)"
    )
    limit: int = Field(
        default=100,
        description="Maximum number of results to return (1-1000)"
    )
    skip: int = Field(
        default=0,
        description="Number of results to skip for pagination"
    )


class GeneSearchResponse(BaseModel):
    """Response from gene search."""
    results: list[GeneItem]
    total: int
    took: int
    max_score: float | None = None


# ================================================
# Helper Functions
# ================================================

def _build_search_query(request: GeneSearchRequest) -> dict[str, Any]:
    """Build query parameters for MyGene.info API."""
    params = {
        "size": min(request.limit, 1000),  # API limit
        "from": request.skip,
        "species": request.species or "human",
        "fields": "_id,symbol,name,summary,alias,entrezgene,type_of_gene,taxid",
    }
    
    # Build query string
    query_parts = []
    
    if request.search:
        query_parts.append(request.search)
    
    if request.symbol:
        query_parts.append(f"symbol:{quote(request.symbol)}")
    
    if request.name:
        query_parts.append(f"name:{quote(request.name)}")
    
    if request.entrezgene:
        query_parts.append(f"entrezgene:{request.entrezgene}")
    
    if request.ensembl_gene:
        query_parts.append(f"ensembl.gene:{quote(request.ensembl_gene)}")
    
    if query_parts:
        params["q"] = " AND ".join(query_parts)
    else:
        # Default query if no specific terms provided - search for genes with symbols
        params["q"] = "_exists_:symbol"
    
    return params


def _parse_gene_item(hit: dict[str, Any]) -> GeneItem:
    """Parse a gene hit from MyGene.info API response."""
    return GeneItem(
        gene_id=hit.get("_id", ""),
        symbol=hit.get("symbol"),
        name=hit.get("name"),
        summary=hit.get("summary"),
        alias=hit.get("alias", []) if isinstance(hit.get("alias"), list) else [hit.get("alias")] if hit.get("alias") else [],
        entrezgene=hit.get("entrezgene"),
        type_of_gene=hit.get("type_of_gene"),
        taxid=hit.get("taxid")
    )


# ================================================
# API Functions
# ================================================

async def search_gene_api(request: GeneSearchRequest) -> GeneSearchResponse:
    """Search MyGene.info API."""
    params = _build_search_query(request)
    
    # Use requests directly for consistency
    import requests
    
    try:
        response = requests.get(MYGENE_QUERY_URL, params=params)
        if response.status_code != 200:
            logging.error(f"Error searching genes: HTTP {response.status_code}: {response.text}")
            return GeneSearchResponse(results=[], total=0, took=0)
        
        response_data = response.json()
        error = None
    except Exception as e:
        logging.error(f"Error searching genes: {e}")
        return GeneSearchResponse(results=[], total=0, took=0)
    
    if not response_data:
        return GeneSearchResponse(results=[], total=0, took=0)
    
    # Parse response
    hits = response_data.get("hits", [])
    total = response_data.get("total", 0)
    took = response_data.get("took", 0)
    max_score = response_data.get("max_score")
    
    # Convert hits to GeneItem objects
    results = []
    for hit in hits:
        try:
            gene_item = _parse_gene_item(hit)
            results.append(gene_item)
        except Exception as e:
            logging.warning(f"Failed to parse gene hit: {e}")
            continue
    
    return GeneSearchResponse(
        results=results,
        total=total,
        took=took,
        max_score=max_score
    )


async def fetch_gene_by_id(gene_id: str) -> GeneInfo | None:
    """Fetch detailed gene information by ID."""
    params = {
        "fields": "symbol,name,summary,alias,type_of_gene,ensembl,refseq,entrezgene,taxid"
    }
    
    response, error = await request_api(
        url=f"{MYGENE_GET_URL}/{quote(gene_id, safe='')}",
        request=params,
        method="GET",
        use_requests=True,
    )
    
    if error or not response:
        return None
    
    try:
        return GeneInfo(**response)
    except Exception as e:
        logging.warning(f"Failed to parse gene response: {e}")
        return None


# ================================================
# Main Functions
# ================================================

def search_genes(
    search: Optional[str] = None,
    symbol: Optional[str] = None,
    name: Optional[str] = None,
    entrezgene: Optional[str] = None,
    ensembl_gene: Optional[str] = None,
    species: Optional[str] = "human",
    limit: int = 100,
    skip: int = 0,
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Search for genes using MyGene.info API.
    
    Args:
        search: General search term to query across all fields
        symbol: Gene symbol (e.g., TP53, BRCA1)
        name: Gene name
        entrezgene: Entrez gene ID
        ensembl_gene: Ensembl gene ID
        species: Species (default: human)
        limit: Maximum number of results to return (1-1000)
        skip: Number of results to skip for pagination
        save_path: Path to save the results
    
    Returns:
        Tuple of (DataFrame with results, summary string)
    """
    
    async def _search():
        request = GeneSearchRequest(
            search=search,
            symbol=symbol,
            name=name,
            entrezgene=entrezgene,
            ensembl_gene=ensembl_gene,
            species=species,
            limit=limit,
            skip=skip
        )
        
        response = await search_gene_api(request)
        return response
    
    # Run the async function
    response = asyncio.run(_search())
    
    # Convert to DataFrame
    if response.results:
        data = []
        for gene in response.results:
            data.append({
                "gene_id": gene.gene_id,
                "symbol": gene.symbol,
                "name": gene.name,
                "summary": gene.summary,
                "alias": ", ".join(gene.alias) if gene.alias else "",
                "entrezgene": gene.entrezgene,
                "type_of_gene": gene.type_of_gene,
                "taxid": gene.taxid,
            })
        
        output_df = pd.DataFrame(data)
    else:
        output_df = pd.DataFrame()
    
    # Create summary string
    output_str = f"Found {len(response.results)} genes"
    if response.total > len(response.results):
        output_str += f" (showing {len(response.results)} of {response.total} total)"
    
    if response.took:
        output_str += f" in {response.took}ms"
    
    # Save results if requested
    if save_path and not output_df.empty:
        try:
            output_df.to_csv(save_path, index=False)
            save_result_str = f"Gene search results saved to {save_path}"
        except Exception as e:
            logging.error(f"Error saving results to {save_path}: {e}")
            save_result_str = f"Error saving results to {save_path}: {e}"
        output_str = f"{output_str}\n-----\n{save_result_str}"
    
    return output_df, output_str


def fetch_gene_details_by_ids(
    gene_ids: list[str],
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Fetch detailed gene information by IDs from MyGene.info.
    
    Args:
        gene_ids: List of gene IDs to fetch details from
        save_path: Path to save the results
    
    Returns:
        Tuple of (DataFrame with results, summary string)
    """
    
    async def _fetch_details():
        tasks = [fetch_gene_by_id(gene_id) for gene_id in gene_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        genes = []
        for result in results:
            if isinstance(result, GeneInfo):
                genes.append(result)
            elif isinstance(result, Exception):
                logging.warning(f"Failed to fetch gene: {result}")
        
        return genes
    
    # Run the async function
    genes = asyncio.run(_fetch_details())
    
    # Convert to DataFrame
    if genes:
        data = []
        for gene in genes:
            data.append({
                "gene_id": gene.gene_id,
                "symbol": gene.symbol,
                "name": gene.name,
                "summary": gene.summary,
                "alias": ", ".join(gene.alias) if gene.alias else "",
                "entrezgene": gene.entrezgene,
                "type_of_gene": gene.type_of_gene,
                "taxid": gene.taxid,
                "ensembl": str(gene.ensembl) if gene.ensembl else "",
                "refseq": str(gene.refseq) if gene.refseq else "",
            })
        
        output_df = pd.DataFrame(data)
    else:
        output_df = pd.DataFrame()
    
    # Create summary string
    output_str = f"Fetched details for {len(genes)} genes out of {len(gene_ids)} requested"
    
    # Save results if requested
    if save_path and not output_df.empty:
        try:
            output_df.to_csv(save_path, index=False)
            save_result_str = f"Gene details saved to {save_path}"
        except Exception as e:
            logging.error(f"Error saving results to {save_path}: {e}")
            save_result_str = f"Error saving results to {save_path}: {e}"
        output_str = f"{output_str}\n-----\n{save_result_str}"
    
    return output_df, output_str