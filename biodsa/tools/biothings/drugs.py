"""Add tools for drug search and information retrieval from MyChem.info."""

import asyncio
import logging
from typing import Any, Optional
from urllib.parse import quote
import pandas as pd
from pydantic import BaseModel, Field

# internal imports
MYCHEM_BASE_URL = "https://mychem.info/v1"
MYCHEM_QUERY_URL = f"{MYCHEM_BASE_URL}/query"
MYCHEM_GET_URL = f"{MYCHEM_BASE_URL}/chem"

from .utils import request_api as request_api
from .schema import DrugInfo, DrugItem


# ================================================
# Schemas
# ================================================

class DrugSearchRequest(BaseModel):
    """Search request for drugs."""
    search: Optional[str] = Field(
        default=None,
        description="General search term to query across all fields"
    )
    name: Optional[str] = Field(
        default=None,
        description="Drug name"
    )
    drugbank_id: Optional[str] = Field(
        default=None,
        description="DrugBank ID (e.g., DB00001)"
    )
    chebi_id: Optional[str] = Field(
        default=None,
        description="ChEBI ID (e.g., CHEBI:15365)"
    )
    chembl_id: Optional[str] = Field(
        default=None,
        description="ChEMBL ID (e.g., CHEMBL25)"
    )
    pubchem_cid: Optional[str] = Field(
        default=None,
        description="PubChem CID"
    )
    inchikey: Optional[str] = Field(
        default=None,
        description="InChI Key"
    )
    limit: int = Field(
        default=100,
        description="Maximum number of results to return (1-1000)"
    )
    skip: int = Field(
        default=0,
        description="Number of results to skip for pagination"
    )


class DrugSearchResponse(BaseModel):
    """Response from drug search."""
    results: list[DrugItem]
    total: int
    took: int
    max_score: float | None = None


# ================================================
# Helper Functions
# ================================================

def _build_search_query(request: DrugSearchRequest) -> dict[str, Any]:
    """Build query parameters for MyChem.info API."""
    params = {
        "size": min(request.limit, 1000),  # API limit
        "from": request.skip,
        # Don't specify fields to get all available data
    }
    
    # Build query string
    query_parts = []
    
    if request.search:
        query_parts.append(request.search)
    
    if request.name:
        query_parts.append(request.name)
    
    if request.drugbank_id:
        query_parts.append(f"drugbank.id:{quote(request.drugbank_id)}")
    
    if request.chebi_id:
        query_parts.append(f"chebi.id:{quote(request.chebi_id)}")
    
    if request.chembl_id:
        query_parts.append(f"chembl.molecule_chembl_id:{quote(request.chembl_id)}")
    
    if request.pubchem_cid:
        query_parts.append(f"pubchem.cid:{request.pubchem_cid}")
    
    if request.inchikey:
        query_parts.append(f"inchikey:{quote(request.inchikey)}")
    
    if query_parts:
        params["q"] = " AND ".join(query_parts)
    else:
        # Default query if no specific terms provided - search for drugs with names
        params["q"] = "_exists_:name"
    
    return params


def _parse_drug_item(hit: dict[str, Any]) -> DrugItem:
    """Parse a drug hit from MyChem.info API response."""
    # Extract fields from nested structures
    drugbank_id = None
    chebi_id = None
    chembl_id = None
    pubchem_cid = None
    tradename = []
    
    if hit.get("drugbank") and isinstance(hit["drugbank"], dict):
        drugbank_id = hit["drugbank"].get("id")
        products = hit["drugbank"].get("products", {})
        if isinstance(products, dict) and "name" in products:
            names = products["name"]
            if isinstance(names, list):
                tradename = names
            elif isinstance(names, str):
                tradename = [names]
    
    if hit.get("chebi") and isinstance(hit["chebi"], dict):
        chebi_id = hit["chebi"].get("id")
    
    if hit.get("chembl") and isinstance(hit["chembl"], dict):
        chembl_id = hit["chembl"].get("molecule_chembl_id")
    
    if hit.get("pubchem") and isinstance(hit["pubchem"], dict):
        pubchem_cid = str(hit["pubchem"].get("cid", ""))
    
    # Get name from various sources
    name = hit.get("name")
    
    # Check NDC data for names
    if not name and hit.get("ndc"):
        ndc_data = hit["ndc"]
        if isinstance(ndc_data, list) and ndc_data:
            ndc_item = ndc_data[0]
            name = ndc_item.get("nonproprietaryname") or ndc_item.get("proprietaryname") or ndc_item.get("substancename")
        elif isinstance(ndc_data, dict):
            name = ndc_data.get("nonproprietaryname") or ndc_data.get("proprietaryname") or ndc_data.get("substancename")
    
    # Check other sources
    if not name and hit.get("drugbank") and isinstance(hit["drugbank"], dict):
        name = hit["drugbank"].get("name")
    if not name and hit.get("chebi") and isinstance(hit["chebi"], dict):
        name = hit["chebi"].get("name")
    if not name and hit.get("chembl") and isinstance(hit["chembl"], dict):
        name = hit["chembl"].get("pref_name")
    if not name and hit.get("unii") and isinstance(hit["unii"], dict):
        name = hit["unii"].get("display_name")
    
    return DrugItem(
        drug_id=hit.get("_id", ""),
        name=name,
        tradename=tradename,
        drugbank_id=drugbank_id,
        chebi_id=chebi_id,
        chembl_id=chembl_id,
        pubchem_cid=pubchem_cid,
        inchikey=hit.get("inchikey"),
        formula=hit.get("formula"),
        description=None  # Will be filled in detailed fetch
    )


