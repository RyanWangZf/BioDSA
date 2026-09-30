"""HPO term search and information tools.

This module provides tools for searching HPO terms and retrieving
detailed term information from the Human Phenotype Ontology.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .client import HPOClient

logger = logging.getLogger(__name__)


def search_hpo_terms(
    query: str,
    max_results: int = 20,
    offset: int = 0,
    category: Optional[List[str]] = None,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Search for HPO terms by keyword, ID, or synonym.
    
    Args:
        query: Search query (term name, keyword, HPO ID, or synonym)
        max_results: Maximum number of results to return (default: 20)
        offset: Number of results to skip (default: 0)
        category: Filter by specific HPO categories (optional)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with search results, formatted output string)
        
    Examples:
        >>> df, output = search_hpo_terms("seizure", max_results=10)
        >>> print(output)
        >>> print(df[['id', 'name']])
    """
    try:
        client = HPOClient()
        results = client.search_terms(
            query,
            max_results=max_results,
            offset=offset,
            category=category
        )
        
        terms = results.get('terms', [])
        total_results = results.get('totalResults', len(terms))
        
        # Convert to DataFrame
        df = pd.DataFrame(terms)
        
        # Format output
        output = f"# HPO Term Search Results\n\n"
        output += f"**Query:** '{query}'\n"
        if category:
            output += f"**Categories:** {', '.join(category)}\n"
        output += f"**Total results:** {total_results}\n"
        output += f"**Returned:** {len(terms)}\n\n"
        
        if not terms:
            output += "No HPO terms found for this query.\n"
        else:
            output += "## Top Results:\n\n"
            for i, term in enumerate(terms[:10], 1):
                output += f"### {i}. {term.get('name', 'N/A')}\n"
                output += f"   - **HPO ID:** {term.get('id', 'N/A')}\n"
                
                if term.get('definition'):
                    definition = term['definition']
                    if len(definition) > 150:
                        definition = definition[:150] + "..."
                    output += f"   - **Definition:** {definition}\n"
                
                synonyms = term.get('synonyms', [])
                if synonyms:
                    output += f"   - **Synonyms:** {', '.join(synonyms[:3])}\n"
                
                output += "\n"
            
            if len(terms) < total_results:
                output += f"*Showing {len(terms)} of {total_results} results. Use offset to see more.*\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error searching HPO terms: {e}")
        error_msg = f"Error searching HPO terms: {str(e)}"
        return pd.DataFrame(), error_msg


def get_hpo_term_details(
    hpo_id: str,
    save_path: Optional[str] = None
) -> Tuple[Dict[str, Any], str]:
    """Get detailed information for a specific HPO term.
    
    Args:
        hpo_id: HPO term identifier (e.g., "HP:0001250")
        save_path: Optional path to save results as JSON
        
    Returns:
        Tuple of (dictionary with term details, formatted output string)
        
    Examples:
        >>> details, output = get_hpo_term_details("HP:0001250")
        >>> print(output)
        >>> print(details['name'])
    """
    try:
        client = HPOClient()
        hpo_id = client.normalize_hpo_id(hpo_id)
        term = client.get_term(hpo_id)
        
        # Format output
        output = f"# HPO Term Details\n\n"
        output += f"## {term.get('name', 'N/A')} ({hpo_id})\n\n"
        output += f"**HPO ID:** {term.get('id', 'N/A')}\n"
        
        if term.get('isObsolete'):
            output += f"**Status:** OBSOLETE\n"
            if term.get('replacement'):
                output += f"**Replaced by:** {term.get('replacement')}\n"
        
        output += "\n"
        
        # Definition
        if term.get('definition'):
            output += "### Definition\n"
            output += f"{term['definition']}\n\n"
        
        # Comment
        if term.get('comment'):
            output += "### Comment\n"
            output += f"{term['comment']}\n\n"
        
        # Synonyms
        synonyms = term.get('synonyms', [])
        if synonyms:
            output += f"### Synonyms ({len(synonyms)} total)\n"
            for syn in synonyms[:10]:
                output += f"- {syn}\n"
            if len(synonyms) > 10:
                output += f"*... and {len(synonyms) - 10} more*\n"
            output += "\n"
        
        # Cross-references
        xrefs = term.get('xrefs', [])
        if xrefs:
            output += f"### External References ({len(xrefs)} total)\n"
            for xref in xrefs[:10]:
                output += f"- {xref}\n"
            if len(xrefs) > 10:
                output += f"*... and {len(xrefs) - 10} more*\n"
            output += "\n"
        
        # Alternative IDs
        alt_ids = term.get('alternativeIds', [])
        if alt_ids:
            output += f"### Alternative IDs\n"
            output += f"{', '.join(alt_ids)}\n\n"
        
        # Parents
        parents = term.get('parents', [])
        if parents:
            output += f"### Parent Terms ({len(parents)})\n"
            for parent in parents[:5]:
                output += f"- {parent.get('id')}: {parent.get('name')}\n"
            output += "\n"
        
        # Children
        children = term.get('children', [])
        if children:
            output += f"### Child Terms ({len(children)})\n"
            for child in children[:5]:
                output += f"- {child.get('id')}: {child.get('name')}\n"
            output += "\n"
        
        # URLs
        output += "### Resources\n"
        output += f"- **HPO Browser:** https://hpo.jax.org/app/browse/term/{hpo_id}\n\n"
        
        # Save if path provided
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(term, f, indent=2)
            output += f"\n**Full details saved to:** {save_path}\n"
        
        return term, output
    
    except Exception as e:
        logger.error(f"Error getting HPO term details: {e}")
        error_msg = f"Error getting HPO term details: {str(e)}"
        return {}, error_msg


