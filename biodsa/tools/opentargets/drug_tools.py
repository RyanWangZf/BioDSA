"""Drug search and information tools for Open Targets Platform.

This module provides tools for searching drugs and retrieving
detailed drug information from the Open Targets Platform.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .client import OpenTargetsClient

logger = logging.getLogger(__name__)


def search_drugs(
    query: str,
    size: int = 25,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Search for drugs by name or ChEMBL ID.
    
    Args:
        query: Search query (drug name or ChEMBL ID)
        size: Number of results to return (1-500, default: 25)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with drug results, formatted output string)
        
    Examples:
        >>> df, output = search_drugs("aspirin", size=10)
        >>> print(output)
        >>> print(df[['id', 'name', 'description']])
    """
    try:
        client = OpenTargetsClient()
        results = client.search_drugs(query, size=size)
        
        hits = results.get('data', {}).get('search', {}).get('hits', [])
        
        # Convert to DataFrame
        df = pd.DataFrame(hits)
        
        # Format output
        output = f"# Drug Search Results\n\n"
        output += f"**Query:** '{query}'\n"
        output += f"**Results found:** {len(hits)}\n\n"
        
        if not hits:
            output += "No drugs found for this query.\n"
        else:
            output += "## Top Results:\n\n"
            for i, hit in enumerate(hits[:10], 1):
                output += f"### {i}. {hit.get('name', 'N/A')}\n"
                output += f"   - **ID:** {hit.get('id', 'N/A')}\n"
                output += f"   - **Description:** {hit.get('description', 'N/A')}\n"
                output += f"   - **Entity:** {hit.get('entity', 'N/A')}\n\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error searching drugs: {e}")
        error_msg = f"Error searching drugs: {str(e)}"
        return pd.DataFrame(), error_msg


def get_drug_details(
    drug_id: str,
    save_path: Optional[str] = None
) -> Tuple[Dict[str, Any], str]:
    """Get comprehensive drug information.
    
    Args:
        drug_id: Drug ChEMBL ID (e.g., "CHEMBL1234")
        save_path: Optional path to save results as JSON
        
    Returns:
        Tuple of (dictionary with drug details, formatted output string)
        
    Examples:
        >>> details, output = get_drug_details("CHEMBL1234")
        >>> print(output)
        >>> print(details['data']['drug'])
    """
    try:
        client = OpenTargetsClient()
        response = client.get_drug_details(drug_id)
        
        drug = response.get('data', {}).get('drug', {})
        
        if not drug:
            error_msg = f"No drug found for ID: {drug_id}"
            return {}, error_msg
        
        # Format output
        output = f"# Drug Details\n\n"
        output += f"## {drug.get('name', 'N/A')}\n\n"
        output += f"**ChEMBL ID:** {drug.get('id', 'N/A')}\n"
        output += f"**Description:** {drug.get('description', 'N/A')}\n"
        output += f"**Drug Type:** {drug.get('drugType', 'N/A')}\n"
        output += f"**Maximum Clinical Trial Phase:** {drug.get('maximumClinicalTrialPhase', 'N/A')}\n"
        output += f"**Has Been Withdrawn:** {drug.get('hasBeenWithdrawn', False)}\n\n"
        
        # Synonyms
        synonyms = drug.get('synonyms', [])
        if synonyms:
            output += "### Synonyms\n"
            for syn in synonyms[:10]:
                output += f"- {syn}\n"
            output += "\n"
        
        # Linked entities counts
        linked_diseases = drug.get('linkedDiseases', {})
        linked_targets = drug.get('linkedTargets', {})
        
        output += "### Associated Entities\n"
        output += f"- **Linked Diseases:** {linked_diseases.get('count', 0)}\n"
        output += f"- **Linked Targets:** {linked_targets.get('count', 0)}\n\n"
        
        # Save if path provided
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(response, f, indent=2)
            output += f"\n**Full details saved to:** {save_path}\n"
        
        return response, output
    
    except Exception as e:
        logger.error(f"Error getting drug details: {e}")
        error_msg = f"Error getting drug details: {str(e)}"
        return {}, error_msg

