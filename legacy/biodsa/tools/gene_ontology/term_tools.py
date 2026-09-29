"""Gene Ontology term search and information tools.

This module provides tools for searching GO terms and retrieving
detailed term information from the Gene Ontology.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .client import GeneOntologyClient

logger = logging.getLogger(__name__)


def search_go_terms(
    query: str,
    ontology: Optional[str] = None,
    limit: int = 25,
    exact: bool = False,
    include_obsolete: bool = False,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Search across Gene Ontology terms.
    
    Args:
        query: Search query (term name, keyword, or definition)
        ontology: GO ontology to search ("molecular_function", "biological_process",
                 "cellular_component", or None for all)
        limit: Number of results to return (1-500, default: 25)
        exact: Exact match only (default: False)
        include_obsolete: Include obsolete terms (default: False)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with search results, formatted output string)
        
    Examples:
        >>> df, output = search_go_terms("kinase activity", limit=10)
        >>> print(output)
        >>> print(df[['id', 'name', 'namespace']])
    """
    try:
        client = GeneOntologyClient()
        results = client.search_terms(
            query,
            ontology=ontology,
            limit=limit,
            exact=exact,
            include_obsolete=include_obsolete
        )
        
        terms = results.get('results', [])
        
        # Convert to DataFrame
        term_data = []
        for term in terms:
            aspect = term.get('aspect', '')
            namespace = (
                'molecular_function' if aspect == 'F' else
                'biological_process' if aspect == 'P' else
                'cellular_component' if aspect == 'C' else
                'unknown'
            )
            
            term_data.append({
                'id': term.get('id'),
                'name': term.get('name'),
                'definition': term.get('definition', {}).get('text', 'No definition available'),
                'namespace': namespace,
                'obsolete': term.get('isObsolete', False)
            })
        
        df = pd.DataFrame(term_data)
        
        # Format output
        output = f"# GO Term Search Results\n\n"
        output += f"**Query:** '{query}'\n"
        if ontology:
            output += f"**Ontology:** {ontology}\n"
        output += f"**Total results:** {results.get('numberOfHits', 0)}\n"
        output += f"**Returned results:** {len(terms)}\n\n"
        
        if not terms:
            output += "No GO terms found for this query.\n"
        else:
            output += "## Top Results:\n\n"
            for i, term in enumerate(terms[:10], 1):
                aspect = term.get('aspect', '')
                namespace = (
                    'molecular_function' if aspect == 'F' else
                    'biological_process' if aspect == 'P' else
                    'cellular_component' if aspect == 'C' else
                    'unknown'
                )
                
                output += f"### {i}. {term.get('name', 'N/A')}\n"
                output += f"   - **GO ID:** {term.get('id', 'N/A')}\n"
                output += f"   - **Ontology:** {namespace}\n"
                
                definition = term.get('definition', {})
                if isinstance(definition, dict):
                    def_text = definition.get('text', 'No definition available')
                else:
                    def_text = str(definition) if definition else 'No definition available'
                
                # Truncate long definitions
                if len(def_text) > 150:
                    def_text = def_text[:150] + "..."
                output += f"   - **Definition:** {def_text}\n"
                
                if term.get('isObsolete'):
                    output += f"   - **Status:** OBSOLETE\n"
                
                output += "\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error searching GO terms: {e}")
        error_msg = f"Error searching GO terms: {str(e)}"
        return pd.DataFrame(), error_msg


