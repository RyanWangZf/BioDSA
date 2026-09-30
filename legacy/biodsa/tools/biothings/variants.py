"""Add tools for variant search and information retrieval from MyVariant.info."""

import asyncio
import logging
from typing import Any, Optional
from urllib.parse import quote
import pandas as pd
from pydantic import BaseModel, Field

# internal imports
from .utils import request_api as request_api
from .schema import VariantInfo, VariantItem

MYVARIANT_BASE_URL = "https://myvariant.info/v1"
MYVARIANT_QUERY_URL = f"{MYVARIANT_BASE_URL}/query"
MYVARIANT_GET_URL = f"{MYVARIANT_BASE_URL}/variant"


# ================================================
# Schemas
# ================================================

class VariantSearchRequest(BaseModel):
    """Search request for variants."""
    search: Optional[str] = Field(
        default=None,
        description="General search term to query across all fields"
    )
    rsid: Optional[str] = Field(
        default=None,
        description="dbSNP rsID (e.g., rs58991260)"
    )
    gene: Optional[str] = Field(
        default=None,
        description="Gene symbol or Entrez gene ID"
    )
    chrom: Optional[str] = Field(
        default=None,
        description="Chromosome (e.g., '1', 'X', 'MT')"
    )
    position: Optional[int] = Field(
        default=None,
        description="Genomic position"
    )
    hgvs: Optional[str] = Field(
        default=None,
        description="HGVS notation (e.g., 'chr1:g.35367G>A', 'NM_000546.5:c.215C>G')"
    )
    clinvar_significance: Optional[str] = Field(
        default=None,
        description="ClinVar clinical significance (e.g., 'pathogenic', 'benign')"
    )
    cosmic_id: Optional[str] = Field(
        default=None,
        description="COSMIC ID"
    )
    limit: int = Field(
        default=100,
        description="Maximum number of results to return (1-1000)"
    )
    skip: int = Field(
        default=0,
        description="Number of results to skip for pagination"
    )


class VariantSearchResponse(BaseModel):
    """Response from variant search."""
    results: list[VariantItem]
    total: int
    took: int
    max_score: float | None = None


# ================================================
# Helper Functions
# ================================================

def _build_search_query(request: VariantSearchRequest) -> dict[str, Any]:
    """Build query parameters for MyVariant.info API."""
    params = {
        "size": min(request.limit, 1000),  # API limit
        "from": request.skip,
        "fields": "_id,chrom,pos,ref,alt,rsid,gene.symbol,cadd.consequence,clinvar.rcv.clinical_significance",
    }
    
    # Build query string
    query_parts = []
    
    if request.search:
        query_parts.append(request.search)
    
    if request.rsid:
        query_parts.append(f"dbsnp.rsid:{quote(request.rsid)}")
    
    if request.gene:
        query_parts.append(f"gene.symbol:{quote(request.gene)}")
    
    if request.chrom:
        query_parts.append(f"chrom:{request.chrom}")
    
    if request.position:
        query_parts.append(f"pos:{request.position}")
    
    if request.hgvs:
        query_parts.append(f"_id:{quote(request.hgvs)}")
    
    if request.clinvar_significance:
        query_parts.append(f"clinvar.rcv.clinical_significance:{quote(request.clinvar_significance)}")
    
    if request.cosmic_id:
        query_parts.append(f"cosmic.cosmic_id:{quote(request.cosmic_id)}")
    
    if query_parts:
        params["q"] = " AND ".join(query_parts)
    else:
        # Default query if no specific terms provided
        params["q"] = "_exists_:rsid"
    
    return params


