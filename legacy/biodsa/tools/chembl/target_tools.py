"""Target-specific tools for ChEMBL Database.

This module provides tools for searching biological targets and retrieving
target-related bioactivity data from ChEMBL.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .client import ChEMBLClient

logger = logging.getLogger(__name__)


def search_targets(
    query: str,
    target_type: Optional[str] = None,
    organism: Optional[str] = None,
    limit: int = 25,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Search for biological targets by name or type.
    
    Args:
        query: Target name or search query
        target_type: Target type filter (e.g., "SINGLE PROTEIN", "PROTEIN COMPLEX")
        organism: Organism filter (e.g., "Homo sapiens")
        limit: Number of results to return (default: 25)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with targets, formatted output string)
        
    Examples:
        >>> # Search for kinase targets
        >>> df, output = search_targets("kinase", limit=10)
        >>> print(output)
        >>> 
        >>> # Search for human protein targets
        >>> df, output = search_targets(
        ...     "receptor",
        ...     target_type="SINGLE PROTEIN",
        ...     organism="Homo sapiens"
        ... )
        >>> print(output)
    """
    try:
        client = ChEMBLClient()
        results = client.search_targets(
            query=query,
            target_type=target_type,
            organism=organism,
            limit=limit
        )
        
        targets = results.get('targets', [])
        
        # Convert to DataFrame
        df = pd.DataFrame(targets)
        
        # Format output
        output = f"# Target Search Results\n\n"
        output += f"**Query:** '{query}'\n"
        if target_type:
            output += f"**Target Type:** {target_type}\n"
        if organism:
            output += f"**Organism:** {organism}\n"
        output += f"**Results found:** {len(targets)}\n\n"
        
        if not targets:
            output += "No targets found for this query.\n"
        else:
            output += "## Top Results:\n\n"
            for i, target in enumerate(targets[:15], 1):
                target_id = target.get('target_chembl_id', 'N/A')
                pref_name = target.get('pref_name', 'N/A')
                target_type_val = target.get('target_type', 'N/A')
                
                output += f"### {i}. {pref_name}\n"
                output += f"   - **ChEMBL ID:** {target_id}\n"
                output += f"   - **Type:** {target_type_val}\n"
                
                # Organism
                if target.get('organism'):
                    output += f"   - **Organism:** {target['organism']}\n"
                
                # Target components (for protein complexes)
                components = target.get('target_components', [])
                if components:
                    output += f"   - **Components:** {len(components)}\n"
                    # Show first component details
                    if components:
                        comp = components[0]
                        if comp.get('component_type'):
                            output += f"     - Type: {comp['component_type']}\n"
                        if comp.get('accession'):
                            output += f"     - Accession: {comp['accession']}\n"
                
                output += "\n"
        
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
    chembl_id: str,
    save_path: Optional[str] = None
) -> Tuple[Dict[str, Any], str]:
    """Get detailed information for a specific target by ChEMBL target ID.
    
    Args:
        chembl_id: ChEMBL target ID (e.g., "CHEMBL2095173")
        save_path: Optional path to save results as JSON
        
    Returns:
        Tuple of (dictionary with target details, formatted output string)
        
    Examples:
        >>> # Get details for COX-2
        >>> details, output = get_target_details("CHEMBL2095173")
        >>> print(output)
        >>> print(details.keys())
    """
    try:
        client = ChEMBLClient()
        target = client.get_target_by_id(chembl_id)
        
        # Format output
        output = f"# Target Details\n\n"
        output += f"## {target.get('pref_name', 'N/A')} ({chembl_id})\n\n"
        
        output += f"**ChEMBL ID:** {target.get('target_chembl_id', 'N/A')}\n"
        output += f"**Type:** {target.get('target_type', 'N/A')}\n"
        output += f"**Organism:** {target.get('organism', 'N/A')}\n"
        
        # Tax ID
        if target.get('tax_id'):
            output += f"**Taxonomy ID:** {target['tax_id']}\n"
        
        output += "\n"
        
        # Target components
        components = target.get('target_components', [])
        if components:
            output += f"### Target Components ({len(components)})\n\n"
            for i, comp in enumerate(components[:5], 1):
                comp_type = comp.get('component_type', 'N/A')
                comp_desc = comp.get('component_description', 'N/A')
                
                output += f"**{i}. {comp_desc}**\n"
                output += f"   - Type: {comp_type}\n"
                
                if comp.get('accession'):
                    output += f"   - Accession: {comp['accession']}\n"
                
                # Synonyms
                synonyms = comp.get('component_synonyms', [])
                if synonyms:
                    syn_list = [s.get('component_synonym', s) if isinstance(s, dict) else s 
                               for s in synonyms[:3]]
                    output += f"   - Synonyms: {', '.join(syn_list)}\n"
                
                # Gene info
                if comp.get('target_gene_id'):
                    output += f"   - Gene ID: {comp['target_gene_id']}\n"
                if comp.get('target_gene_symbol'):
                    output += f"   - Gene Symbol: {comp['target_gene_symbol']}\n"
                
                output += "\n"
            
            if len(components) > 5:
                output += f"... and {len(components) - 5} more components\n\n"
        
        # Cross references
        xrefs = target.get('cross_references', [])
        if xrefs:
            output += f"### External References ({len(xrefs)} total)\n"
            # Group by source
            by_source = {}
            for xref in xrefs:
                source = xref.get('xref_src', 'Unknown')
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(xref.get('xref_id', 'N/A'))
            
            for source, ids in list(by_source.items())[:10]:
                output += f"- **{source}:** {', '.join(ids[:3])}\n"
            output += "\n"
        
        # Save if path provided
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(target, f, indent=2)
            output += f"\n**Full details saved to:** {save_path}\n"
        
        return target, output
    
    except Exception as e:
        logger.error(f"Error getting target details: {e}")
        error_msg = f"Error getting target details: {str(e)}"
        return {}, error_msg


