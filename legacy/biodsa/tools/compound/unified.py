"""Unified compound search and retrieval across multiple APIs.

This module aggregates compound information from:
- KEGG Compound Database
- PubChem
"""

import logging
import json
from typing import Optional, Dict, Any, List, Tuple

from biodsa.tools.kegg.client import KEGGClient
from biodsa.tools.pubchem.client import PubChemClient


# ================================================
# Unified Compound Search Function
# ================================================

def search_compounds_unified(
    search_term: str,
    search_type: str = "name",
    limit_per_source: int = 10,
    sources: Optional[List[str]] = None,
    save_path: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Search for compounds across multiple databases with a simple search term.
    
    This function queries KEGG Compound and PubChem databases and aggregates
    the results, providing a comprehensive view of compound information.
    
    Args:
        search_term: Search query (compound name, CAS number, formula, SMILES, etc.)
        search_type: Type of search ('name', 'formula', 'smiles', 'inchi', 'cas'). Default: 'name'
        limit_per_source: Maximum results per source (default: 10)
        sources: List of sources to search. If None, searches all.
                 Options: ['kegg', 'pubchem']
        save_path: Optional path to save aggregated results
    
    Returns:
        Tuple of (dict of results by source, formatted output string)
        
    Examples:
        >>> # Search for aspirin across all sources
        >>> results, output = search_compounds_unified("aspirin", limit_per_source=5)
        >>> print(output)  # Prints formatted results
    """
    if sources is None:
        sources = ['kegg', 'pubchem']
    
    results = {}
    summaries = []
    errors = []
    
    # Search KEGG Compound Database
    if 'kegg' in sources:
        try:
            kegg_client = KEGGClient()
            kegg_results = kegg_client.search_compounds(
                query=search_term,
                search_type=search_type if search_type in ['name', 'formula', 'exact_mass', 'mol_weight'] else 'name',
                max_results=limit_per_source
            )
            results['kegg'] = kegg_results
            summaries.append(f"**KEGG Compound:** Found {len(kegg_results)} compounds")
        except Exception as e:
            logging.error(f"KEGG search failed: {e}")
            results['kegg'] = []
            errors.append(f"KEGG: {str(e)}")
    
    # Search PubChem
    if 'pubchem' in sources:
        try:
            pubchem_client = PubChemClient()
            
            # Map search_type to PubChem's expected format
            pubchem_search_type = search_type
            if pubchem_search_type in ['exact_mass', 'mol_weight', 'cas']:
                pubchem_search_type = 'name'
            
            pubchem_cids = pubchem_client.search_compounds(
                query=search_term,
                search_type=pubchem_search_type,
                max_records=limit_per_source
            )
            
            pubchem_compounds = []
            if pubchem_cids:
                # Get properties for first 10 compounds
                display_cids = pubchem_cids[:min(10, len(pubchem_cids))]
                for cid in display_cids:
                    try:
                        props = pubchem_client.get_compound_properties(cid, properties=[
                            'MolecularFormula', 'MolecularWeight', 'CanonicalSMILES',
                            'IUPACName', 'Title'
                        ])
                        props['CID'] = cid
                        pubchem_compounds.append(props)
                    except Exception:
                        pass
            
            results['pubchem'] = {
                'cids': pubchem_cids,
                'compounds': pubchem_compounds
            }
            summaries.append(f"**PubChem:** Found {len(pubchem_cids)} compounds")
        except Exception as e:
            logging.error(f"PubChem search failed: {e}")
            results['pubchem'] = {'cids': [], 'compounds': []}
            errors.append(f"PubChem: {str(e)}")
    
    # Build formatted output string
    output = "# Unified Compound Search Results\n\n"
    output += f"## Search Term: '{search_term}'\n"
    output += f"## Search Type: {search_type}\n\n"
    
    # Count total results
    total_results = 0
    if 'kegg' in results:
        total_results += len(results['kegg']) if isinstance(results['kegg'], list) else 0
    if 'pubchem' in results:
        total_results += len(results['pubchem'].get('cids', []))
    
    output += f"**Total results:** {total_results} across {len(sources)} sources\n\n"
    output += "### Results by Source:\n"
    for s in summaries:
        output += f"- {s}\n"
    
    if errors:
        output += "\n### Errors:\n"
        for e in errors:
            output += f"- ⚠️ {e}\n"
    
    output += "\n" + "="*80 + "\n\n"
    
    # Format KEGG results
    if 'kegg' in results and results['kegg']:
        kegg_compounds = results['kegg']
        output += f"## KEGG COMPOUND Results\n\n"
        output += f"Found {len(kegg_compounds)} compounds from KEGG:\n\n"
        for idx, compound in enumerate(kegg_compounds[:10], 1):
            compound_id = compound.get('id', 'N/A')
            description = compound.get('description', 'N/A')
            output += f"**{idx}. {compound_id}** - {description}\n"
        if len(kegg_compounds) > 10:
            output += f"\n... and {len(kegg_compounds) - 10} more compounds\n"
        output += "\n"
    
    # Format PubChem results
    if 'pubchem' in results:
        pubchem_data = results['pubchem']
        pubchem_compounds = pubchem_data.get('compounds', [])
        total_cids = len(pubchem_data.get('cids', []))
        
        if pubchem_compounds:
            output += f"## PUBCHEM Results\n\n"
            output += f"Found {total_cids} compounds from PubChem:\n\n"
            for idx, compound in enumerate(pubchem_compounds, 1):
                cid = compound.get('CID', 'N/A')
                title = compound.get('Title', 'Unknown')
                formula = compound.get('MolecularFormula', 'N/A')
                mol_weight = compound.get('MolecularWeight', 'N/A')
                output += f"**{idx}. CID {cid}** - {title}\n"
                output += f"  - Formula: {formula}, MW: {mol_weight}\n"
            if total_cids > len(pubchem_compounds):
                output += f"\n... and {total_cids - len(pubchem_compounds)} more compounds\n"
            output += "\n"
    
    # Save results if requested
    if save_path:
        try:
            save_data = {
                'search_term': search_term,
                'search_type': search_type,
                'sources': sources,
                'results': results
            }
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            output += f"\n**Results saved to:** {save_path}\n"
        except Exception as e:
            logging.error(f"Error saving results: {e}")
            output += f"\n⚠️ **Error saving results:** {e}\n"
    
    return results, output


# ================================================
# Unified Compound Fetch Function
# ================================================

def fetch_compound_details_unified(
    compound_id: str,
    id_type: Optional[str] = None,
    sources: Optional[List[str]] = None,
    include_reactions: bool = True,
    include_pathways: bool = True,
    save_path: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Fetch detailed compound information using any compound identifier.
    
    This function automatically detects the ID type (if not specified) and
    queries relevant databases to fetch comprehensive compound information.
    
    Args:
        compound_id: Compound identifier (KEGG ID like C00002, PubChem CID like 2244)
        id_type: Type of ID. If None, will attempt to detect.
                 Options: 'kegg', 'pubchem', 'name'
        sources: List of sources to fetch from. If None, fetches from detected source.
                 Options: ['kegg', 'pubchem']
        include_reactions: Include reactions involving the compound (KEGG only)
        include_pathways: Include pathways containing the compound
        save_path: Optional path to save results as JSON
    
    Returns:
        Tuple of (dict of compound details by source, formatted output string)
        
    Examples:
        >>> # Fetch by KEGG ID
        >>> details, output = fetch_compound_details_unified("C00002")
        >>> print(output)
        
        >>> # Fetch by PubChem CID
        >>> details, output = fetch_compound_details_unified("2244", id_type='pubchem')
        >>> print(output)
    """
    # Auto-detect ID type if not specified
    if id_type is None:
        id_type = _detect_compound_id_type(compound_id)
    
    if sources is None:
        sources = ['kegg'] if id_type == 'kegg' else ['pubchem']
    
    details = {}
    summaries = []
    errors = []
    
    # Fetch from KEGG
    if 'kegg' in sources and id_type in ['kegg', 'name']:
        try:
            kegg_client = KEGGClient()
            
            if id_type == 'kegg':
                # Clean compound ID
                clean_id = compound_id.replace('cpd:', '')
                compound_info = kegg_client.get_compound_info(clean_id)
                details['kegg'] = {'compound_info': compound_info, 'compound_id': clean_id}
                summaries.append(f"**KEGG:** Found compound information")
                
                # Get reactions if requested
                if include_reactions:
                    try:
                        reactions = kegg_client.get_compound_reactions(clean_id)
                        details['kegg']['reactions'] = reactions
                    except Exception as e:
                        details['kegg']['reactions_error'] = str(e)
                
                # Get pathways if requested
                if include_pathways:
                    try:
                        pathways = kegg_client.find_related_entries('compound', 'pathway', [clean_id])
                        details['kegg']['pathways'] = pathways
                    except Exception as e:
                        details['kegg']['pathways_error'] = str(e)
            
            elif id_type == 'name':
                # Search first, then fetch
                search_results = kegg_client.search_compounds(compound_id, max_results=1)
                if search_results:
                    kegg_id = search_results[0]['id'].replace('cpd:', '')
                    compound_info = kegg_client.get_compound_info(kegg_id)
                    details['kegg'] = {'compound_info': compound_info, 'compound_id': kegg_id}
                    summaries.append(f"**KEGG:** Found compound information")
                else:
                    summaries.append(f"**KEGG:** No results found")
        except Exception as e:
            logging.error(f"KEGG fetch failed: {e}")
            errors.append(f"KEGG: {str(e)}")
    
    # Fetch from PubChem
    if 'pubchem' in sources and id_type in ['pubchem', 'name']:
        try:
            pubchem_client = PubChemClient()
            
            if id_type == 'pubchem':
                cid = compound_id.replace('CID:', '')
                
                # Get compound info
                compound_info = pubchem_client.get_compound_info(cid)
                
                # Get properties
                props = pubchem_client.get_compound_properties(cid, properties=[
                    'MolecularFormula', 'MolecularWeight', 'CanonicalSMILES',
                    'IUPACName', 'XLogP', 'TPSA', 'HBondDonorCount', 'HBondAcceptorCount',
                    'RotatableBondCount', 'Title'
                ])
                
                # Get synonyms
                try:
                    synonyms = pubchem_client.get_compound_synonyms(cid)
                except Exception:
                    synonyms = []
                
                details['pubchem'] = {
                    'compound_id': cid,
                    'compound_info': compound_info,
                    'properties': props,
                    'synonyms': synonyms[:20] if synonyms else []
                }
                summaries.append(f"**PubChem:** Found compound information")
            
            elif id_type == 'name':
                # Search first, then fetch
                cids = pubchem_client.search_compounds(compound_id, search_type='name', max_records=1)
                if cids:
                    cid = cids[0]
                    props = pubchem_client.get_compound_properties(cid, properties=[
                        'MolecularFormula', 'MolecularWeight', 'CanonicalSMILES',
                        'IUPACName', 'XLogP', 'TPSA', 'Title'
                    ])
                    details['pubchem'] = {
                        'compound_id': cid,
                        'properties': props
                    }
                    summaries.append(f"**PubChem:** Found compound information")
                else:
                    summaries.append(f"**PubChem:** No results found")
        except Exception as e:
            logging.error(f"PubChem fetch failed: {e}")
            errors.append(f"PubChem: {str(e)}")
    
    # Build formatted output string
    output = "# Unified Compound Details\n\n"
    output += f"## Query: '{compound_id}' (Type: {id_type})\n\n"
    
    output += "### Fetch Summary:\n"
    for s in summaries:
        output += f"- {s}\n"
    
    if errors:
        output += "\n### Errors:\n"
        for e in errors:
            output += f"- ⚠️ {e}\n"
    
    output += "\n" + "="*80 + "\n\n"
    
    # Format KEGG details
    if 'kegg' in details:
        kegg_data = details['kegg']
        compound_info = kegg_data.get('compound_info', {})
        
        output += "## KEGG Compound Details\n\n"
        output += f"**ID:** {kegg_data.get('compound_id', 'N/A')}\n"
        output += f"**Name:** {compound_info.get('NAME', 'Unknown')}\n"
        
        if 'FORMULA' in compound_info:
            output += f"**Formula:** {compound_info['FORMULA']}\n"
        if 'EXACT_MASS' in compound_info:
            output += f"**Exact Mass:** {compound_info['EXACT_MASS']}\n"
        if 'MOL_WEIGHT' in compound_info:
            output += f"**Molecular Weight:** {compound_info['MOL_WEIGHT']}\n"
        
        # Reactions
        reactions = kegg_data.get('reactions', [])
        if reactions:
            output += f"\n**Reactions ({len(reactions)}):**\n"
            for i, rxn in enumerate(reactions[:5], 1):
                output += f"  {i}. {rxn.get('target', 'Unknown')}\n"
            if len(reactions) > 5:
                output += f"  ... and {len(reactions) - 5} more\n"
        
        # Pathways
        pathways = kegg_data.get('pathways', [])
        if pathways:
            output += f"\n**Pathways ({len(pathways)}):**\n"
            for i, pathway in enumerate(pathways[:5], 1):
                output += f"  {i}. {pathway.get('target', 'Unknown')}\n"
            if len(pathways) > 5:
                output += f"  ... and {len(pathways) - 5} more\n"
        
        output += f"\n**KEGG URL:** https://www.kegg.jp/entry/{kegg_data.get('compound_id', '')}\n\n"
    
    # Format PubChem details
    if 'pubchem' in details:
        pubchem_data = details['pubchem']
        props = pubchem_data.get('properties', {})
        
        output += "## PubChem Compound Details\n\n"
        output += f"**CID:** {pubchem_data.get('compound_id', 'N/A')}\n"
        output += f"**Name:** {props.get('Title', 'Unknown')}\n"
        output += f"**Formula:** {props.get('MolecularFormula', 'N/A')}\n"
        output += f"**Molecular Weight:** {props.get('MolecularWeight', 'N/A')}\n"
        output += f"**IUPAC Name:** {props.get('IUPACName', 'N/A')}\n"
        
        output += "\n**Chemical Properties:**\n"
        output += f"  - XLogP: {props.get('XLogP', 'N/A')}\n"
        output += f"  - TPSA: {props.get('TPSA', 'N/A')}\n"
        output += f"  - H-Bond Donors: {props.get('HBondDonorCount', 'N/A')}\n"
        output += f"  - H-Bond Acceptors: {props.get('HBondAcceptorCount', 'N/A')}\n"
        
        smiles = props.get('CanonicalSMILES', 'N/A')
        if len(str(smiles)) > 80:
            smiles = str(smiles)[:80] + "..."
        output += f"  - SMILES: {smiles}\n"
        
        # Synonyms
        synonyms = pubchem_data.get('synonyms', [])
        if synonyms:
            output += f"\n**Synonyms ({len(synonyms)}):**\n"
            for syn in synonyms[:5]:
                output += f"  - {syn}\n"
            if len(synonyms) > 5:
                output += f"  ... and {len(synonyms) - 5} more\n"
        
        cid = pubchem_data.get('compound_id', '')
        output += f"\n**PubChem URL:** https://pubchem.ncbi.nlm.nih.gov/compound/{cid}\n\n"
    
    # Save results if requested
    if save_path:
        try:
            save_data = {
                'compound_id': compound_id,
                'id_type': id_type,
                'sources': sources,
                'details': details
            }
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent=2, default=str)
            output += f"\n**Details saved to:** {save_path}\n"
        except Exception as e:
            logging.error(f"Error saving details: {e}")
            output += f"\n⚠️ **Error saving details:** {e}\n"
    
    return details, output


# ================================================
# Helper Functions
# ================================================

def _detect_compound_id_type(compound_id: str) -> str:
    """
    Detect the type of compound identifier.
    
    Args:
        compound_id: Compound identifier string
    
    Returns:
        Detected ID type: 'kegg', 'pubchem', or 'name'
    """
    compound_id = compound_id.strip()
    
    # KEGG Compound ID: C00000 format or cpd:C00000
    if compound_id.startswith('cpd:') or (compound_id.startswith('C') and len(compound_id) == 6 and compound_id[1:].isdigit()):
        return 'kegg'
    
    # PubChem CID: numeric or CID:number
    if compound_id.upper().startswith('CID:'):
        return 'pubchem'
    
    if compound_id.isdigit():
        return 'pubchem'
    
    # Default to name search
    return 'name'