# ================================================
# API Functions
# ================================================

async def search_drug_api(request: DrugSearchRequest) -> DrugSearchResponse:
    """Search MyChem.info API."""
    params = _build_search_query(request)
    
    # Use requests directly for consistency
    import requests
    
    try:
        response = requests.get(MYCHEM_QUERY_URL, params=params)
        if response.status_code != 200:
            logging.error(f"Error searching drugs: HTTP {response.status_code}: {response.text}")
            return DrugSearchResponse(results=[], total=0, took=0)
        
        response_data = response.json()
        error = None
    except Exception as e:
        logging.error(f"Error searching drugs: {e}")
        return DrugSearchResponse(results=[], total=0, took=0)
    
    if not response_data:
        return DrugSearchResponse(results=[], total=0, took=0)
    
    # Parse response
    hits = response_data.get("hits", [])
    total = response_data.get("total", 0)
    took = response_data.get("took", 0)
    max_score = response_data.get("max_score")
    
    # Convert hits to DrugItem objects
    results = []
    for hit in hits:
        try:
            drug_item = _parse_drug_item(hit)
            results.append(drug_item)
        except Exception as e:
            logging.warning(f"Failed to parse drug hit: {e}")
            continue
    
    return DrugSearchResponse(
        results=results,
        total=total,
        took=took,
        max_score=max_score
    )


async def fetch_drug_by_id(drug_id: str) -> DrugInfo | None:
    """Fetch detailed drug information by ID."""
    params = {
        "fields": "name,drugbank,chebi,chembl,pubchem,unii,inchikey,formula,description,indication,pharmacology,mechanism_of_action"
    }
    
    response, error = await request_api(
        url=f"{MYCHEM_GET_URL}/{quote(drug_id, safe='')}",
        request=params,
        method="GET",
        use_requests=True,
    )
    
    if error or not response:
        return None
    
    try:
        # Handle array response (multiple results)
        if isinstance(response, list):
            if not response:
                return None
            # Take the first result
            response = response[0]
        
        # Extract fields from nested structures
        _extract_drugbank_fields(response)
        _extract_chebi_fields(response)
        _extract_chembl_fields(response)
        _extract_pubchem_fields(response)
        _extract_unii_fields(response)
        
        return DrugInfo(**response)
    except Exception as e:
        logging.warning(f"Failed to parse drug response: {e}")
        return None


def _extract_drugbank_fields(response: dict[str, Any]) -> None:
    """Extract DrugBank fields from response."""
    if "drugbank" in response and isinstance(response["drugbank"], dict):
        db = response["drugbank"]
        response["drugbank_id"] = db.get("id")
        response["name"] = response.get("name") or db.get("name")
        response["tradename"] = db.get("products", {}).get("name", [])
        if isinstance(response["tradename"], str):
            response["tradename"] = [response["tradename"]]
        response["indication"] = db.get("indication")
        response["mechanism_of_action"] = db.get("mechanism_of_action")
        response["description"] = db.get("description")


def _extract_chebi_fields(response: dict[str, Any]) -> None:
    """Extract ChEBI fields from response."""
    if "chebi" in response and isinstance(response["chebi"], dict):
        response["chebi_id"] = response["chebi"].get("id")
        if not response.get("name"):
            response["name"] = response["chebi"].get("name")


def _extract_chembl_fields(response: dict[str, Any]) -> None:
    """Extract ChEMBL fields from response."""
    if "chembl" in response and isinstance(response["chembl"], dict):
        response["chembl_id"] = response["chembl"].get("molecule_chembl_id")
        if not response.get("name"):
            response["name"] = response["chembl"].get("pref_name")


def _extract_pubchem_fields(response: dict[str, Any]) -> None:
    """Extract PubChem fields from response."""
    if "pubchem" in response and isinstance(response["pubchem"], dict):
        response["pubchem_cid"] = str(response["pubchem"].get("cid", ""))


def _extract_unii_fields(response: dict[str, Any]) -> None:
    """Extract UNII fields from response."""
    if "unii" in response and isinstance(response["unii"], dict):
        unii_data = response["unii"]
        # Set UNII code
        response["unii"] = unii_data.get("unii", "")
        # Use display name as drug name if not already set
        if not response.get("name") and unii_data.get("display_name"):
            response["name"] = unii_data["display_name"]
        # Use NCIT description if no description
        if not response.get("description") and unii_data.get("ncit_description"):
            response["description"] = unii_data["ncit_description"]