def get_go_term_details(
    go_id: str,
    save_path: Optional[str] = None
) -> Tuple[Dict[str, Any], str]:
    """Get detailed information for a specific GO term.
    
    Args:
        go_id: GO term identifier (e.g., "GO:0008150")
        save_path: Optional path to save results as JSON
        
    Returns:
        Tuple of (dictionary with term details, formatted output string)
        
    Examples:
        >>> details, output = get_go_term_details("GO:0008150")
        >>> print(output)
        >>> print(details['name'])
    """
    try:
        client = GeneOntologyClient()
        go_id = client.normalize_go_id(go_id)
        response = client.get_term(go_id)
        
        results = response.get('results', [])
        if not results:
            error_msg = f"GO term not found: {go_id}"
            return {}, error_msg
        
        term = results[0]
        
        # Determine namespace
        aspect = term.get('aspect', '')
        namespace = (
            'molecular_function' if aspect == 'F' else
            'biological_process' if aspect == 'P' else
            'cellular_component' if aspect == 'C' else
            'unknown'
        )
        
        # Format output
        output = f"# GO Term Details\n\n"
        output += f"## {term.get('name', 'N/A')} ({go_id})\n\n"
        output += f"**GO ID:** {term.get('id', 'N/A')}\n"
        output += f"**Ontology:** {namespace}\n"
        
        if term.get('isObsolete'):
            output += f"**Status:** OBSOLETE\n"
            if term.get('replacedBy'):
                output += f"**Replaced by:** {', '.join(term.get('replacedBy', []))}\n"
            if term.get('consider'):
                output += f"**Consider:** {', '.join(term.get('consider', []))}\n"
        
        output += "\n"
        
        # Definition
        definition = term.get('definition', {})
        if isinstance(definition, dict):
            def_text = definition.get('text', 'No definition available')
            def_refs = definition.get('xrefs', [])
        else:
            def_text = str(definition) if definition else 'No definition available'
            def_refs = []
        
        output += "### Definition\n"
        output += f"{def_text}\n\n"
        
        if def_refs:
            output += "**References:**\n"
            for ref in def_refs[:5]:
                output += f"- {ref}\n"
            output += "\n"
        
        # Synonyms
        synonyms = term.get('synonyms', [])
        if synonyms:
            output += f"### Synonyms ({len(synonyms)} total)\n"
            for syn in synonyms[:10]:
                syn_name = syn.get('name', syn) if isinstance(syn, dict) else syn
                output += f"- {syn_name}\n"
            output += "\n"
        
        # Cross-references
        xrefs = term.get('xrefs', [])
        if xrefs:
            output += f"### External References ({len(xrefs)} total)\n"
            for xref in xrefs[:10]:
                xref_name = xref.get('id', xref) if isinstance(xref, dict) else xref
                output += f"- {xref_name}\n"
            output += "\n"
        
        # URLs
        output += "### Resources\n"
        output += f"- **QuickGO:** https://www.ebi.ac.uk/QuickGO/term/{go_id}\n"
        output += f"- **AmiGO:** http://amigo.geneontology.org/amigo/term/{go_id}\n\n"
        
        # Save if path provided
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(term, f, indent=2)
            output += f"\n**Full details saved to:** {save_path}\n"
        
        return term, output
    
    except Exception as e:
        logger.error(f"Error getting GO term details: {e}")
        error_msg = f"Error getting GO term details: {str(e)}"
        return {}, error_msg