def search_by_uniprot(
    uniprot_id: str,
    limit: int = 25,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Find ChEMBL targets by UniProt accession.
    
    Args:
        uniprot_id: UniProt accession number (e.g., "P00533")
        limit: Number of results to return (default: 25)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with targets, formatted output string)
        
    Examples:
        >>> # Find targets for EGFR UniProt ID
        >>> df, output = search_by_uniprot("P00533")
        >>> print(output)
    """
    try:
        client = ChEMBLClient()
        results = client.search_by_uniprot(uniprot_id, limit=limit)
        
        targets = results.get('targets', [])
        
        # Convert to DataFrame
        df = pd.DataFrame(targets)
        
        # Format output
        output = f"# Targets by UniProt ID\n\n"
        output += f"**UniProt ID:** {uniprot_id}\n"
        output += f"**Results found:** {len(targets)}\n\n"
        
        if not targets:
            output += "No targets found for this UniProt ID.\n"
        else:
            output += "## Matching Targets:\n\n"
            for i, target in enumerate(targets[:15], 1):
                target_id = target.get('target_chembl_id', 'N/A')
                pref_name = target.get('pref_name', 'N/A')
                
                output += f"### {i}. {pref_name}\n"
                output += f"   - **ChEMBL ID:** {target_id}\n"
                output += f"   - **Type:** {target.get('target_type', 'N/A')}\n"
                output += f"   - **Organism:** {target.get('organism', 'N/A')}\n"
                output += "\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error searching by UniProt: {e}")
        error_msg = f"Error searching by UniProt: {str(e)}"
        return pd.DataFrame(), error_msg


def get_target_bioactivities(
    target_chembl_id: str,
    activity_type: Optional[str] = None,
    limit: int = 100,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Get bioactivity measurements for a specific target.
    
    Args:
        target_chembl_id: ChEMBL target ID (e.g., "CHEMBL2095173")
        activity_type: Activity type filter (e.g., "IC50", "Ki", "EC50")
        limit: Number of results to return (default: 100)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with bioactivities, formatted output string)
        
    Examples:
        >>> # Get all IC50 values for COX-2
        >>> df, output = get_target_bioactivities(
        ...     "CHEMBL2095173",
        ...     activity_type="IC50"
        ... )
        >>> print(output)
    """
    try:
        client = ChEMBLClient()
        results = client.search_activities(
            target_chembl_id=target_chembl_id,
            activity_type=activity_type,
            limit=limit
        )
        
        activities = results.get('activities', [])
        
        # Convert to DataFrame
        df = pd.DataFrame(activities)
        
        # Format output
        output = f"# Target Bioactivities\n\n"
        output += f"**Target:** {target_chembl_id}\n"
        if activity_type:
            output += f"**Activity Type:** {activity_type}\n"
        output += f"**Results found:** {len(activities)}\n\n"
        
        if not activities:
            output += "No bioactivity data found for this target.\n"
        else:
            # Group by activity type
            by_type = {}
            for act in activities:
                act_type = act.get('standard_type', 'Unknown')
                if act_type not in by_type:
                    by_type[act_type] = []
                by_type[act_type].append(act)
            
            output += f"## Activity Types Found: {len(by_type)}\n\n"
            for act_type, acts in by_type.items():
                output += f"- **{act_type}:** {len(acts)} measurements\n"
            
            output += "\n## Sample Bioactivities:\n\n"
            
            for i, act in enumerate(activities[:20], 1):
                mol_id = act.get('molecule_chembl_id', 'N/A')
                act_type = act.get('standard_type', 'N/A')
                value = act.get('standard_value', 'N/A')
                units = act.get('standard_units', '')
                relation = act.get('standard_relation', '')
                
                output += f"### {i}. Compound: {mol_id}\n"
                output += f"   - **Activity:** {act_type}\n"
                
                # Format value with relation and units
                value_str = f"{relation} {value} {units}".strip() if value != 'N/A' else 'N/A'
                output += f"   - **Value:** {value_str}\n"
                
                # Assay info
                if act.get('assay_chembl_id'):
                    output += f"   - **Assay:** {act['assay_chembl_id']}\n"
                if act.get('assay_description'):
                    desc = str(act['assay_description'])[:100]
                    output += f"   - **Assay Description:** {desc}...\n"
                
                output += "\n"
            
            if len(activities) > 20:
                output += f"\n... and {len(activities) - 20} more activities\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error getting target bioactivities: {e}")
        error_msg = f"Error getting target bioactivities: {str(e)}"
        return pd.DataFrame(), error_msg


