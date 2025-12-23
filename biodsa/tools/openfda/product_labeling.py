"""OpenFDA Product Labeling API client.

This module provides functions to search and retrieve drug product labeling information
from the OpenFDA Drug Labeling database. This includes package inserts, prescribing information,
warnings, indications, dosage, and other label content.
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

OPENFDA_LABEL_BASE_URL = "https://api.fda.gov/drug/label.json"

# ================================================
# Schemas
# ================================================

class OpenFDALabelSearchRequest(BaseModel):
    """Search request for OpenFDA Drug Labeling API."""
    
    # General search
    search_term: Optional[str] = Field(
        default=None,
        description="General search term to query across all fields"
    )
    
    # Label content fields
    indications_and_usage: Optional[str] = Field(
        default=None,
        description="Search in indications and usage section"
    )
    dosage_and_administration: Optional[str] = Field(
        default=None,
        description="Search in dosage and administration section"
    )
    contraindications: Optional[str] = Field(
        default=None,
        description="Search in contraindications section"
    )
    warnings: Optional[str] = Field(
        default=None,
        description="Search in warnings section"
    )
    adverse_reactions: Optional[str] = Field(
        default=None,
        description="Search in adverse reactions section"
    )
    drug_interactions: Optional[str] = Field(
        default=None,
        description="Search in drug interactions section"
    )
    boxed_warning: Optional[str] = Field(
        default=None,
        description="Search in boxed warning (black box) section"
    )
    mechanism_of_action: Optional[str] = Field(
        default=None,
        description="Search in mechanism of action section"
    )
    pharmacokinetics: Optional[str] = Field(
        default=None,
        description="Search in pharmacokinetics section"
    )
    pharmacodynamics: Optional[str] = Field(
        default=None,
        description="Search in pharmacodynamics section"
    )
    clinical_pharmacology: Optional[str] = Field(
        default=None,
        description="Search in clinical pharmacology section"
    )
    clinical_studies: Optional[str] = Field(
        default=None,
        description="Search in clinical studies section"
    )
    overdosage: Optional[str] = Field(
        default=None,
        description="Search in overdosage section"
    )
    description: Optional[str] = Field(
        default=None,
        description="Search in description section"
    )
    
    # OpenFDA standardized fields
    brand_name: Optional[str] = Field(
        default=None,
        description="Brand or trade name of the drug product"
    )
    generic_name: Optional[str] = Field(
        default=None,
        description="Generic name(s) of the drug product"
    )
    substance_name: Optional[str] = Field(
        default=None,
        description="Active ingredient name"
    )
    manufacturer_name: Optional[str] = Field(
        default=None,
        description="Name of manufacturer or company"
    )
    product_type: Optional[str] = Field(
        default=None,
        description="Type of drug product"
    )
    route: Optional[str] = Field(
        default=None,
        description="Route of administration"
    )
    application_number: Optional[str] = Field(
        default=None,
        description="NDA, ANDA, or BLA number"
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


class OpenFDALabelItem(BaseModel):
    """A drug label item from OpenFDA search results."""
    # IDs
    id: Optional[str] = None
    set_id: Optional[str] = None
    version: Optional[str] = None
    effective_time: Optional[str] = None
    
    # OpenFDA standardized fields
    brand_name: Optional[List[str]] = None
    generic_name: Optional[List[str]] = None
    substance_name: Optional[List[str]] = None
    manufacturer_name: Optional[List[str]] = None
    product_type: Optional[List[str]] = None
    route: Optional[List[str]] = None
    application_number: Optional[List[str]] = None
    
    # Label content fields (as arrays of strings)
    indications_and_usage: Optional[List[str]] = None
    dosage_and_administration: Optional[List[str]] = None
    contraindications: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    adverse_reactions: Optional[List[str]] = None
    drug_interactions: Optional[List[str]] = None
    boxed_warning: Optional[List[str]] = None
    mechanism_of_action: Optional[List[str]] = None
    pharmacokinetics: Optional[List[str]] = None
    pharmacodynamics: Optional[List[str]] = None
    clinical_pharmacology: Optional[List[str]] = None
    clinical_studies: Optional[List[str]] = None
    overdosage: Optional[List[str]] = None
    description: Optional[List[str]] = None
    how_supplied: Optional[List[str]] = None
    storage_and_handling: Optional[List[str]] = None
    use_in_specific_populations: Optional[List[str]] = None
    pregnancy: Optional[List[str]] = None
    pediatric_use: Optional[List[str]] = None
    geriatric_use: Optional[List[str]] = None
    nursing_mothers: Optional[List[str]] = None


class OpenFDALabelSearchResponse(BaseModel):
    """Response from OpenFDA label search."""
    results: List[OpenFDALabelItem]
    total: int = 0


# ================================================
# Helper Functions
# ================================================

def _build_label_search_query(request: OpenFDALabelSearchRequest) -> Dict[str, Any]:
    """Build query parameters for OpenFDA Label API.
    
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
    
    # Label content fields
    if request.indications_and_usage:
        query_parts.append(f'indications_and_usage:"{request.indications_and_usage}"')
    
    if request.dosage_and_administration:
        query_parts.append(f'dosage_and_administration:"{request.dosage_and_administration}"')
    
    if request.contraindications:
        query_parts.append(f'contraindications:"{request.contraindications}"')
    
    if request.warnings:
        query_parts.append(f'warnings:"{request.warnings}"')
    
    if request.adverse_reactions:
        query_parts.append(f'adverse_reactions:"{request.adverse_reactions}"')
    
    if request.drug_interactions:
        query_parts.append(f'drug_interactions:"{request.drug_interactions}"')
    
    if request.boxed_warning:
        query_parts.append(f'boxed_warning:"{request.boxed_warning}"')
    
    if request.mechanism_of_action:
        query_parts.append(f'mechanism_of_action:"{request.mechanism_of_action}"')
    
    if request.pharmacokinetics:
        query_parts.append(f'pharmacokinetics:"{request.pharmacokinetics}"')
    
    if request.pharmacodynamics:
        query_parts.append(f'pharmacodynamics:"{request.pharmacodynamics}"')
    
    if request.clinical_pharmacology:
        query_parts.append(f'clinical_pharmacology:"{request.clinical_pharmacology}"')
    
    if request.clinical_studies:
        query_parts.append(f'clinical_studies:"{request.clinical_studies}"')
    
    if request.overdosage:
        query_parts.append(f'overdosage:"{request.overdosage}"')
    
    if request.description:
        query_parts.append(f'description:"{request.description}"')
    
    # OpenFDA standardized fields
    if request.brand_name:
        query_parts.append(f'openfda.brand_name:"{quote(request.brand_name)}"')
    
    if request.generic_name:
        query_parts.append(f'openfda.generic_name:"{quote(request.generic_name)}"')
    
    if request.substance_name:
        query_parts.append(f'openfda.substance_name:"{quote(request.substance_name)}"')
    
    if request.manufacturer_name:
        query_parts.append(f'openfda.manufacturer_name:"{quote(request.manufacturer_name)}"')
    
    if request.product_type:
        query_parts.append(f'openfda.product_type:"{quote(request.product_type)}"')
    
    if request.route:
        query_parts.append(f'openfda.route:"{quote(request.route)}"')
    
    if request.application_number:
        query_parts.append(f'openfda.application_number:"{quote(request.application_number)}"')
    
    if query_parts:
        # Join with AND to make the search more specific
        params["search"] = " AND ".join(query_parts)
    else:
        # If no search terms provided, search for all labels
        params["search"] = "*"
    
    return params