def get_go_term_hierarchy(
    go_id: str,
    direction: str = "ancestors",
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Get hierarchical relationships for a GO term.
    
    Args:
        go_id: GO term identifier
        direction: "ancestors" for parent terms or "descendants" for child terms
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with related terms, formatted output string)
        
    Examples:
        >>> df, output = get_go_term_hierarchy("GO:0004672", direction="ancestors")
        >>> print(output)
    """
    try:
        client = GeneOntologyClient()
        go_id = client.normalize_go_id(go_id)
        
        if direction == "ancestors":
            response = client.get_term_ancestors(go_id)
        elif direction == "descendants":
            response = client.get_term_descendants(go_id)
        elif direction == "children":
            response = client.get_term_children(go_id)
        else:
            raise ValueError(f"Invalid direction: {direction}. Use 'ancestors', 'descendants', or 'children'")
        
        results = response.get('results', [])
        
        # Convert to DataFrame
        term_data = []
        for term in results:
            aspect = term.get('aspect', '')
            namespace = (
                'molecular_function' if aspect == 'F' else
                'biological_process' if aspect == 'P' else
                'cellular_component' if aspect == 'C' else
                'unknown'
            )
            
            term_data.append({
                'id': term.get('id'),
                'name': term.get('name'),
                'namespace': namespace,
                'relation': term.get('relation', 'unknown')
            })
        
        df = pd.DataFrame(term_data)
        
        # Format output
        output = f"# GO Term Hierarchy\n\n"
        output += f"**Query term:** {go_id}\n"
        output += f"**Direction:** {direction}\n"
        output += f"**Related terms found:** {len(results)}\n\n"
        
        if not results:
            output += f"No {direction} found for this term.\n"
        else:
            output += f"## Related Terms:\n\n"
            for i, term in enumerate(results[:20], 1):
                aspect = term.get('aspect', '')
                namespace = (
                    'molecular_function' if aspect == 'F' else
                    'biological_process' if aspect == 'P' else
                    'cellular_component' if aspect == 'C' else
                    'unknown'
                )
                
                output += f"{i}. **{term.get('name', 'N/A')}** ({term.get('id', 'N/A')})\n"
                output += f"   - Ontology: {namespace}\n"
                if term.get('relation'):
                    output += f"   - Relation: {term.get('relation')}\n"
                output += "\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error getting GO term hierarchy: {e}")
        error_msg = f"Error getting GO term hierarchy: {str(e)}"
        return pd.DataFrame(), error_msg


def validate_go_id(go_id: str) -> Tuple[Dict[str, Any], str]:
    """Validate a GO identifier.
    
    Args:
        go_id: GO identifier to validate
        
    Returns:
        Tuple of (validation results dictionary, formatted output string)
        
    Examples:
        >>> result, output = validate_go_id("GO:0008150")
        >>> print(output)
    """
    try:
        client = GeneOntologyClient()
        validation = client.validate_term(go_id)
        
        # Format output
        output = f"# GO ID Validation\n\n"
        output += f"**Input ID:** {validation['input_id']}\n"
        output += f"**Normalized ID:** {validation['normalized_id']}\n"
        output += f"**Valid format:** {'✓ Yes' if validation['valid_format'] else '✗ No'}\n"
        output += f"**Exists in GO:** {'✓ Yes' if validation['exists'] else '✗ No'}\n\n"
        
        if validation['term_info']:
            term = validation['term_info']
            aspect = term.get('aspect', '')
            namespace = (
                'molecular_function' if aspect == 'F' else
                'biological_process' if aspect == 'P' else
                'cellular_component' if aspect == 'C' else
                'unknown'
            )
            
            output += "### Term Information\n"
            output += f"- **Name:** {term.get('name', 'N/A')}\n"
            output += f"- **Ontology:** {namespace}\n"
            output += f"- **Obsolete:** {'Yes' if term.get('isObsolete') else 'No'}\n\n"
        
        output += "### Format Rules\n"
        output += f"- **Pattern:** {validation['format_rules']['pattern']}\n"
        output += f"- **Example:** {validation['format_rules']['example']}\n"
        output += f"- **Description:** {validation['format_rules']['description']}\n"
        
        return validation, output
    
    except Exception as e:
        logger.error(f"Error validating GO ID: {e}")
        error_msg = f"Error validating GO ID: {str(e)}"
        return {}, error_msg


def get_ontology_statistics() -> Tuple[Dict[str, Any], str]:
    """Get statistics about GO ontologies.
    
    Returns:
        Tuple of (statistics dictionary, formatted output string)
        
    Examples:
        >>> stats, output = get_ontology_statistics()
        >>> print(output)
    """
    try:
        client = GeneOntologyClient()
        stats = client.get_ontology_statistics()
        
        # Format output
        output = f"# Gene Ontology Statistics\n\n"
        
        output += "## Ontologies\n\n"
        for ont_name, ont_info in stats['ontologies'].items():
            output += f"### {ont_name.replace('_', ' ').title()}\n"
            output += f"- **Description:** {ont_info['description']}\n"
            output += f"- **Root term:** {ont_info['root_term']}\n"
            output += f"- **Aspect code:** {ont_info['aspect']}\n\n"
        
        output += "## Evidence Codes\n\n"
        for category, cat_info in stats['evidence_codes'].items():
            output += f"### {category.replace('_', ' ').title()}\n"
            output += f"- **Description:** {cat_info['description']}\n"
            output += f"- **Codes:** {', '.join(cat_info['codes'])}\n\n"
        
        output += "## Resources\n\n"
        for resource, url in stats['resources'].items():
            output += f"- **{resource.replace('_', ' ').title()}:** {url}\n"
        
        return stats, output
    
    except Exception as e:
        logger.error(f"Error getting ontology statistics: {e}")
        error_msg = f"Error getting ontology statistics: {str(e)}"
        return {}, error_msg

