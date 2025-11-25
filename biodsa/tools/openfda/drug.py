"""OpenFDA Drug API client.

This module provides functions to search and retrieve drug information from the
OpenFDA Drugs@FDA database.
"""

import logging
import requests
import pandas as pd
from typing import Optional, Dict, Any, List
from urllib.parse import quote
from pydantic import BaseModel, Field

# ================================================
# Constants
# ================================================

OPENFDA_BASE_URL = "https://api.fda.gov/drug/drugsfda.json"

# ================================================
# Schemas
# ================================================

class OpenFDADrugSearchRequest(BaseModel):
    """Search request for OpenFDA Drugs@FDA API."""
    
    # General search
    search_term: Optional[str] = Field(
        default=None,
        description="General search term to query across all fields"
    )
    
    # Application fields
    application_number: Optional[str] = Field(
        default=None,
        description="NDA, ANDA, or BLA number"
    )
    
    # Product fields
    brand_name: Optional[str] = Field(
        default=None,
        description="Brand or trade name of the drug product"
    )
    generic_name: Optional[str] = Field(
        default=None,
        description="Generic name(s) of the drug product"
    )
    manufacturer_name: Optional[str] = Field(
        default=None,
        description="Name of manufacturer or company that makes this drug product"
    )
    marketing_status: Optional[str] = Field(
        default=None,
        description="Marketing status (e.g., 'Prescription', 'Discontinued', 'OTC')"
    )
    product_number: Optional[str] = Field(
        default=None,
        description="Product number (NDA, ANDA, or BLA)"
    )
    route: Optional[str] = Field(
        default=None,
        description="Route of administration (e.g., 'ORAL', 'INTRAVENOUS')"
    )
    substance_name: Optional[str] = Field(
        default=None,
        description="Active ingredient name"
    )
    
    # Pagination
    limit: int = Field(
        default=100,
        description="Maximum number of results to return (1-1000)"
    )
    skip: int = Field(
        default=0,
        description="Number of results to skip for pagination"
    )


class OpenFDADrugItem(BaseModel):
    """A drug item from OpenFDA search results."""
    application_number: Optional[str] = None
    brand_name: Optional[List[str]] = None
    generic_name: Optional[List[str]] = None
    manufacturer_name: Optional[List[str]] = None
    marketing_status: Optional[str] = None
    product_number: Optional[List[str]] = None
    route: Optional[List[str]] = None
    substance_name: Optional[List[str]] = None
    dosage_form: Optional[str] = None
    application_type: Optional[str] = None
    sponsor_name: Optional[str] = None


class OpenFDADrugSearchResponse(BaseModel):
    """Response from OpenFDA drug search."""
    results: List[OpenFDADrugItem]
    total: int = 0


# ================================================
# Helper Functions
# ================================================

def _build_search_query(request: OpenFDADrugSearchRequest) -> Dict[str, Any]:
    """Build query parameters for OpenFDA API.
    
    Args:
        request: The search request object
        
    Returns:
        Dictionary of query parameters
    """
    params = {
        "limit": min(request.limit, 1000),  # API limit
        "skip": request.skip,
    }
    
    # Build search query string
    query_parts = []
    
    if request.search_term:
        # General search across all fields
        query_parts.append(request.search_term)
    
    if request.application_number:
        query_parts.append(f'application_number:"{quote(request.application_number)}"')
    
    if request.brand_name:
        query_parts.append(f'products.brand_name:"{quote(request.brand_name)}"')
    
    if request.generic_name:
        query_parts.append(f'products.generic_name:"{quote(request.generic_name)}"')
    
    if request.manufacturer_name:
        query_parts.append(f'products.manufacturer_name:"{quote(request.manufacturer_name)}"')
    
    if request.marketing_status:
        query_parts.append(f'products.marketing_status:"{quote(request.marketing_status)}"')
    
    if request.product_number:
        query_parts.append(f'products.product_number:"{quote(request.product_number)}"')
    
    if request.route:
        query_parts.append(f'products.route:"{quote(request.route)}"')
    
    if request.substance_name:
        query_parts.append(f'openfda.substance_name:"{quote(request.substance_name)}"')
    
    if query_parts:
        # Join with AND to make the search more specific
        params["search"] = " AND ".join(query_parts)
    else:
        # If no search terms provided, search for all drugs
        params["search"] = "*"
    
    return params


