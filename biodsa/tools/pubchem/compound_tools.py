"""
PubChem Compound Search and Retrieval Tools

Functions for searching and retrieving compound information.
"""

import pandas as pd
from typing import Dict, Any, Optional, List, Union
from .client import PubChemClient


def search_compounds(
    query: str,
    search_type: str = 'name',
    max_records: int = 100,
    client: Optional[PubChemClient] = None
) -> pd.DataFrame:
    """
    Search PubChem database for compounds.
    
    Args:
        query: Search query (compound name, CAS, formula, etc.)
        search_type: Type of search (name, smiles, inchi, formula, cid)
        max_records: Maximum number of results
        client: Optional PubChemClient instance
        
    Returns:
        DataFrame with compound results
        
    Example:
        >>> df = search_compounds("aspirin", max_records=10)
        >>> print(df[['CID', 'MolecularFormula', 'MolecularWeight']])
    """
    if client is None:
        client = PubChemClient()
    
    try:
        # Get CIDs
        cids = client.search_compounds(query, search_type=search_type, max_records=max_records)
        
        if not cids:
            return pd.DataFrame()
        
        # Get properties for the first 10 CIDs
        display_cids = cids[:10]
        cid_string = ','.join(str(cid) for cid in display_cids)
        
        properties = client.get_compound_properties(cid_string, properties=[
            'MolecularFormula', 'MolecularWeight', 'CanonicalSMILES',
            'IUPACName', 'XLogP', 'TPSA'
        ])
        
        # Convert to DataFrame
        if isinstance(properties, dict) and 'CID' in properties:
            return pd.DataFrame([properties])
        
        return pd.DataFrame(properties) if isinstance(properties, list) else pd.DataFrame()
        
    except Exception as e:
        raise Exception(f"Error searching compounds: {str(e)}")


def get_compound_info(
    cid: Union[int, str],
    client: Optional[PubChemClient] = None
) -> Dict[str, Any]:
    """
    Get detailed information for a specific compound.
    
    Args:
        cid: PubChem Compound ID
        client: Optional PubChemClient instance
        
    Returns:
        Dict with compound information
        
    Example:
        >>> info = get_compound_info(2244)  # Aspirin
        >>> print(info['PC_Compounds'][0]['props'])
    """
    if client is None:
        client = PubChemClient()
    
    try:
        return client.get_compound_info(cid)
    except Exception as e:
        raise Exception(f"Error getting compound info: {str(e)}")


def get_compound_synonyms(
    cid: Union[int, str],
    client: Optional[PubChemClient] = None
) -> List[str]:
    """
    Get all names and synonyms for a compound.
    
    Args:
        cid: PubChem Compound ID
        client: Optional PubChemClient instance
        
    Returns:
        List of synonyms
        
    Example:
        >>> synonyms = get_compound_synonyms(2244)
        >>> print(synonyms[:10])  # First 10 synonyms
    """
    if client is None:
        client = PubChemClient()
    
    try:
        return client.get_compound_synonyms(cid)
    except Exception as e:
        raise Exception(f"Error getting synonyms: {str(e)}")


def search_by_smiles(
    smiles: str,
    client: Optional[PubChemClient] = None
) -> Optional[Dict[str, Any]]:
    """
    Search for a compound by SMILES string (exact match).
    
    Args:
        smiles: SMILES string
        client: Optional PubChemClient instance
        
    Returns:
        Dict with compound info if found, None otherwise
        
    Example:
        >>> info = search_by_smiles("CC(=O)OC1=CC=CC=C1C(=O)O")  # Aspirin
        >>> if info:
        >>>     print(f"Found CID: {info['cid']}")
    """
    if client is None:
        client = PubChemClient()
    
    try:
        cid = client.search_by_smiles(smiles)
        if cid:
            properties = client.get_compound_properties(cid)
            return {
                'cid': cid,
                'query_smiles': smiles,
                'properties': properties
            }
        return None
    except Exception as e:
        raise Exception(f"Error searching by SMILES: {str(e)}")


def search_by_inchi(
    inchi: str,
    client: Optional[PubChemClient] = None
) -> Optional[Dict[str, Any]]:
    """
    Search for a compound by InChI or InChI key.
    
    Args:
        inchi: InChI string or InChI key
        client: Optional PubChemClient instance
        
    Returns:
        Dict with compound info if found, None otherwise
        
    Example:
        >>> info = search_by_inchi("InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)")
        >>> if info:
        >>>     print(f"Found CID: {info['cid']}")
    """
    if client is None:
        client = PubChemClient()
    
    try:
        cid = client.search_by_inchi(inchi)
        if cid:
            properties = client.get_compound_properties(cid)
            return {
                'cid': cid,
                'query_inchi': inchi,
                'properties': properties
            }
        return None
    except Exception as e:
        raise Exception(f"Error searching by InChI: {str(e)}")


def search_by_cas_number(
    cas_number: str,
    client: Optional[PubChemClient] = None
) -> Optional[Dict[str, Any]]:
    """
    Search for a compound by CAS Registry Number.
    
    Args:
        cas_number: CAS number (e.g., "50-78-2")
        client: Optional PubChemClient instance
        
    Returns:
        Dict with compound info if found, None otherwise
        
    Example:
        >>> info = search_by_cas_number("50-78-2")  # Aspirin
        >>> if info:
        >>>     print(f"Found CID: {info['cid']}")
    """
    if client is None:
        client = PubChemClient()
    
    try:
        cid = client.search_by_cas(cas_number)
        if cid:
            properties = client.get_compound_properties(cid)
            return {
                'cid': cid,
                'cas_number': cas_number,
                'properties': properties
            }
        return None
    except Exception as e:
        raise Exception(f"Error searching by CAS number: {str(e)}")


def batch_compound_lookup(
    cids: List[int],
    operation: str = 'property',
    client: Optional[PubChemClient] = None
) -> List[Dict[str, Any]]:
    """
    Process multiple compound IDs efficiently.
    
    Args:
        cids: List of PubChem CIDs (max 200)
        operation: Operation to perform (property, synonyms)
        client: Optional PubChemClient instance
        
    Returns:
        List of results for each CID
        
    Example:
        >>> results = batch_compound_lookup([2244, 3672, 5090])
        >>> for r in results:
        >>>     if r['success']:
        >>>         print(f"CID {r['cid']}: {r['data']}")
    """
    if client is None:
        client = PubChemClient()
    
    try:
        return client.batch_compound_lookup(cids, operation=operation)
    except Exception as e:
        raise Exception(f"Error in batch lookup: {str(e)}")