def _parse_variant_item(hit: dict[str, Any]) -> VariantItem:
    """Parse a variant hit from MyVariant.info API response."""
    # Extract gene symbol
    gene_symbol = None
    if hit.get("gene") and isinstance(hit["gene"], dict):
        gene_symbol = hit["gene"].get("symbol")
    elif hit.get("gene") and isinstance(hit["gene"], list):
        if hit["gene"] and isinstance(hit["gene"][0], dict):
            gene_symbol = hit["gene"][0].get("symbol")
    
    # Extract variant type
    variant_type = None
    if hit.get("cadd") and isinstance(hit["cadd"], dict):
        variant_type = hit["cadd"].get("consequence")
    
    # Extract clinical significance
    clinical_significance = None
    if hit.get("clinvar") and isinstance(hit["clinvar"], dict):
        rcv = hit["clinvar"].get("rcv")
        if rcv:
            if isinstance(rcv, dict):
                clinical_significance = rcv.get("clinical_significance")
            elif isinstance(rcv, list) and rcv:
                clinical_significance = rcv[0].get("clinical_significance")
    
    return VariantItem(
        variant_id=hit.get("_id", ""),
        chrom=hit.get("chrom"),
        pos=hit.get("pos"),
        ref=hit.get("ref"),
        alt=hit.get("alt"),
        rsid=hit.get("rsid"),
        gene_symbol=gene_symbol,
        variant_type=variant_type,
        clinical_significance=clinical_significance
    )


# ================================================
# API Functions
# ================================================

async def search_variant_api(request: VariantSearchRequest) -> VariantSearchResponse:
    """Search MyVariant.info API."""
    params = _build_search_query(request)
    
    # Use requests directly for consistency
    import requests
    
    try:
        response = requests.get(MYVARIANT_QUERY_URL, params=params)
        if response.status_code != 200:
            logging.error(f"Error searching variants: HTTP {response.status_code}: {response.text}")
            return VariantSearchResponse(results=[], total=0, took=0)
        
        response_data = response.json()
        error = None
    except Exception as e:
        logging.error(f"Error searching variants: {e}")
        return VariantSearchResponse(results=[], total=0, took=0)
    
    if not response_data:
        return VariantSearchResponse(results=[], total=0, took=0)
    
    # Parse response
    hits = response_data.get("hits", [])
    total = response_data.get("total", 0)
    took = response_data.get("took", 0)
    max_score = response_data.get("max_score")
    
    # Convert hits to VariantItem objects
    results = []
    for hit in hits:
        try:
            variant_item = _parse_variant_item(hit)
            results.append(variant_item)
        except Exception as e:
            logging.warning(f"Failed to parse variant hit: {e}")
            continue
    
    return VariantSearchResponse(
        results=results,
        total=total,
        took=took,
        max_score=max_score
    )


async def fetch_variant_by_id(variant_id: str) -> VariantInfo | None:
    """Fetch detailed variant information by ID."""
    params = {
        "fields": "chrom,pos,ref,alt,rsid,gene,clinvar,dbsnp,cadd,dbnsfp,cosmic,vcf"
    }
    
    response, error = await request_api(
        url=f"{MYVARIANT_GET_URL}/{quote(variant_id, safe='')}",
        request=params,
        method="GET",
        use_requests=True,
    )
    
    if error or not response:
        return None
    
    try:
        # Handle array response (multiple results) - take the first one
        if isinstance(response, list):
            if not response:
                return None
            response = response[0]
        
        return VariantInfo(**response)
    except Exception as e:
        logging.warning(f"Failed to parse variant response: {e}")
        return None


# ================================================
# Main Functions
# ================================================

