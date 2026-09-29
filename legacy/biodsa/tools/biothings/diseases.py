"""Add tools for disease search and information retrieval from MyDisease.info."""

import asyncio
import logging
from typing import Any, Optional
from urllib.parse import quote
import pandas as pd
from pydantic import BaseModel, Field

MYDISEASE_BASE_URL = "https://mydisease.info/v1"
MYDISEASE_QUERY_URL = f"{MYDISEASE_BASE_URL}/query"
MYDISEASE_GET_URL = f"{MYDISEASE_BASE_URL}/disease"

# internal imports
from .utils import request_api as request_api
from .schema import DiseaseInfo, DiseaseItem


# ================================================
# Schemas
# ================================================

class DiseaseSearchRequest(BaseModel):
    """Search request for diseases."""
    search: Optional[str] = Field(
        default=None,
        description="General search term to query across all fields"
    )
    name: Optional[str] = Field(
        default=None,
        description="Disease name"
    )
    mondo_id: Optional[str] = Field(
        default=None,
        description="MONDO ID (e.g., MONDO:0004992)"
    )
    doid: Optional[str] = Field(
        default=None,
        description="Disease Ontology ID (e.g., DOID:162)"
    )
    omim_id: Optional[str] = Field(
        default=None,
        description="OMIM ID"
    )
    mesh_id: Optional[str] = Field(
        default=None,
        description="MeSH ID"
    )
    limit: int = Field(
        default=100,
        description="Maximum number of results to return (1-1000)"
    )
    skip: int = Field(
        default=0,
        description="Number of results to skip for pagination"
    )


class DiseaseSearchResponse(BaseModel):
    """Response from disease search."""
    results: list[DiseaseItem]
    total: int
    took: int
    max_score: float | None = None


# ================================================
# Helper Functions
# ================================================

def _build_search_query(request: DiseaseSearchRequest) -> dict[str, Any]:
    """Build query parameters for MyDisease.info API."""
    params = {
        "size": min(request.limit, 1000),  # API limit
        "from": request.skip,
        "fields": "_id,name,mondo,definition,synonyms,xrefs",
    }
    
    # Build query string
    query_parts = []
    
    if request.search:
        query_parts.append(request.search)
    
    if request.name:
        query_parts.append(request.name)
    
    if request.mondo_id:
        query_parts.append(f"mondo.id:{request.mondo_id}")
    
    if request.doid:
        query_parts.append(f"disease_ontology.doid:{request.doid}")
    
    if request.omim_id:
        query_parts.append(f"omim.id:{request.omim_id}")
    
    if request.mesh_id:
        query_parts.append(f"mesh.id:{request.mesh_id}")
    
    if query_parts:
        params["q"] = " AND ".join(query_parts)
    else:
        # Default query if no specific terms provided - search for diseases with names
        params["q"] = "_exists_:name"
    
    return params


def _parse_disease_item(hit: dict[str, Any]) -> DiseaseItem:
    """Parse a disease hit from MyDisease.info API response."""
    # Extract name from various sources
    name = hit.get("name")
    if not name and hit.get("mondo") and isinstance(hit["mondo"], dict):
        name = hit["mondo"].get("label")
    
    # Extract MONDO ID
    mondo_id = None
    if hit.get("mondo") and isinstance(hit["mondo"], dict):
        mondo_id = hit["mondo"].get("mondo") or hit["mondo"].get("id")
    
    # Extract DOID
    doid = None
    if hit.get("disease_ontology") and isinstance(hit["disease_ontology"], dict):
        doid = hit["disease_ontology"].get("doid")
    elif hit.get("mondo") and isinstance(hit["mondo"], dict):
        xrefs = hit["mondo"].get("xrefs", {})
        if isinstance(xrefs, dict) and "doid" in xrefs:
            doid_list = xrefs["doid"]
            if isinstance(doid_list, list) and doid_list:
                doid = doid_list[0]
    
    # Extract definition
    definition = hit.get("definition")
    if not definition and hit.get("mondo") and isinstance(hit["mondo"], dict):
        definition = hit["mondo"].get("definition")
    
    # Extract synonyms
    synonyms = hit.get("synonyms", [])
    if not synonyms and hit.get("mondo") and isinstance(hit["mondo"], dict):
        mondo_synonyms = hit["mondo"].get("synonym")
        if isinstance(mondo_synonyms, dict):
            exact = mondo_synonyms.get("exact", [])
            if isinstance(exact, list):
                synonyms = exact
        elif isinstance(mondo_synonyms, list):
            synonyms = mondo_synonyms
    
    return DiseaseItem(
        disease_id=hit.get("_id", ""),
        name=name,
        definition=definition,
        synonyms=synonyms if isinstance(synonyms, list) else [synonyms] if synonyms else [],
        mondo_id=mondo_id,
        doid=doid
    )


