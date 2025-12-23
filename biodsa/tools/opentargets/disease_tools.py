"""Disease search and information tools for Open Targets Platform.

This module provides tools for searching diseases and retrieving
detailed disease information from the Open Targets Platform.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .client import OpenTargetsClient

logger = logging.getLogger(__name__)


def search_diseases(
    query: str,
    size: int = 25,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Search for diseases by name, synonym, or description.
    
    Args:
        query: Search query (disease name, synonym, description)
        size: Number of results to return (1-500, default: 25)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with disease results, formatted output string)
        
    Examples:
        >>> df, output = search_diseases("lung cancer", size=10)
        >>> print(output)
        >>> print(df[['id', 'name', 'description']])
    """
    try:
        client = OpenTargetsClient()
        results = client.search_diseases(query, size=size)
        
        hits = results.get('data', {}).get('search', {}).get('hits', [])
        
        # Convert to DataFrame
        df = pd.DataFrame(hits)
        
        # Format output
        output = f"# Disease Search Results\n\n"
        output += f"**Query:** '{query}'\n"
        output += f"**Results found:** {len(hits)}\n\n"
        
        if not hits:
            output += "No diseases found for this query.\n"
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
        logger.error(f"Error searching diseases: {e}")
        error_msg = f"Error searching diseases: {str(e)}"
        return pd.DataFrame(), error_msg


def get_disease_details(
    disease_id: str,
    save_path: Optional[str] = None
) -> Tuple[Dict[str, Any], str]:
    """Get comprehensive disease information.
    
    Args:
        disease_id: Disease EFO ID (e.g., "EFO_0000508")
        save_path: Optional path to save results as JSON
        
    Returns:
        Tuple of (dictionary with disease details, formatted output string)
        
    Examples:
        >>> details, output = get_disease_details("EFO_0000508")
        >>> print(output)
        >>> print(details['data']['disease'])
    """
    try:
        client = OpenTargetsClient()
        response = client.get_disease_details(disease_id)
        
        disease = response.get('data', {}).get('disease', {})
        
        if not disease:
            error_msg = f"No disease found for ID: {disease_id}"
            return {}, error_msg
        
        # Format output
        output = f"# Disease Details\n\n"
        output += f"## {disease.get('name', 'N/A')}\n\n"
        output += f"**EFO ID:** {disease.get('id', 'N/A')}\n"
        output += f"**Description:** {disease.get('description', 'N/A')}\n\n"
        
        # Synonyms
        synonyms = disease.get('synonyms', {})
        if synonyms and synonyms.get('terms'):
            output += "### Synonyms\n"
            for term in synonyms.get('terms', [])[:10]:
                output += f"- {term}\n"
            output += "\n"
        
        # Therapeutic Areas
        therapeutic_areas = disease.get('therapeuticAreas', [])
        if therapeutic_areas:
            output += "### Therapeutic Areas\n"
            for area in therapeutic_areas:
                output += f"- **{area.get('name', 'N/A')}** ({area.get('id', 'N/A')})\n"
            output += "\n"
        
        # Parents
        parents = disease.get('parents', [])
        if parents:
            output += f"### Parent Terms ({len(parents)} total)\n"
            for parent in parents[:5]:
                output += f"- **{parent.get('name', 'N/A')}** ({parent.get('id', 'N/A')})\n"
            output += "\n"
        
        # Children
        children = disease.get('children', [])
        if children:
            output += f"### Child Terms ({len(children)} total)\n"
            for child in children[:5]:
                output += f"- **{child.get('name', 'N/A')}** ({child.get('id', 'N/A')})\n"
            output += "\n"
        
        # Ontology Information
        ontology = disease.get('ontology', {})
        if ontology:
            output += "### Ontology Information\n"
            output += f"- **Is Therapeutic Area:** {ontology.get('isTherapeuticArea', False)}\n"
            output += f"- **Is Leaf Node:** {ontology.get('leaf', False)}\n"
            sources = ontology.get('sources', [])
            if sources:
                output += "- **Sources:**\n"
                for source in sources:
                    output += f"  - {source.get('name', 'N/A')}: {source.get('url', 'N/A')}\n"
            output += "\n"
        
        # Save if path provided
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(response, f, indent=2)
            output += f"\n**Full details saved to:** {save_path}\n"
        
        return response, output
    
    except Exception as e:
        logger.error(f"Error getting disease details: {e}")
        error_msg = f"Error getting disease details: {str(e)}"
        return {}, error_msg


