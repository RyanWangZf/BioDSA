"""Target search and information tools for Open Targets Platform.

This module provides tools for searching therapeutic targets and retrieving
detailed target information from the Open Targets Platform.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .client import OpenTargetsClient

logger = logging.getLogger(__name__)


def search_targets(
    query: str,
    size: int = 25,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Search for therapeutic targets by gene symbol, name, or description.
    
    Args:
        query: Search query (gene symbol, name, description)
        size: Number of results to return (1-500, default: 25)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with target results, formatted output string)
        
    Examples:
        >>> df, output = search_targets("BRCA1", size=10)
        >>> print(output)
        >>> print(df[['id', 'name', 'description']])
    """
    try:
        client = OpenTargetsClient()
        results = client.search_targets(query, size=size)
        
        hits = results.get('data', {}).get('search', {}).get('hits', [])
        
        # Convert to DataFrame
        df = pd.DataFrame(hits)
        
        # Format output
        output = f"# Target Search Results\n\n"
        output += f"**Query:** '{query}'\n"
        output += f"**Results found:** {len(hits)}\n\n"
        
        if not hits:
            output += "No targets found for this query.\n"
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
        logger.error(f"Error searching targets: {e}")
        error_msg = f"Error searching targets: {str(e)}"
        return pd.DataFrame(), error_msg


def get_target_details(
    target_id: str,
    save_path: Optional[str] = None
) -> Tuple[Dict[str, Any], str]:
    """Get comprehensive target information.
    
    Args:
        target_id: Target Ensembl gene ID (e.g., "ENSG00000139618")
        save_path: Optional path to save results as JSON
        
    Returns:
        Tuple of (dictionary with target details, formatted output string)
        
    Examples:
        >>> details, output = get_target_details("ENSG00000139618")
        >>> print(output)
        >>> print(details['data']['target'])
    """
    try:
        client = OpenTargetsClient()
        response = client.get_target_details(target_id)
        
        target = response.get('data', {}).get('target', {})
        
        if not target:
            error_msg = f"No target found for ID: {target_id}"
            return {}, error_msg
        
        # Format output
        output = f"# Target Details\n\n"
        output += f"## {target.get('approvedSymbol', 'N/A')} - {target.get('approvedName', 'N/A')}\n\n"
        output += f"**Ensembl ID:** {target.get('id', 'N/A')}\n"
        output += f"**Biotype:** {target.get('biotype', 'N/A')}\n\n"
        
        # Genomic Location
        genomic_loc = target.get('genomicLocation', {})
        if genomic_loc:
            output += "### Genomic Location\n"
            output += f"- **Chromosome:** {genomic_loc.get('chromosome', 'N/A')}\n"
            output += f"- **Start:** {genomic_loc.get('start', 'N/A')}\n"
            output += f"- **End:** {genomic_loc.get('end', 'N/A')}\n"
            output += f"- **Strand:** {genomic_loc.get('strand', 'N/A')}\n\n"
        
        # Function Descriptions
        func_desc = target.get('functionDescriptions', [])
        if func_desc:
            output += "### Function\n"
            for desc in func_desc[:3]:  # Show first 3
                output += f"- {desc}\n"
            output += "\n"
        
        # Pathways
        pathways = target.get('pathways', [])
        if pathways:
            output += f"### Associated Pathways ({len(pathways)} total)\n"
            for pathway in pathways[:5]:  # Show first 5
                output += f"- **{pathway.get('pathway', 'N/A')}** ({pathway.get('pathwayId', 'N/A')})\n"
            output += "\n"
        
        # Protein IDs
        protein_ids = target.get('proteinIds', [])
        if protein_ids:
            output += "### Protein IDs\n"
            for pid in protein_ids[:5]:
                output += f"- **{pid.get('source', 'N/A')}:** {pid.get('id', 'N/A')}\n"
            output += "\n"
        
        # Synonyms
        synonyms = target.get('synonyms', [])
        if synonyms:
            output += "### Synonyms\n"
            for syn in synonyms[:10]:
                output += f"- {syn.get('label', 'N/A')} (from {syn.get('source', 'N/A')})\n"
            output += "\n"
        
        # Tractability
        tractability = target.get('tractability', [])
        if tractability:
            output += "### Tractability\n"
            for tract in tractability:
                output += f"- **{tract.get('modality', 'N/A')}:** {tract.get('label', 'N/A')} (value: {tract.get('value', 'N/A')})\n"
            output += "\n"
        
        # Save if path provided
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(response, f, indent=2)
            output += f"\n**Full details saved to:** {save_path}\n"
        
        return response, output
    
    except Exception as e:
        logger.error(f"Error getting target details: {e}")
        error_msg = f"Error getting target details: {str(e)}"
        return {}, error_msg


def get_target_associated_diseases(
    target_id: str,
    size: int = 25,
    min_score: Optional[float] = None,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Get diseases associated with a specific target.
    
    Args:
        target_id: Target Ensembl gene ID (e.g., "ENSG00000139618")
        size: Number of associations to return (default: 25)
        min_score: Minimum association score threshold (0-1, optional)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with disease associations, formatted output string)
        
    Examples:
        >>> df, output = get_target_associated_diseases("ENSG00000139618", size=10)
        >>> print(output)
        >>> print(df[['disease_id', 'disease_name', 'score']])
    """
    try:
        client = OpenTargetsClient()
        response = client.get_target_associations(
            target_id,
            size=size,
            min_score=min_score
        )
        
        target_data = response.get('data', {}).get('target', {})
        associations = target_data.get('associatedDiseases', {})
        rows = associations.get('rows', [])
        
        # Convert to DataFrame
        data_records = []
        for row in rows:
            disease = row.get('disease', {})
            record = {
                'disease_id': disease.get('id'),
                'disease_name': disease.get('name'),
                'score': row.get('score')
            }
            # Add datatype scores
            datatype_scores = row.get('datatypeScores', [])
            for ds in datatype_scores:
                record[f"score_{ds.get('id', 'unknown')}"] = ds.get('score')
            data_records.append(record)
        
        df = pd.DataFrame(data_records)
        
        # Format output
        output = f"# Target-Disease Associations\n\n"
        output += f"**Target:** {target_data.get('approvedSymbol', 'N/A')} ({target_data.get('approvedName', 'N/A')})\n"
        output += f"**Target ID:** {target_data.get('id', 'N/A')}\n"
        output += f"**Total associations:** {associations.get('count', 0)}\n"
        if min_score:
            output += f"**Minimum score filter:** {min_score}\n"
        output += "\n"
        
        if not rows:
            output += "No disease associations found.\n"
        else:
            output += "## Top Disease Associations:\n\n"
            for i, row in enumerate(rows[:10], 1):
                disease = row.get('disease', {})
                output += f"### {i}. {disease.get('name', 'N/A')}\n"
                output += f"   - **Disease ID:** {disease.get('id', 'N/A')}\n"
                output += f"   - **Association Score:** {row.get('score', 'N/A'):.4f}\n"
                
                # Show datatype scores
                datatype_scores = row.get('datatypeScores', [])
                if datatype_scores:
                    output += "   - **Evidence scores:**\n"
                    for ds in datatype_scores:
                        output += f"     - {ds.get('id', 'unknown')}: {ds.get('score', 'N/A'):.4f}\n"
                output += "\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error getting target associations: {e}")
        error_msg = f"Error getting target associations: {str(e)}"
        return pd.DataFrame(), error_msg