def _parse_label_item(result: Dict[str, Any]) -> OpenFDALabelItem:
    """Parse a label result from OpenFDA API response.
    
    Args:
        result: Raw result dictionary from API
        
    Returns:
        Parsed OpenFDALabelItem
    """
    # Extract basic metadata
    label_id = result.get("id")
    set_id = result.get("set_id")
    version = result.get("version")
    effective_time = result.get("effective_time")
    
    # Extract OpenFDA standardized fields
    openfda = result.get("openfda", {})
    brand_name = openfda.get("brand_name", [])
    generic_name = openfda.get("generic_name", [])
    substance_name = openfda.get("substance_name", [])
    manufacturer_name = openfda.get("manufacturer_name", [])
    product_type = openfda.get("product_type", [])
    route = openfda.get("route", [])
    application_number = openfda.get("application_number", [])
    
    # Extract label content fields
    return OpenFDALabelItem(
        id=label_id,
        set_id=set_id,
        version=version,
        effective_time=effective_time,
        brand_name=brand_name if brand_name else None,
        generic_name=generic_name if generic_name else None,
        substance_name=substance_name if substance_name else None,
        manufacturer_name=manufacturer_name if manufacturer_name else None,
        product_type=product_type if product_type else None,
        route=route if route else None,
        application_number=application_number if application_number else None,
        indications_and_usage=result.get("indications_and_usage"),
        dosage_and_administration=result.get("dosage_and_administration"),
        contraindications=result.get("contraindications"),
        warnings=result.get("warnings"),
        adverse_reactions=result.get("adverse_reactions"),
        drug_interactions=result.get("drug_interactions"),
        boxed_warning=result.get("boxed_warning"),
        mechanism_of_action=result.get("mechanism_of_action"),
        pharmacokinetics=result.get("pharmacokinetics"),
        pharmacodynamics=result.get("pharmacodynamics"),
        clinical_pharmacology=result.get("clinical_pharmacology"),
        clinical_studies=result.get("clinical_studies"),
        overdosage=result.get("overdosage"),
        description=result.get("description"),
        how_supplied=result.get("how_supplied"),
        storage_and_handling=result.get("storage_and_handling"),
        use_in_specific_populations=result.get("use_in_specific_populations"),
        pregnancy=result.get("pregnancy"),
        pediatric_use=result.get("pediatric_use"),
        geriatric_use=result.get("geriatric_use"),
        nursing_mothers=result.get("nursing_mothers"),
    )