def get_disease_associated_targets(
    disease_id: str,
    size: int = 25,
    min_score: Optional[float] = None,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Get targets associated with a specific disease.
    
    Args:
        disease_id: Disease EFO ID (e.g., "EFO_0000508")
        size: Number of associations to return (default: 25)
        min_score: Minimum association score threshold (0-1, optional)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with target associations, formatted output string)
        
    Examples:
        >>> df, output = get_disease_associated_targets("EFO_0000508", size=10)
        >>> print(output)
        >>> print(df[['target_id', 'target_symbol', 'score']])
    """
    try:
        client = OpenTargetsClient()
        response = client.get_disease_associations(
            disease_id,
            size=size,
            min_score=min_score
        )
        
        disease_data = response.get('data', {}).get('disease', {})
        associations = disease_data.get('associatedTargets', {})
        rows = associations.get('rows', [])
        
        # Convert to DataFrame
        data_records = []
        for row in rows:
            target = row.get('target', {})
            record = {
                'target_id': target.get('id'),
                'target_symbol': target.get('approvedSymbol'),
                'target_name': target.get('approvedName'),
                'score': row.get('score')
            }
            # Add datatype scores
            datatype_scores = row.get('datatypeScores', [])
            for ds in datatype_scores:
                record[f"score_{ds.get('id', 'unknown')}"] = ds.get('score')
            data_records.append(record)
        
        df = pd.DataFrame(data_records)
        
        # Format output
        output = f"# Disease-Target Associations\n\n"
        output += f"**Disease:** {disease_data.get('name', 'N/A')}\n"
        output += f"**Disease ID:** {disease_data.get('id', 'N/A')}\n"
        output += f"**Total associations:** {associations.get('count', 0)}\n"
        if min_score:
            output += f"**Minimum score filter:** {min_score}\n"
        output += "\n"
        
        if not rows:
            output += "No target associations found.\n"
        else:
            output += "## Top Target Associations:\n\n"
            for i, row in enumerate(rows[:10], 1):
                target = row.get('target', {})
                output += f"### {i}. {target.get('approvedSymbol', 'N/A')} - {target.get('approvedName', 'N/A')}\n"
                output += f"   - **Target ID:** {target.get('id', 'N/A')}\n"
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
        logger.error(f"Error getting disease associations: {e}")
        error_msg = f"Error getting disease associations: {str(e)}"
        return pd.DataFrame(), error_msg


def get_disease_targets_summary(
    disease_id: str,
    size: int = 50,
    min_score: Optional[float] = None,
    save_path: Optional[str] = None
) -> Tuple[Dict[str, Any], str]:
    """Get overview of all targets associated with a disease.
    
    Args:
        disease_id: Disease EFO ID (e.g., "EFO_0000508")
        size: Number of targets to return (default: 50)
        min_score: Minimum association score threshold (0-1, optional)
        save_path: Optional path to save results as JSON
        
    Returns:
        Tuple of (dictionary with summary, formatted output string)
        
    Examples:
        >>> summary, output = get_disease_targets_summary("EFO_0000508", size=20)
        >>> print(output)
        >>> print(summary['topTargets'])
    """
    try:
        client = OpenTargetsClient()
        summary = client.get_disease_targets_summary(
            disease_id,
            size=size,
            min_score=min_score
        )
        
        # Format output
        output = f"# Disease Targets Summary\n\n"
        output += f"**Disease:** {summary.get('diseaseName', 'N/A')}\n"
        output += f"**Disease ID:** {summary.get('diseaseId', 'N/A')}\n"
        output += f"**Total associated targets:** {summary.get('totalTargets', 0)}\n"
        if min_score:
            output += f"**Minimum score filter:** {min_score}\n"
        output += "\n"
        
        top_targets = summary.get('topTargets', [])
        if not top_targets:
            output += "No targets found.\n"
        else:
            output += f"## Top {len(top_targets)} Targets:\n\n"
            for i, target in enumerate(top_targets, 1):
                output += f"### {i}. {target.get('targetSymbol', 'N/A')} - {target.get('targetName', 'N/A')}\n"
                output += f"   - **Target ID:** {target.get('targetId', 'N/A')}\n"
                output += f"   - **Association Score:** {target.get('associationScore', 'N/A'):.4f}\n"
                
                # Show datatype scores
                datatype_scores = target.get('datatypeScores', [])
                if datatype_scores:
                    output += "   - **Evidence scores:**\n"
                    for ds in datatype_scores:
                        output += f"     - {ds.get('id', 'unknown')}: {ds.get('score', 'N/A'):.4f}\n"
                output += "\n"
        
        # Save if path provided
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(summary, f, indent=2)
            output += f"\n**Full summary saved to:** {save_path}\n"
        
        return summary, output
    
    except Exception as e:
        logger.error(f"Error getting disease targets summary: {e}")
        error_msg = f"Error getting disease targets summary: {str(e)}"
        return {}, error_msg

