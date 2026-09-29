"""Compound search and retrieval tools for ChEMBL Database.

This module provides tools for searching compounds and retrieving
detailed compound information from the ChEMBL Database.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .client import ChEMBLClient

logger = logging.getLogger(__name__)


def search_compounds(
    query: str,
    limit: int = 25,
    offset: int = 0,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Search ChEMBL database for compounds by name, synonym, or identifier.
    
    Args:
        query: Search query (compound name, synonym, or identifier)
        limit: Number of results to return (1-1000, default: 25)
        offset: Number of results to skip (default: 0)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with compound results, formatted output string)
        
    Examples:
        >>> df, output = search_compounds("aspirin", limit=10)
        >>> print(output)
        >>> print(df[['molecule_chembl_id', 'pref_name']])
    """
    try:
        client = ChEMBLClient()
        results = client.search_compounds(query, limit=limit, offset=offset)
        
        molecules = results.get('molecules', [])
        
        # Convert to DataFrame
        df = pd.DataFrame(molecules)
        
        # Format output
        output = f"# Compound Search Results\n\n"
        output += f"**Query:** '{query}'\n"
        output += f"**Results found:** {len(molecules)}\n\n"
        
        if not molecules:
            output += "No compounds found for this query.\n"
        else:
            output += "## Top Results:\n\n"
            for i, mol in enumerate(molecules[:10], 1):
                output += f"### {i}. {mol.get('pref_name', 'N/A')}\n"
                output += f"   - **ChEMBL ID:** {mol.get('molecule_chembl_id', 'N/A')}\n"
                output += f"   - **Type:** {mol.get('molecule_type', 'N/A')}\n"
                
                # Add molecular properties if available
                props = mol.get('molecule_properties', {})
                if props:
                    output += f"   - **MW:** {props.get('full_mwt', props.get('molecular_weight', 'N/A'))}\n"
                    output += f"   - **LogP:** {props.get('alogp', 'N/A')}\n"
                
                # Add max phase if available
                if mol.get('max_phase'):
                    output += f"   - **Max Phase:** {mol.get('max_phase')}\n"
                
                output += "\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error searching compounds: {e}")
        error_msg = f"Error searching compounds: {str(e)}"
        return pd.DataFrame(), error_msg


def get_compound_details(
    chembl_id: str,
    save_path: Optional[str] = None
) -> Tuple[Dict[str, Any], str]:
    """Get detailed information for a specific compound by ChEMBL ID.
    
    Args:
        chembl_id: ChEMBL compound ID (e.g., "CHEMBL25")
        save_path: Optional path to save results as JSON
        
    Returns:
        Tuple of (dictionary with compound details, formatted output string)
        
    Examples:
        >>> details, output = get_compound_details("CHEMBL25")
        >>> print(output)
        >>> print(details['molecule_properties'])
    """
    try:
        client = ChEMBLClient()
        compound = client.get_compound_by_id(chembl_id)
        
        # Format output
        output = f"# Compound Details\n\n"
        output += f"## {compound.get('pref_name', 'N/A')} ({chembl_id})\n\n"
        output += f"**ChEMBL ID:** {compound.get('molecule_chembl_id', 'N/A')}\n"
        output += f"**Type:** {compound.get('molecule_type', 'N/A')}\n"
        
        # Max phase (drug development)
        if compound.get('max_phase') is not None:
            phases = ['Preclinical', 'Phase I', 'Phase II', 'Phase III', 'Approved']
            phase = compound.get('max_phase', 0)
            # Ensure phase is an integer
            try:
                phase = int(phase)
                output += f"**Development Phase:** {phases[phase] if 0 <= phase < len(phases) else 'Unknown'}\n"
            except (ValueError, TypeError):
                output += f"**Development Phase:** {phase}\n"
        
        output += "\n"
        
        # Molecular properties
        props = compound.get('molecule_properties', {})
        if props:
            output += "### Molecular Properties\n"
            output += f"- **Molecular Weight:** {props.get('full_mwt', props.get('molecular_weight', 'N/A'))} Da\n"
            output += f"- **LogP:** {props.get('alogp', 'N/A')}\n"
            output += f"- **H-Bond Donors:** {props.get('hbd', 'N/A')}\n"
            output += f"- **H-Bond Acceptors:** {props.get('hba', 'N/A')}\n"
            output += f"- **Polar Surface Area:** {props.get('psa', 'N/A')} Ų\n"
            output += f"- **Rotatable Bonds:** {props.get('rtb', 'N/A')}\n"
            output += f"- **Lipinski Violations:** {props.get('num_ro5_violations', 'N/A')}\n"
            output += "\n"
        
        # Structure information
        structures = compound.get('molecule_structures', {})
        if structures:
            output += "### Structure Information\n"
            if structures.get('canonical_smiles'):
                output += f"- **SMILES:** {structures['canonical_smiles']}\n"
            if structures.get('standard_inchi_key'):
                output += f"- **InChI Key:** {structures['standard_inchi_key']}\n"
            output += "\n"
        
        # Synonyms
        synonyms = compound.get('molecule_synonyms', [])
        if synonyms:
            output += f"### Synonyms ({len(synonyms)} total)\n"
            for syn in synonyms[:10]:
                output += f"- {syn.get('molecule_synonym', syn.get('synonyms', 'N/A'))}\n"
            output += "\n"
        
        # Cross references
        xrefs = compound.get('cross_references', [])
        if xrefs:
            output += f"### External References ({len(xrefs)} total)\n"
            # Group by source
            by_source = {}
            for xref in xrefs:
                source = xref.get('xref_src', 'Unknown')
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(xref.get('xref_id', 'N/A'))
            
            for source, ids in list(by_source.items())[:5]:
                output += f"- **{source}:** {', '.join(ids[:3])}\n"
            output += "\n"
        
        # Save if path provided
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(compound, f, indent=2)
            output += f"\n**Full details saved to:** {save_path}\n"
        
        return compound, output
    
    except Exception as e:
        logger.error(f"Error getting compound details: {e}")
        error_msg = f"Error getting compound details: {str(e)}"
        return {}, error_msg