# ================================================
# API Functions
# ================================================

def search_drug_labels(
    search_term: Optional[str] = None,
    indications_and_usage: Optional[str] = None,
    dosage_and_administration: Optional[str] = None,
    contraindications: Optional[str] = None,
    warnings: Optional[str] = None,
    adverse_reactions: Optional[str] = None,
    drug_interactions: Optional[str] = None,
    boxed_warning: Optional[str] = None,
    mechanism_of_action: Optional[str] = None,
    pharmacokinetics: Optional[str] = None,
    pharmacodynamics: Optional[str] = None,
    clinical_pharmacology: Optional[str] = None,
    clinical_studies: Optional[str] = None,
    overdosage: Optional[str] = None,
    description: Optional[str] = None,
    brand_name: Optional[str] = None,
    generic_name: Optional[str] = None,
    substance_name: Optional[str] = None,
    manufacturer_name: Optional[str] = None,
    product_type: Optional[str] = None,
    route: Optional[str] = None,
    application_number: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Search for drug product labels using OpenFDA Drug Labeling API.
    
    This function searches the structured product labeling (SPL) content that appears
    on drug packaging and inserts. You can search within specific label sections or
    use standardized drug identifiers.
    
    Args:
        search_term: General search term to query across all fields
        indications_and_usage: Search in indications and usage section
        dosage_and_administration: Search in dosage and administration section
        contraindications: Search in contraindications section
        warnings: Search in warnings section
        adverse_reactions: Search in adverse reactions section
        drug_interactions: Search in drug interactions section
        boxed_warning: Search in boxed warning (black box) section
        mechanism_of_action: Search in mechanism of action section
        pharmacokinetics: Search in pharmacokinetics section
        pharmacodynamics: Search in pharmacodynamics section
        clinical_pharmacology: Search in clinical pharmacology section
        clinical_studies: Search in clinical studies section
        overdosage: Search in overdosage section
        description: Search in description section
        brand_name: Brand or trade name of the drug product
        generic_name: Generic name(s) of the drug product
        substance_name: Active ingredient name
        manufacturer_name: Name of manufacturer or company
        product_type: Type of drug product
        route: Route of administration (e.g., 'ORAL', 'INTRAVENOUS')
        application_number: NDA, ANDA, or BLA number
        limit: Maximum number of results to return (1-1000)
        skip: Number of results to skip for pagination
        save_path: Path to save the results as JSON
    
    Returns:
        Tuple of (DataFrame with results, summary string)
        
    Examples:
        >>> # Search for drug interactions with caffeine
        >>> df, summary = search_drug_labels(drug_interactions="caffeine", limit=5)
        
        >>> # Search by brand name
        >>> df, summary = search_drug_labels(brand_name="Lipitor", limit=3)
        
        >>> # Search for warnings about a specific condition
        >>> df, summary = search_drug_labels(warnings="pregnancy", limit=10)
        
        >>> # Search mechanism of action for a specific target
        >>> df, summary = search_drug_labels(mechanism_of_action="PDE4 inhibitor")
    """
    # Create request object
    request = OpenFDALabelSearchRequest(
        search_term=search_term,
        indications_and_usage=indications_and_usage,
        dosage_and_administration=dosage_and_administration,
        contraindications=contraindications,
        warnings=warnings,
        adverse_reactions=adverse_reactions,
        drug_interactions=drug_interactions,
        boxed_warning=boxed_warning,
        mechanism_of_action=mechanism_of_action,
        pharmacokinetics=pharmacokinetics,
        pharmacodynamics=pharmacodynamics,
        clinical_pharmacology=clinical_pharmacology,
        clinical_studies=clinical_studies,
        overdosage=overdosage,
        description=description,
        brand_name=brand_name,
        generic_name=generic_name,
        substance_name=substance_name,
        manufacturer_name=manufacturer_name,
        product_type=product_type,
        route=route,
        application_number=application_number,
        limit=limit,
        skip=skip,
    )
    
    # Build query parameters
    params = _build_label_search_query(request)
    
    try:
        # Make API request
        response = requests.get(OPENFDA_LABEL_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error searching OpenFDA drug labels: {e}")
        return pd.DataFrame(), f"Error searching OpenFDA drug labels: {e}"
    except ValueError as e:
        logging.error(f"Error parsing OpenFDA response: {e}")
        return pd.DataFrame(), f"Error parsing OpenFDA response: {e}"
    
    # Parse response
    results = response_data.get("results", [])
    
    # Get metadata
    meta = response_data.get("meta", {})
    total = meta.get("results", {}).get("total", len(results))
    
    # Parse label items
    label_items = []
    for result in results:
        try:
            label_item = _parse_label_item(result)
            label_items.append(label_item)
        except Exception as e:
            logging.warning(f"Failed to parse label result: {e}")
            continue
    
    # Convert to DataFrame
    if label_items:
        data = []
        for label in label_items:
            # Helper function to join list fields
            def join_list(lst):
                if not lst:
                    return ""
                # Truncate long text for better display
                text = " | ".join(lst)
                return text[:500] + "..." if len(text) > 500 else text
            
            data.append({
                "id": label.id,
                "set_id": label.set_id,
                "effective_time": label.effective_time,
                "brand_name": ", ".join(label.brand_name) if label.brand_name else "",
                "generic_name": ", ".join(label.generic_name) if label.generic_name else "",
                "substance_name": ", ".join(label.substance_name) if label.substance_name else "",
                "manufacturer_name": ", ".join(label.manufacturer_name) if label.manufacturer_name else "",
                "route": ", ".join(label.route) if label.route else "",
                "application_number": ", ".join(label.application_number) if label.application_number else "",
                "indications_and_usage": join_list(label.indications_and_usage),
                "dosage_and_administration": join_list(label.dosage_and_administration),
                "contraindications": join_list(label.contraindications),
                "warnings": join_list(label.warnings),
                "adverse_reactions": join_list(label.adverse_reactions),
                "drug_interactions": join_list(label.drug_interactions),
                "boxed_warning": join_list(label.boxed_warning),
            })
        
        output_df = pd.DataFrame(data)
    else:
        output_df = pd.DataFrame()
    
    # Create summary string
    output_str = f"Found {len(label_items)} drug labels"
    if total > len(label_items):
        output_str += f" (showing {len(label_items)} of {total} total)"
    
    # Save results if requested
    if save_path and not output_df.empty:
        try:
            # Save as JSON to preserve full label content
            import json
            with open(save_path, 'w') as f:
                json.dump([item.dict() for item in label_items], f, indent=2)
            save_result_str = f"OpenFDA drug label search results saved to {save_path}"
        except Exception as e:
            logging.error(f"Error saving results to {save_path}: {e}")
            save_result_str = f"Error saving results to {save_path}: {e}"
        output_str = f"{output_str}\n-----\n{save_result_str}"
    
    return output_df, output_str


def fetch_drug_label_by_id(
    set_id: str,
    save_path: Optional[str] = None,
) -> tuple[Dict[str, Any], str]:
    """
    Fetch detailed drug label information by set ID from OpenFDA.
    
    The set ID is a unique identifier that is stable across label versions.
    
    Args:
        set_id: The label set ID (a GUID/UUID)
        save_path: Path to save the full label content as JSON
    
    Returns:
        Tuple of (label dictionary, summary string)
        
    Examples:
        >>> # Fetch by set ID
        >>> label, summary = fetch_drug_label_by_id("12345678-1234-1234-1234-123456789012")
    """
    try:
        # Search for the specific set ID
        params = {
            "search": f'set_id:"{set_id}"',
            "limit": 1,
        }
        
        response = requests.get(OPENFDA_LABEL_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching OpenFDA drug label: {e}")
        return {}, f"Error fetching OpenFDA drug label: {e}"
    except ValueError as e:
        logging.error(f"Error parsing OpenFDA response: {e}")
        return {}, f"Error parsing OpenFDA response: {e}"
    
    # Parse response
    results = response_data.get("results", [])
    
    if not results:
        return {}, f"No drug label found with set ID: {set_id}"
    
    label_data = results[0]
    
    # Create summary string
    openfda = label_data.get("openfda", {})
    brand_names = openfda.get("brand_name", [])
    generic_names = openfda.get("generic_name", [])
    
    output_str = f"Found drug label for set ID: {set_id}"
    if brand_names:
        output_str += f"\nBrand name(s): {', '.join(brand_names[:3])}"
    if generic_names:
        output_str += f"\nGeneric name(s): {', '.join(generic_names[:3])}"
    
    # Save results if requested
    if save_path:
        try:
            import json
            with open(save_path, 'w') as f:
                json.dump(label_data, f, indent=2)
            save_result_str = f"OpenFDA drug label saved to {save_path}"
        except Exception as e:
            logging.error(f"Error saving results to {save_path}: {e}")
            save_result_str = f"Error saving results to {save_path}: {e}"
        output_str = f"{output_str}\n-----\n{save_result_str}"
    
    return label_data, output_str


# ================================================
# Convenience Functions
# ================================================

def search_labels_by_drug_interaction(
    interaction_term: str,
    limit: int = 100,
    skip: int = 0,
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Search for drug labels by drug interaction term.
    
    Args:
        interaction_term: Search term for drug interactions (e.g., "caffeine", "warfarin")
        limit: Maximum number of results to return
        skip: Number of results to skip for pagination
        save_path: Path to save the results
    
    Returns:
        Tuple of (DataFrame with results, summary string)
        
    Examples:
        >>> # Search for caffeine interactions
        >>> df, summary = search_labels_by_drug_interaction("caffeine", limit=10)
    """
    return search_drug_labels(
        drug_interactions=interaction_term,
        limit=limit,
        skip=skip,
        save_path=save_path,
    )


def search_labels_by_adverse_reaction(
    reaction_term: str,
    limit: int = 100,
    skip: int = 0,
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Search for drug labels by adverse reaction term.
    
    Args:
        reaction_term: Search term for adverse reactions
        limit: Maximum number of results to return
        skip: Number of results to skip for pagination
        save_path: Path to save the results
    
    Returns:
        Tuple of (DataFrame with results, summary string)
        
    Examples:
        >>> # Search for headache as adverse reaction
        >>> df, summary = search_labels_by_adverse_reaction("headache", limit=10)
    """
    return search_drug_labels(
        adverse_reactions=reaction_term,
        limit=limit,
        skip=skip,
        save_path=save_path,
    )


def search_labels_by_indication(
    indication_term: str,
    limit: int = 100,
    skip: int = 0,
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Search for drug labels by indication/usage term.
    
    Args:
        indication_term: Search term for indications (e.g., "diabetes", "hypertension")
        limit: Maximum number of results to return
        skip: Number of results to skip for pagination
        save_path: Path to save the results
    
    Returns:
        Tuple of (DataFrame with results, summary string)
        
    Examples:
        >>> # Search for diabetes indications
        >>> df, summary = search_labels_by_indication("diabetes", limit=10)
    """
    return search_drug_labels(
        indications_and_usage=indication_term,
        limit=limit,
        skip=skip,
        save_path=save_path,
    )


def search_labels_by_mechanism(
    mechanism_term: str,
    limit: int = 100,
    skip: int = 0,
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Search for drug labels by mechanism of action term.
    
    Args:
        mechanism_term: Search term for mechanism (e.g., "PDE4 inhibitor", "beta blocker")
        limit: Maximum number of results to return
        skip: Number of results to skip for pagination
        save_path: Path to save the results
    
    Returns:
        Tuple of (DataFrame with results, summary string)
        
    Examples:
        >>> # Search for PDE4 inhibitors
        >>> df, summary = search_labels_by_mechanism("PDE4 inhibitor", limit=10)
    """
    return search_drug_labels(
        mechanism_of_action=mechanism_term,
        limit=limit,
        skip=skip,
        save_path=save_path,
    )


def search_labels_with_boxed_warning(
    warning_term: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    save_path: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Search for drug labels that have boxed warnings (black box warnings).
    
    Args:
        warning_term: Optional search term within boxed warnings
        limit: Maximum number of results to return
        skip: Number of results to skip for pagination
        save_path: Path to save the results
    
    Returns:
        Tuple of (DataFrame with results, summary string)
        
    Examples:
        >>> # Find all drugs with boxed warnings
        >>> df, summary = search_labels_with_boxed_warning(limit=50)
        
        >>> # Find drugs with suicide-related boxed warnings
        >>> df, summary = search_labels_with_boxed_warning("suicide", limit=10)
    """
    if warning_term:
        return search_drug_labels(
            boxed_warning=warning_term,
            limit=limit,
            skip=skip,
            save_path=save_path,
        )
    else:
        # Search for any label with a boxed warning field
        return search_drug_labels(
            search_term="_exists_:boxed_warning",
            limit=limit,
            skip=skip,
            save_path=save_path,
        )