def get_compounds_for_target(
    target_chembl_id: str,
    activity_threshold: Optional[float] = None,
    activity_type: str = "IC50",
    limit: int = 50,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Get active compounds for a specific target.
    
    Args:
        target_chembl_id: ChEMBL target ID (e.g., "CHEMBL2095173")
        activity_threshold: Maximum activity value threshold (e.g., 1000 for IC50 < 1000nM)
        activity_type: Activity type to filter (default: "IC50")
        limit: Number of results to return (default: 50)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with compounds, formatted output string)
        
    Examples:
        >>> # Get compounds with IC50 < 100nM for COX-2
        >>> df, output = get_compounds_for_target(
        ...     "CHEMBL2095173",
        ...     activity_threshold=100,
        ...     activity_type="IC50"
        ... )
        >>> print(output)
    """
    try:
        client = ChEMBLClient()
        
        # Get bioactivities
        results = client.search_activities(
            target_chembl_id=target_chembl_id,
            activity_type=activity_type,
            limit=limit * 3  # Get more to filter
        )
        
        activities = results.get('activities', [])
        
        # Filter by threshold if specified
        if activity_threshold is not None:
            filtered = []
            for act in activities:
                value = act.get('standard_value')
                relation = act.get('standard_relation', '=')
                
                if value is not None:
                    try:
                        value = float(value)
                        # Only include if value is below threshold (more potent)
                        if relation in ['=', '<', '<='] and value <= activity_threshold:
                            filtered.append(act)
                    except (ValueError, TypeError):
                        pass
            
            activities = filtered[:limit]
        else:
            activities = activities[:limit]
        
        # Extract unique compounds
        seen_compounds = set()
        compounds_data = []
        
        for act in activities:
            mol_id = act.get('molecule_chembl_id')
            if mol_id and mol_id not in seen_compounds:
                compounds_data.append({
                    'molecule_chembl_id': mol_id,
                    'activity_type': act.get('standard_type'),
                    'activity_value': act.get('standard_value'),
                    'activity_units': act.get('standard_units'),
                    'activity_relation': act.get('standard_relation'),
                    'assay_chembl_id': act.get('assay_chembl_id'),
                    'pchembl_value': act.get('pchembl_value')
                })
                seen_compounds.add(mol_id)
        
        # Convert to DataFrame
        df = pd.DataFrame(compounds_data)
        
        # Format output
        output = f"# Active Compounds for Target\n\n"
        output += f"**Target:** {target_chembl_id}\n"
        output += f"**Activity Type:** {activity_type}\n"
        if activity_threshold is not None:
            output += f"**Threshold:** ≤ {activity_threshold}\n"
        output += f"**Unique compounds found:** {len(compounds_data)}\n\n"
        
        if not compounds_data:
            output += "No compounds found matching the criteria.\n"
        else:
            output += "## Active Compounds:\n\n"
            
            for i, comp in enumerate(compounds_data[:20], 1):
                mol_id = comp['molecule_chembl_id']
                value = comp['activity_value']
                units = comp['activity_units']
                relation = comp['activity_relation']
                
                output += f"### {i}. {mol_id}\n"
                
                # Format activity
                if value is not None:
                    value_str = f"{relation} {value} {units}".strip()
                    output += f"   - **{activity_type}:** {value_str}\n"
                
                # pChEMBL value (standardized potency)
                if comp.get('pchembl_value'):
                    output += f"   - **pChEMBL:** {comp['pchembl_value']}\n"
                
                output += "\n"
            
            if len(compounds_data) > 20:
                output += f"\n... and {len(compounds_data) - 20} more compounds\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error getting compounds for target: {e}")
        error_msg = f"Error getting compounds for target: {str(e)}"
        return pd.DataFrame(), error_msg