# ================================================
# API Functions
# ================================================

async def search_disease_api(request: DiseaseSearchRequest) -> DiseaseSearchResponse:
    """Search MyDisease.info API."""
    params = _build_search_query(request)
    
    # Use requests directly for now to bypass http_client issues
    import requests
    from urllib.parse import urlencode
    
    try:
        response = requests.get(MYDISEASE_QUERY_URL, params=params)
        if response.status_code != 200:
            logging.error(f"Error searching diseases: HTTP {response.status_code}: {response.text}")
            return DiseaseSearchResponse(results=[], total=0, took=0)
        
        response_data = response.json()
        error = None
    except Exception as e:
        logging.error(f"Error searching diseases: {e}")
        return DiseaseSearchResponse(results=[], total=0, took=0)
    
    if not response_data:
        return DiseaseSearchResponse(results=[], total=0, took=0)
    
    # Parse response
    hits = response_data.get("hits", [])
    total = response_data.get("total", 0)
    took = response_data.get("took", 0)
    max_score = response_data.get("max_score")
    
    # Convert hits to DiseaseItem objects
    results = []
    for hit in hits:
        try:
            disease_item = _parse_disease_item(hit)
            results.append(disease_item)
        except Exception as e:
            logging.warning(f"Failed to parse disease hit: {e}")
            continue
    
    return DiseaseSearchResponse(
        results=results,
        total=total,
        took=took,
        max_score=max_score
    )


async def fetch_disease_by_id(disease_id: str) -> DiseaseInfo | None:
    """Fetch detailed disease information by ID."""
    params = {
        "fields": "name,mondo,definition,synonyms,xrefs,phenotypes"
    }
    
    # Build URL with query parameters
    from urllib.parse import urlencode
    query_string = urlencode(params)
    url_with_params = f"{MYDISEASE_GET_URL}/{quote(disease_id, safe='')}?{query_string}"
    
    response, error = await request_api(
        url=url_with_params,
        request={},
        method="GET",
        use_requests=True,
    )
    
    if error or not response:
        return None
    
    try:
        # Extract definition from mondo if available
        if "mondo" in response and isinstance(response["mondo"], dict):
            if (
                "definition" in response["mondo"]
                and "definition" not in response
            ):
                response["definition"] = response["mondo"]["definition"]
            # Extract synonyms from mondo
            if "synonym" in response["mondo"]:
                mondo_synonyms = response["mondo"]["synonym"]
                if isinstance(mondo_synonyms, dict):
                    # Handle exact synonyms
                    exact = mondo_synonyms.get("exact", [])
                    if isinstance(exact, list):
                        response["synonyms"] = exact
                elif isinstance(mondo_synonyms, list):
                    response["synonyms"] = mondo_synonyms
        
        return DiseaseInfo(**response)
    except Exception as e:
        logging.warning(f"Failed to parse disease response: {e}")
        return None


# ================================================
# Main Functions
# ================================================