def get_hpo_term_hierarchy(
    hpo_id: str,
    direction: str = "ancestors",
    max_results: int = 50,
    offset: int = 0,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Get hierarchical relationships for an HPO term.
    
    Args:
        hpo_id: HPO term identifier
        direction: "ancestors", "descendants", "parents", or "children"
        max_results: Maximum number of results to return (default: 50)
        offset: Number of results to skip (default: 0)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with related terms, formatted output string)
        
    Examples:
        >>> df, output = get_hpo_term_hierarchy("HP:0001250", direction="ancestors")
        >>> print(output)
    """
    try:
        client = HPOClient()
        hpo_id = client.normalize_hpo_id(hpo_id)
        
        if direction == "ancestors":
            terms = client.get_ancestors(hpo_id, max_results=max_results, offset=offset)
        elif direction == "descendants":
            terms = client.get_descendants(hpo_id, max_results=max_results, offset=offset)
        elif direction == "parents":
            terms = client.get_parents(hpo_id, max_results=max_results, offset=offset)
        elif direction == "children":
            terms = client.get_children(hpo_id, max_results=max_results, offset=offset)
        else:
            raise ValueError(f"Invalid direction: {direction}")
        
        # Convert to DataFrame
        df = pd.DataFrame(terms)
        
        # Format output
        output = f"# HPO Term Hierarchy\n\n"
        output += f"**Query term:** {hpo_id}\n"
        output += f"**Direction:** {direction}\n"
        output += f"**Related terms found:** {len(terms)}\n\n"
        
        if not terms:
            output += f"No {direction} found for this term.\n"
        else:
            output += f"## Related Terms:\n\n"
            for i, term in enumerate(terms[:20], 1):
                output += f"{i}. **{term.get('name', 'N/A')}** ({term.get('id', 'N/A')})\n"
                if term.get('definition'):
                    definition = term['definition']
                    if len(definition) > 100:
                        definition = definition[:100] + "..."
                    output += f"   {definition}\n"
                output += "\n"
            
            if len(terms) > 20:
                output += f"*... and {len(terms) - 20} more. Use offset to see more results.*\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error getting HPO term hierarchy: {e}")
        error_msg = f"Error getting HPO term hierarchy: {str(e)}"
        return pd.DataFrame(), error_msg


def validate_hpo_id(hpo_id: str) -> Tuple[Dict[str, Any], str]:
    """Validate an HPO identifier.
    
    Args:
        hpo_id: HPO identifier to validate
        
    Returns:
        Tuple of (validation results dictionary, formatted output string)
        
    Examples:
        >>> result, output = validate_hpo_id("HP:0001250")
        >>> print(output)
    """
    try:
        client = HPOClient()
        validation = client.validate_term(hpo_id)
        
        # Format output
        output = f"# HPO ID Validation\n\n"
        output += f"**Input ID:** {validation['input_id']}\n"
        output += f"**Normalized ID:** {validation['normalized_id']}\n"
        output += f"**Valid format:** {'✓ Yes' if validation['valid_format'] else '✗ No'}\n"
        output += f"**Exists in HPO:** {'✓ Yes' if validation['exists'] else '✗ No'}\n\n"
        
        if validation['term_info']:
            term = validation['term_info']
            output += "### Term Information\n"
            output += f"- **Name:** {term.get('name', 'N/A')}\n"
            if term.get('definition'):
                definition = term['definition']
                if len(definition) > 150:
                    definition = definition[:150] + "..."
                output += f"- **Definition:** {definition}\n"
            if term.get('isObsolete'):
                output += f"- **Status:** OBSOLETE\n"
            output += "\n"
        
        output += "### Format Rules\n"
        output += f"- **Pattern:** {validation['format_rules']['pattern']}\n"
        output += f"- **Example:** {validation['format_rules']['example']}\n"
        output += f"- **Description:** {validation['format_rules']['description']}\n"
        
        return validation, output
    
    except Exception as e:
        logger.error(f"Error validating HPO ID: {e}")
        error_msg = f"Error validating HPO ID: {str(e)}"
        return {}, error_msg


def get_hpo_term_path(
    hpo_id: str,
    save_path: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], str]:
    """Get the full hierarchical path from root to a specific HPO term.
    
    Args:
        hpo_id: HPO term identifier
        save_path: Optional path to save path as JSON
        
    Returns:
        Tuple of (list of terms in path, formatted output string)
        
    Examples:
        >>> path, output = get_hpo_term_path("HP:0001250")
        >>> print(output)
    """
    try:
        client = HPOClient()
        hpo_id = client.normalize_hpo_id(hpo_id)
        path = client.get_term_path(hpo_id)
        
        # Format output
        output = f"# HPO Term Path\n\n"
        output += f"**Term:** {hpo_id}\n"
        output += f"**Path depth:** {len(path) - 1} levels\n\n"
        
        output += "## Hierarchical Path:\n\n"
        for i, term in enumerate(path):
            indent = '  ' * i
            connector = '→' if i == len(path) - 1 else '├'
            output += f"{indent}{connector} **{term.get('id')}**: {term.get('name')}\n"
        
        # Save if path provided
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(path, f, indent=2)
            output += f"\n**Path saved to:** {save_path}\n"
        
        return path, output
    
    except Exception as e:
        logger.error(f"Error getting HPO term path: {e}")
        error_msg = f"Error getting HPO term path: {str(e)}"
        return [], error_msg


def compare_hpo_terms(
    term1_id: str,
    term2_id: str,
    save_path: Optional[str] = None
) -> Tuple[Dict[str, Any], str]:
    """Compare two HPO terms and find their relationship.
    
    Args:
        term1_id: First HPO term identifier
        term2_id: Second HPO term identifier
        save_path: Optional path to save comparison as JSON
        
    Returns:
        Tuple of (comparison results dictionary, formatted output string)
        
    Examples:
        >>> comparison, output = compare_hpo_terms("HP:0001250", "HP:0012469")
        >>> print(output)
    """
    try:
        client = HPOClient()
        comparison = client.compare_terms(term1_id, term2_id)
        
        # Format output
        output = f"# HPO Term Comparison\n\n"
        
        term1 = comparison['term1']
        term2 = comparison['term2']
        
        output += f"**Term 1:** {term1.get('id')} - {term1.get('name')}\n"
        output += f"**Term 2:** {term2.get('id')} - {term2.get('name')}\n\n"
        
        output += f"**Relationship:** {comparison['relationship']}\n\n"
        
        output += f"**Hierarchy Depths:**\n"
        output += f"- Term 1 depth: {comparison['term1_depth']} levels from root\n"
        output += f"- Term 2 depth: {comparison['term2_depth']} levels from root\n\n"
        
        common_ancestors = comparison['common_ancestors']
        if common_ancestors:
            output += f"**Common Ancestors ({len(common_ancestors)}):**\n"
            for i, ancestor in enumerate(common_ancestors[:10], 1):
                output += f"{i}. {ancestor.get('id')}: {ancestor.get('name')}\n"
            if len(common_ancestors) > 10:
                output += f"*... and {len(common_ancestors) - 10} more*\n"
        else:
            output += "**Common Ancestors:** None found\n"
        
        # Save if path provided
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(comparison, f, indent=2)
            output += f"\n**Comparison saved to:** {save_path}\n"
        
        return comparison, output
    
    except Exception as e:
        logger.error(f"Error comparing HPO terms: {e}")
        error_msg = f"Error comparing HPO terms: {str(e)}"
        return {}, error_msg


def get_hpo_term_statistics(
    hpo_id: str,
    save_path: Optional[str] = None
) -> Tuple[Dict[str, Any], str]:
    """Get comprehensive statistics for an HPO term.
    
    Args:
        hpo_id: HPO term identifier
        save_path: Optional path to save statistics as JSON
        
    Returns:
        Tuple of (statistics dictionary, formatted output string)
        
    Examples:
        >>> stats, output = get_hpo_term_statistics("HP:0001250")
        >>> print(output)
    """
    try:
        client = HPOClient()
        hpo_id = client.normalize_hpo_id(hpo_id)
        stats = client.get_term_statistics(hpo_id)
        
        # Format output
        output = f"# HPO Term Statistics\n\n"
        output += f"**Term:** {stats['term_id']} - {stats['term_name']}\n\n"
        
        if stats.get('definition'):
            definition = stats['definition']
            if len(definition) > 200:
                definition = definition[:200] + "..."
            output += f"**Definition:** {definition}\n\n"
        
        hierarchy = stats['hierarchy']
        output += "## Hierarchy Statistics\n"
        output += f"- **Depth from root:** {hierarchy['depth_from_root']} levels\n"
        output += f"- **Total ancestors:** {hierarchy['ancestor_count']}\n"
        output += f"- **Direct parents:** {hierarchy['parent_count']}\n"
        output += f"- **Direct children:** {hierarchy['child_count']}\n"
        output += f"- **Total descendants:** {hierarchy['descendant_count']}\n\n"
        
        properties = stats['properties']
        output += "## Term Properties\n"
        output += f"- **Synonyms:** {len(properties['synonyms'])}\n"
        output += f"- **Cross-references:** {len(properties['xrefs'])}\n"
        output += f"- **Alternative IDs:** {len(properties['alternative_ids'])}\n"
        output += f"- **Is obsolete:** {'Yes' if properties['is_obsolete'] else 'No'}\n"
        
        if properties.get('comment'):
            output += f"\n**Comment:** {properties['comment'][:150]}...\n"
        
        # Save if path provided
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(stats, f, indent=2)
            output += f"\n**Statistics saved to:** {save_path}\n"
        
        return stats, output
    
    except Exception as e:
        logger.error(f"Error getting HPO term statistics: {e}")
        error_msg = f"Error getting HPO term statistics: {str(e)}"
        return {}, error_msg


def batch_get_hpo_terms(
    hpo_ids: List[str],
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Retrieve multiple HPO terms in a single batch.
    
    Args:
        hpo_ids: List of HPO term identifiers (maximum 20)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with terms, formatted output string)
        
    Examples:
        >>> df, output = batch_get_hpo_terms(["HP:0001250", "HP:0012469"])
        >>> print(output)
    """
    try:
        client = HPOClient()
        results = client.batch_get_terms(hpo_ids)
        
        # Separate successful and failed results
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        # Convert successful results to DataFrame
        term_data = []
        for result in successful:
            term = result['data']
            term_data.append({
                'id': term.get('id'),
                'name': term.get('name'),
                'definition': term.get('definition', '')[:100] if term.get('definition') else '',
                'synonyms_count': len(term.get('synonyms', [])),
                'is_obsolete': term.get('isObsolete', False)
            })
        
        df = pd.DataFrame(term_data)
        
        # Format output
        output = f"# Batch HPO Term Retrieval\n\n"
        output += f"**Total requested:** {len(hpo_ids)}\n"
        output += f"**Successful:** {len(successful)}\n"
        output += f"**Failed:** {len(failed)}\n\n"
        
        if successful:
            output += "## Successfully Retrieved Terms:\n\n"
            for i, result in enumerate(successful, 1):
                term = result['data']
                output += f"{i}. **{term.get('id')}**: {term.get('name')}\n"
                if term.get('definition'):
                    definition = term['definition']
                    if len(definition) > 100:
                        definition = definition[:100] + "..."
                    output += f"   {definition}\n"
                output += "\n"
        
        if failed:
            output += "## Failed Terms:\n\n"
            for result in failed:
                output += f"- **{result['id']}**: {result['error']}\n"
            output += "\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error in batch term retrieval: {e}")
        error_msg = f"Error in batch term retrieval: {str(e)}"
        return pd.DataFrame(), error_msg