# ================================================
# Main Functions
# ================================================

def search_drugs(
    search: Optional[str] = None,
    name: Optional[str] = None,
    drugbank_id: Optional[str] = None,
    chebi_id: Optional[str] = None,
    chembl_id: Optional[str] = None,
    pubchem_cid: Optional[str] = None,
    inchikey: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Search for drugs using MyChem.info API.
    
    Args:
        search: General search term to query across all fields
        name: Drug name
        drugbank_id: DrugBank ID (e.g., DB00001)
        chebi_id: ChEBI ID (e.g., CHEBI:15365)
        chembl_id: ChEMBL ID (e.g., CHEMBL25)
        pubchem_cid: PubChem CID
        inchikey: InChI Key
        limit: Maximum number of results to return (1-1000)
        skip: Number of results to skip for pagination
        save_path: Path to save the results
    
    Returns:
        Tuple of (DataFrame with results, summary string)
    """
    
    async def _search():
        request = DrugSearchRequest(
            search=search,
            name=name,
            drugbank_id=drugbank_id,
            chebi_id=chebi_id,
            chembl_id=chembl_id,
            pubchem_cid=pubchem_cid,
            inchikey=inchikey,
            limit=limit,
            skip=skip
        )
        
        response = await search_drug_api(request)
        return response
    
    # Run the async function
    response = asyncio.run(_search())
    
    # Convert to DataFrame
    if response.results:
        data = []
        for drug in response.results:
            data.append({
                "drug_id": drug.drug_id,
                "name": drug.name,
                "tradename": ", ".join(drug.tradename) if drug.tradename else "",
                "drugbank_id": drug.drugbank_id,
                "chebi_id": drug.chebi_id,
                "chembl_id": drug.chembl_id,
                "pubchem_cid": drug.pubchem_cid,
                "inchikey": drug.inchikey,
                "formula": drug.formula,
            })
        
        output_df = pd.DataFrame(data)
    else:
        output_df = pd.DataFrame()
    
    # Create summary string
    output_str = f"Found {len(response.results)} drugs"
    if response.total > len(response.results):
        output_str += f" (showing {len(response.results)} of {response.total} total)"
    
    if response.took:
        output_str += f" in {response.took}ms"
    
    # Save results if requested
    if save_path and not output_df.empty:
        try:
            output_df.to_csv(save_path, index=False)
            save_result_str = f"Drug search results saved to {save_path}"
        except Exception as e:
            logging.error(f"Error saving results to {save_path}: {e}")
            save_result_str = f"Error saving results to {save_path}: {e}"
        output_str = f"{output_str}\n-----\n{save_result_str}"
    
    return output_df, output_str


def fetch_drug_details_by_ids(
    drug_ids: list[str],
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Fetch detailed drug information by IDs from MyChem.info.
    
    Args:
        drug_ids: List of drug IDs to fetch details from
        save_path: Path to save the results
    
    Returns:
        Tuple of (DataFrame with results, summary string)
    """
    
    async def _fetch_details():
        tasks = [fetch_drug_by_id(drug_id) for drug_id in drug_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        drugs = []
        for result in results:
            if isinstance(result, DrugInfo):
                drugs.append(result)
            elif isinstance(result, Exception):
                logging.warning(f"Failed to fetch drug: {result}")
        
        return drugs
    
    # Run the async function
    drugs = asyncio.run(_fetch_details())
    
    # Convert to DataFrame
    if drugs:
        data = []
        for drug in drugs:
            data.append({
                "drug_id": drug.drug_id,
                "name": drug.name,
                "tradename": ", ".join(drug.tradename) if drug.tradename else "",
                "drugbank_id": drug.drugbank_id,
                "chebi_id": drug.chebi_id,
                "chembl_id": drug.chembl_id,
                "pubchem_cid": drug.pubchem_cid,
                "unii": str(drug.unii) if drug.unii else "",
                "inchikey": drug.inchikey,
                "formula": drug.formula,
                "description": drug.description,
                "indication": drug.indication,
                "mechanism_of_action": drug.mechanism_of_action,
                "pharmacology": str(drug.pharmacology) if drug.pharmacology else "",
            })
        
        output_df = pd.DataFrame(data)
    else:
        output_df = pd.DataFrame()
    
    # Create summary string
    output_str = f"Fetched details for {len(drugs)} drugs out of {len(drug_ids)} requested"
    
    # Save results if requested
    if save_path and not output_df.empty:
        try:
            output_df.to_csv(save_path, index=False)
            save_result_str = f"Drug details saved to {save_path}"
        except Exception as e:
            logging.error(f"Error saving results to {save_path}: {e}")
            save_result_str = f"Error saving results to {save_path}: {e}"
        output_str = f"{output_str}\n-----\n{save_result_str}"
    
    return output_df, output_str