def _parse_drug_item(result: Dict[str, Any]) -> OpenFDADrugItem:
    """Parse a drug result from OpenFDA API response.
    
    Args:
        result: Raw result dictionary from API
        
    Returns:
        Parsed OpenFDADrugItem
    """
    # Extract application-level fields
    application_number = result.get("application_number")
    sponsor_name = result.get("sponsor_name")
    
    # Determine application type from number prefix
    application_type = None
    if application_number:
        if application_number.startswith("NDA"):
            application_type = "NDA"
        elif application_number.startswith("ANDA"):
            application_type = "ANDA"
        elif application_number.startswith("BLA"):
            application_type = "BLA"
    
    # Extract product-level fields (products is an array)
    products = result.get("products", [])
    
    brand_names = []
    generic_names = []
    manufacturer_names = []
    marketing_statuses = []
    product_numbers = []
    routes = []
    dosage_forms = []
    
    for product in products:
        if product.get("brand_name"):
            brand_names.append(product["brand_name"])
        if product.get("generic_name"):
            generic_names.append(product["generic_name"])
        if product.get("manufacturer_name"):
            manufacturer_names.append(product["manufacturer_name"])
        if product.get("marketing_status"):
            marketing_statuses.append(product["marketing_status"])
        if product.get("product_number"):
            product_numbers.append(product["product_number"])
        if product.get("route"):
            # Route is an array
            routes.extend(product["route"])
        if product.get("dosage_form"):
            dosage_forms.append(product["dosage_form"])
    
    # Extract substance names from openfda section
    substance_names = []
    openfda = result.get("openfda", {})
    if openfda.get("substance_name"):
        substance_names = openfda["substance_name"]
    
    # Get the most common marketing status
    marketing_status = marketing_statuses[0] if marketing_statuses else None
    
    # Get the first dosage form
    dosage_form = dosage_forms[0] if dosage_forms else None
    
    return OpenFDADrugItem(
        application_number=application_number,
        application_type=application_type,
        sponsor_name=sponsor_name,
        brand_name=list(set(brand_names)) if brand_names else None,
        generic_name=list(set(generic_names)) if generic_names else None,
        manufacturer_name=list(set(manufacturer_names)) if manufacturer_names else None,
        marketing_status=marketing_status,
        product_number=list(set(product_numbers)) if product_numbers else None,
        route=list(set(routes)) if routes else None,
        substance_name=substance_names if substance_names else None,
        dosage_form=dosage_form,
    )


# ================================================
# API Functions
# ================================================