def search_similar_compounds(
    smiles: str,
    similarity: int = 70,
    limit: int = 25,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Find chemically similar compounds using Tanimoto similarity.
    
    Args:
        smiles: SMILES string of the query molecule
        similarity: Similarity threshold percentage (0-100, default: 70)
        limit: Number of results to return (default: 25)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with similar compounds, formatted output string)
        
    Examples:
        >>> df, output = search_similar_compounds(
        ...     "CC(=O)Oc1ccccc1C(=O)O",
        ...     similarity=70
        ... )
        >>> print(output)
    """
    try:
        client = ChEMBLClient()
        results = client.search_similar_compounds(smiles, similarity=similarity, limit=limit)
        
        molecules = results.get('molecules', [])
        
        # Convert to DataFrame
        df = pd.DataFrame(molecules)
        
        # Format output
        output = f"# Similar Compounds Search\n\n"
        output += f"**Query SMILES:** {smiles}\n"
        output += f"**Similarity threshold:** {similarity}%\n"
        output += f"**Results found:** {len(molecules)}\n\n"
        
        if not molecules:
            output += "No similar compounds found.\n"
        else:
            output += "## Top Results:\n\n"
            for i, mol in enumerate(molecules[:10], 1):
                output += f"### {i}. {mol.get('pref_name', 'N/A')}\n"
                output += f"   - **ChEMBL ID:** {mol.get('molecule_chembl_id', 'N/A')}\n"
                output += f"   - **Similarity:** {mol.get('similarity', 'N/A')}\n"
                
                # Add molecular properties
                props = mol.get('molecule_properties', {})
                if props:
                    mw = props.get('full_mwt', props.get('molecular_weight'))
                    if mw:
                        output += f"   - **MW:** {mw} Da\n"
                
                output += "\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error searching similar compounds: {e}")
        error_msg = f"Error searching similar compounds: {str(e)}"
        return pd.DataFrame(), error_msg


def search_substructure(
    smiles: str,
    limit: int = 25,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Find compounds containing specific substructures.
    
    Args:
        smiles: SMILES string of the substructure query
        limit: Number of results to return (default: 25)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with matching compounds, formatted output string)
        
    Examples:
        >>> df, output = search_substructure("c1ccccc1", limit=10)
        >>> print(output)
    """
    try:
        client = ChEMBLClient()
        results = client.search_substructure(smiles, limit=limit)
        
        molecules = results.get('molecules', [])
        
        # Convert to DataFrame
        df = pd.DataFrame(molecules)
        
        # Format output
        output = f"# Substructure Search\n\n"
        output += f"**Query SMILES:** {smiles}\n"
        output += f"**Results found:** {len(molecules)}\n\n"
        
        if not molecules:
            output += "No compounds found with this substructure.\n"
        else:
            output += "## Top Results:\n\n"
            for i, mol in enumerate(molecules[:10], 1):
                output += f"### {i}. {mol.get('pref_name', 'N/A')}\n"
                output += f"   - **ChEMBL ID:** {mol.get('molecule_chembl_id', 'N/A')}\n"
                output += f"   - **Type:** {mol.get('molecule_type', 'N/A')}\n"
                output += "\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error searching substructure: {e}")
        error_msg = f"Error searching substructure: {str(e)}"
        return pd.DataFrame(), error_msg


def batch_compound_lookup(
    chembl_ids: List[str],
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Process multiple ChEMBL IDs efficiently.
    
    Args:
        chembl_ids: List of ChEMBL compound IDs (1-50)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with compounds, formatted output string)
        
    Examples:
        >>> df, output = batch_compound_lookup(["CHEMBL25", "CHEMBL59"])
        >>> print(output)
    """
    try:
        client = ChEMBLClient()
        results = client.batch_compound_lookup(chembl_ids)
        
        # Extract successful results
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        # Convert to DataFrame
        compound_data = []
        for result in successful:
            compound = result['data']
            compound_data.append({
                'chembl_id': compound.get('molecule_chembl_id'),
                'name': compound.get('pref_name'),
                'type': compound.get('molecule_type'),
                'max_phase': compound.get('max_phase'),
                'success': True
            })
        
        for result in failed:
            compound_data.append({
                'chembl_id': result['chembl_id'],
                'name': None,
                'type': None,
                'max_phase': None,
                'success': False,
                'error': result.get('error')
            })
        
        df = pd.DataFrame(compound_data)
        
        # Format output
        output = f"# Batch Compound Lookup\n\n"
        output += f"**Total queries:** {len(chembl_ids)}\n"
        output += f"**Successful:** {len(successful)}\n"
        output += f"**Failed:** {len(failed)}\n\n"
        
        if successful:
            output += "## Successful Lookups:\n\n"
            for i, result in enumerate(successful[:10], 1):
                compound = result['data']
                output += f"### {i}. {compound.get('pref_name', 'N/A')}\n"
                output += f"   - **ChEMBL ID:** {compound.get('molecule_chembl_id', 'N/A')}\n"
                output += "\n"
        
        if failed:
            output += "## Failed Lookups:\n\n"
            for result in failed:
                output += f"- **{result['chembl_id']}:** {result.get('error', 'Unknown error')}\n"
            output += "\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error in batch compound lookup: {e}")
        error_msg = f"Error in batch compound lookup: {str(e)}"
        return pd.DataFrame(), error_msg