def search_variants(
    search: Optional[str] = None,
    rsid: Optional[str] = None,
    gene: Optional[str] = None,
    chrom: Optional[str] = None,
    position: Optional[int] = None,
    hgvs: Optional[str] = None,
    clinvar_significance: Optional[str] = None,
    cosmic_id: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Search for genetic variants using MyVariant.info API.
    
    Args:
        search: General search term to query across all fields
        rsid: dbSNP rsID (e.g., rs58991260)
        gene: Gene symbol or Entrez gene ID
        chrom: Chromosome (e.g., '1', 'X', 'MT')
        position: Genomic position
        hgvs: HGVS notation (e.g., 'chr1:g.35367G>A')
        clinvar_significance: ClinVar clinical significance
        cosmic_id: COSMIC ID
        limit: Maximum number of results to return (1-1000)
        skip: Number of results to skip for pagination
        save_path: Path to save the results
    
    Returns:
        Tuple of (DataFrame with results, summary string)
    """
    
    async def _search():
        request = VariantSearchRequest(
            search=search,
            rsid=rsid,
            gene=gene,
            chrom=chrom,
            position=position,
            hgvs=hgvs,
            clinvar_significance=clinvar_significance,
            cosmic_id=cosmic_id,
            limit=limit,
            skip=skip
        )
        
        response = await search_variant_api(request)
        return response
    
    # Run the async function
    response = asyncio.run(_search())
    
    # Convert to DataFrame
    if response.results:
        data = []
        for variant in response.results:
            data.append({
                "variant_id": variant.variant_id,
                "chrom": variant.chrom,
                "pos": variant.pos,
                "ref": variant.ref,
                "alt": variant.alt,
                "rsid": variant.rsid,
                "gene_symbol": variant.gene_symbol,
                "variant_type": variant.variant_type,
                "clinical_significance": variant.clinical_significance,
            })
        
        output_df = pd.DataFrame(data)
    else:
        output_df = pd.DataFrame()
    
    # Create summary string
    output_str = f"Found {len(response.results)} variants"
    if response.total > len(response.results):
        output_str += f" (showing {len(response.results)} of {response.total} total)"
    
    if response.took:
        output_str += f" in {response.took}ms"
    
    # Save results if requested
    if save_path and not output_df.empty:
        try:
            output_df.to_csv(save_path, index=False)
            save_result_str = f"Variant search results saved to {save_path}"
        except Exception as e:
            logging.error(f"Error saving results to {save_path}: {e}")
            save_result_str = f"Error saving results to {save_path}: {e}"
        output_str = f"{output_str}\n-----\n{save_result_str}"
    
    return output_df, output_str


def fetch_variant_details_by_ids(
    variant_ids: list[str],
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Fetch detailed variant information by IDs from MyVariant.info.
    
    Args:
        variant_ids: List of variant IDs (HGVS notation or rsIDs) to fetch details from
        save_path: Path to save the results
    
    Returns:
        Tuple of (DataFrame with results, summary string)
    """
    
    async def _fetch_details():
        tasks = [fetch_variant_by_id(variant_id) for variant_id in variant_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        variants = []
        for result in results:
            if isinstance(result, VariantInfo):
                variants.append(result)
            elif isinstance(result, Exception):
                logging.warning(f"Failed to fetch variant: {result}")
        
        return variants
    
    # Run the async function
    variants = asyncio.run(_fetch_details())
    
    # Convert to DataFrame
    if variants:
        data = []
        for variant in variants:
            data.append({
                "variant_id": variant.variant_id,
                "chrom": variant.chrom,
                "pos": variant.pos,
                "ref": variant.ref,
                "alt": variant.alt,
                "rsid": variant.rsid,
                "gene": str(variant.gene) if variant.gene else "",
                "clinvar": str(variant.clinvar)[:200] if variant.clinvar else "",
                "dbsnp": str(variant.dbsnp)[:200] if variant.dbsnp else "",
                "cadd": str(variant.cadd)[:200] if variant.cadd else "",
                "cosmic": str(variant.cosmic)[:200] if variant.cosmic else "",
            })
        
        output_df = pd.DataFrame(data)
    else:
        output_df = pd.DataFrame()
    
    # Create summary string
    output_str = f"Fetched details for {len(variants)} variants out of {len(variant_ids)} requested"
    
    # Save results if requested
    if save_path and not output_df.empty:
        try:
            output_df.to_csv(save_path, index=False)
            save_result_str = f"Variant details saved to {save_path}"
        except Exception as e:
            logging.error(f"Error saving results to {save_path}: {e}")
            save_result_str = f"Error saving results to {save_path}: {e}"
        output_str = f"{output_str}\n-----\n{save_result_str}"
    
    return output_df, output_str