def search_openfda_drugs(
    search_term: Optional[str] = None,
    application_number: Optional[str] = None,
    brand_name: Optional[str] = None,
    generic_name: Optional[str] = None,
    manufacturer_name: Optional[str] = None,
    marketing_status: Optional[str] = None,
    product_number: Optional[str] = None,
    route: Optional[str] = None,
    substance_name: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Search for drugs using OpenFDA Drugs@FDA API.
    
    Args:
        search_term: General search term to query across all fields
        application_number: NDA, ANDA, or BLA number
        brand_name: Brand or trade name of the drug product
        generic_name: Generic name(s) of the drug product
        manufacturer_name: Name of manufacturer or company
        marketing_status: Marketing status (e.g., 'Prescription', 'Discontinued', 'OTC')
        product_number: Product number
        route: Route of administration (e.g., 'ORAL', 'INTRAVENOUS')
        substance_name: Active ingredient name
        limit: Maximum number of results to return (1-1000)
        skip: Number of results to skip for pagination
        save_path: Path to save the results as CSV
    
    Returns:
        Tuple of (DataFrame with results, summary string)
        
    Examples:
        >>> # Search for discontinued drugs
        >>> df, summary = search_openfda_drugs(marketing_status="Discontinued", limit=5)
        
        >>> # Search by brand name
        >>> df, summary = search_openfda_drugs(brand_name="Aspirin", limit=10)
        
        >>> # Search by active ingredient
        >>> df, summary = search_openfda_drugs(substance_name="ACETYLSALICYLIC ACID")
    """
    # Create request object
    request = OpenFDADrugSearchRequest(
        search_term=search_term,
        application_number=application_number,
        brand_name=brand_name,
        generic_name=generic_name,
        manufacturer_name=manufacturer_name,
        marketing_status=marketing_status,
        product_number=product_number,
        route=route,
        substance_name=substance_name,
        limit=limit,
        skip=skip,
    )
    
    # Build query parameters
    params = _build_search_query(request)
    
    try:
        # Make API request
        response = requests.get(OPENFDA_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error searching OpenFDA drugs: {e}")
        return pd.DataFrame(), f"Error searching OpenFDA drugs: {e}"
    except ValueError as e:
        logging.error(f"Error parsing OpenFDA response: {e}")
        return pd.DataFrame(), f"Error parsing OpenFDA response: {e}"
    
    # Parse response
    results = response_data.get("results", [])
    
    # Get metadata
    meta = response_data.get("meta", {})
    total = meta.get("results", {}).get("total", len(results))
    
    # Parse drug items
    drug_items = []
    for result in results:
        try:
            drug_item = _parse_drug_item(result)
            drug_items.append(drug_item)
        except Exception as e:
            logging.warning(f"Failed to parse drug result: {e}")
            continue
    
    # Convert to DataFrame
    if drug_items:
        data = []
        for drug in drug_items:
            data.append({
                "application_number": drug.application_number,
                "application_type": drug.application_type,
                "sponsor_name": drug.sponsor_name,
                "brand_name": ", ".join(drug.brand_name) if drug.brand_name else "",
                "generic_name": ", ".join(drug.generic_name) if drug.generic_name else "",
                "manufacturer_name": ", ".join(drug.manufacturer_name) if drug.manufacturer_name else "",
                "substance_name": ", ".join(drug.substance_name) if drug.substance_name else "",
                "marketing_status": drug.marketing_status,
                "dosage_form": drug.dosage_form,
                "route": ", ".join(drug.route) if drug.route else "",
                "product_number": ", ".join(drug.product_number) if drug.product_number else "",
            })
        
        output_df = pd.DataFrame(data)
    else:
        output_df = pd.DataFrame()
    
    # Create summary string
    output_str = f"Found {len(drug_items)} drugs"
    if total > len(drug_items):
        output_str += f" (showing {len(drug_items)} of {total} total)"
    
    # Save results if requested
    if save_path and not output_df.empty:
        try:
            output_df.to_csv(save_path, index=False)
            save_result_str = f"OpenFDA drug search results saved to {save_path}"
        except Exception as e:
            logging.error(f"Error saving results to {save_path}: {e}")
            save_result_str = f"Error saving results to {save_path}: {e}"
        output_str = f"{output_str}\n-----\n{save_result_str}"
    
    return output_df, output_str


def fetch_openfda_drug_by_application(
    application_number: str,
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Fetch detailed drug information by application number from OpenFDA.
    
    Args:
        application_number: The NDA, ANDA, or BLA application number
        save_path: Path to save the results as CSV
    
    Returns:
        Tuple of (DataFrame with results, summary string)
        
    Examples:
        >>> # Fetch by application number
        >>> df, summary = fetch_openfda_drug_by_application("NDA021462")
    """
    try:
        # Search for the specific application number
        params = {
            "search": f'application_number:"{application_number}"',
            "limit": 1,
        }
        
        response = requests.get(OPENFDA_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching OpenFDA drug: {e}")
        return pd.DataFrame(), f"Error fetching OpenFDA drug: {e}"
    except ValueError as e:
        logging.error(f"Error parsing OpenFDA response: {e}")
        return pd.DataFrame(), f"Error parsing OpenFDA response: {e}"
    
    # Parse response
    results = response_data.get("results", [])
    
    if not results:
        return pd.DataFrame(), f"No drug found with application number: {application_number}"
    
    # Parse the drug item
    try:
        drug_item = _parse_drug_item(results[0])
    except Exception as e:
        logging.error(f"Failed to parse drug result: {e}")
        return pd.DataFrame(), f"Failed to parse drug result: {e}"
    
    # Convert to DataFrame
    data = [{
        "application_number": drug_item.application_number,
        "application_type": drug_item.application_type,
        "sponsor_name": drug_item.sponsor_name,
        "brand_name": ", ".join(drug_item.brand_name) if drug_item.brand_name else "",
        "generic_name": ", ".join(drug_item.generic_name) if drug_item.generic_name else "",
        "manufacturer_name": ", ".join(drug_item.manufacturer_name) if drug_item.manufacturer_name else "",
        "substance_name": ", ".join(drug_item.substance_name) if drug_item.substance_name else "",
        "marketing_status": drug_item.marketing_status,
        "dosage_form": drug_item.dosage_form,
        "route": ", ".join(drug_item.route) if drug_item.route else "",
        "product_number": ", ".join(drug_item.product_number) if drug_item.product_number else "",
    }]
    
    output_df = pd.DataFrame(data)
    
    # Create summary string
    output_str = f"Found drug with application number: {application_number}"
    
    # Save results if requested
    if save_path:
        try:
            output_df.to_csv(save_path, index=False)
            save_result_str = f"OpenFDA drug details saved to {save_path}"
        except Exception as e:
            logging.error(f"Error saving results to {save_path}: {e}")
            save_result_str = f"Error saving results to {save_path}: {e}"
        output_str = f"{output_str}\n-----\n{save_result_str}"
    
    return output_df, output_str


# ================================================
# Convenience Functions
# ================================================

def search_drugs_by_status(
    marketing_status: str,
    limit: int = 100,
    skip: int = 0,
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Search for drugs by marketing status.
    
    Args:
        marketing_status: Marketing status (e.g., 'Prescription', 'Discontinued', 'OTC')
        limit: Maximum number of results to return
        skip: Number of results to skip for pagination
        save_path: Path to save the results
    
    Returns:
        Tuple of (DataFrame with results, summary string)
        
    Examples:
        >>> # Search for discontinued drugs
        >>> df, summary = search_drugs_by_status("Discontinued", limit=50)
    """
    return search_openfda_drugs(
        marketing_status=marketing_status,
        limit=limit,
        skip=skip,
        save_path=save_path,
    )


def search_drugs_by_ingredient(
    substance_name: str,
    limit: int = 100,
    skip: int = 0,
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Search for drugs by active ingredient/substance name.
    
    Args:
        substance_name: Active ingredient name
        limit: Maximum number of results to return
        skip: Number of results to skip for pagination
        save_path: Path to save the results
    
    Returns:
        Tuple of (DataFrame with results, summary string)
        
    Examples:
        >>> # Search by ingredient
        >>> df, summary = search_drugs_by_ingredient("ACETYLSALICYLIC ACID")
    """
    return search_openfda_drugs(
        substance_name=substance_name,
        limit=limit,
        skip=skip,
        save_path=save_path,
    )


def search_drugs_by_route(
    route: str,
    limit: int = 100,
    skip: int = 0,
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Search for drugs by route of administration.
    
    Args:
        route: Route of administration (e.g., 'ORAL', 'INTRAVENOUS', 'TOPICAL')
        limit: Maximum number of results to return
        skip: Number of results to skip for pagination
        save_path: Path to save the results
    
    Returns:
        Tuple of (DataFrame with results, summary string)
        
    Examples:
        >>> # Search for intravenous drugs
        >>> df, summary = search_drugs_by_route("INTRAVENOUS", limit=50)
    """
    return search_openfda_drugs(
        route=route,
        limit=limit,
        skip=skip,
        save_path=save_path,
    )