def search_diseases(
    search: Optional[str] = None,
    name: Optional[str] = None,
    mondo_id: Optional[str] = None,
    doid: Optional[str] = None,
    omim_id: Optional[str] = None,
    mesh_id: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Search for diseases using MyDisease.info API.
    
    Args:
        search: General search term to query across all fields
        name: Disease name
        mondo_id: MONDO ID (e.g., MONDO:0004992)
        doid: Disease Ontology ID (e.g., DOID:162)
        omim_id: OMIM ID
        mesh_id: MeSH ID
        limit: Maximum number of results to return (1-1000)
        skip: Number of results to skip for pagination
        save_path: Path to save the results
    
    Returns:
        Tuple of (DataFrame with results, summary string)
    """
    
    async def _search():
        request = DiseaseSearchRequest(
            search=search,
            name=name,
            mondo_id=mondo_id,
            doid=doid,
            omim_id=omim_id,
            mesh_id=mesh_id,
            limit=limit,
            skip=skip
        )
        
        response = await search_disease_api(request)
        return response
    
    # Run the async function
    response = asyncio.run(_search())
    
    # Convert to DataFrame
    if response.results:
        data = []
        for disease in response.results:
            data.append({
                "disease_id": disease.disease_id,
                "name": disease.name,
                "definition": disease.definition,
                "synonyms": ", ".join(disease.synonyms) if disease.synonyms else "",
                "mondo_id": disease.mondo_id,
                "doid": disease.doid,
            })
        
        output_df = pd.DataFrame(data)
    else:
        output_df = pd.DataFrame()
    
    # Create summary string
    output_str = f"Found {len(response.results)} diseases"
    if response.total > len(response.results):
        output_str += f" (showing {len(response.results)} of {response.total} total)"
    
    if response.took:
        output_str += f" in {response.took}ms"
    
    # Save results if requested
    if save_path and not output_df.empty:
        try:
            output_df.to_csv(save_path, index=False)
            save_result_str = f"Disease search results saved to {save_path}"
        except Exception as e:
            logging.error(f"Error saving results to {save_path}: {e}")
            save_result_str = f"Error saving results to {save_path}: {e}"
        output_str = f"{output_str}\n-----\n{save_result_str}"
    
    return output_df, output_str


def fetch_disease_details_by_ids(
    disease_ids: list[str],
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Fetch detailed disease information by IDs from MyDisease.info.
    
    Args:
        disease_ids: List of disease IDs to fetch details from
        save_path: Path to save the results
    
    Returns:
        Tuple of (DataFrame with results, summary string)
    """
    
    async def _fetch_details():
        tasks = [fetch_disease_by_id(disease_id) for disease_id in disease_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        diseases = []
        for result in results:
            if isinstance(result, DiseaseInfo):
                diseases.append(result)
            elif isinstance(result, Exception):
                logging.warning(f"Failed to fetch disease: {result}")
        
        return diseases
    
    # Run the async function
    diseases = asyncio.run(_fetch_details())
    
    # Convert to DataFrame
    if diseases:
        data = []
        for disease in diseases:
            data.append({
                "disease_id": disease.disease_id,
                "name": disease.name,
                "definition": disease.definition,
                "synonyms": ", ".join(disease.synonyms) if disease.synonyms else "",
                "mondo": str(disease.mondo) if disease.mondo else "",
                "xrefs": str(disease.xrefs) if disease.xrefs else "",
                "phenotypes": str(disease.phenotypes) if disease.phenotypes else "",
            })
        
        output_df = pd.DataFrame(data)
    else:
        output_df = pd.DataFrame()
    
    # Create summary string
    output_str = f"Fetched details for {len(diseases)} diseases out of {len(disease_ids)} requested"
    
    # Save results if requested
    if save_path and not output_df.empty:
        try:
            output_df.to_csv(save_path, index=False)
            save_result_str = f"Disease details saved to {save_path}"
        except Exception as e:
            logging.error(f"Error saving results to {save_path}: {e}")
            save_result_str = f"Error saving results to {save_path}: {e}"
        output_str = f"{output_str}\n-----\n{save_result_str}"
    
    return output_df, output_str