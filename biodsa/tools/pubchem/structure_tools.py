"""
PubChem Structure Analysis and Similarity Tools

Functions for structure similarity search and analysis.
"""

import pandas as pd
from typing import Dict, Any, Optional, List, Union
from .client import PubChemClient


def search_similar_compounds(
    smiles: str,
    threshold: int = 90,
    max_records: int = 100,
    client: Optional[PubChemClient] = None
) -> pd.DataFrame:
    """
    Find chemically similar compounds using Tanimoto similarity.
    
    Args:
        smiles: SMILES string of query molecule
        threshold: Similarity threshold (0-100, default: 90)
        max_records: Maximum number of results
        client: Optional PubChemClient instance
        
    Returns:
        DataFrame with similar compounds
        
    Example:
        >>> df = search_similar_compounds("CC(=O)OC1=CC=CC=C1C(=O)O", threshold=85)
        >>> print(df[['CID', 'MolecularWeight']])
    """
    if client is None:
        client = PubChemClient()
    
    try:
        cids = client.search_similar_compounds(smiles, threshold=threshold, max_records=max_records)
        
        if not cids:
            return pd.DataFrame()
        
        # Get properties for first 10 results
        display_cids = cids[:10]
        results = []
        
        for cid in display_cids:
            try:
                props = client.get_compound_properties(cid, properties=[
                    'MolecularFormula', 'MolecularWeight', 'CanonicalSMILES', 'IUPACName'
                ])
                props['CID'] = cid
                results.append(props)
            except:
                continue
        
        return pd.DataFrame(results)
        
    except Exception as e:
        raise Exception(f"Error searching similar compounds: {str(e)}")


def substructure_search(
    smiles: str,
    max_records: int = 100,
    client: Optional[PubChemClient] = None
) -> pd.DataFrame:
    """
    Find compounds containing a specific substructure.
    
    Args:
        smiles: SMILES string of substructure query
        max_records: Maximum number of results
        client: Optional PubChemClient instance
        
    Returns:
        DataFrame with matching compounds
        
    Example:
        >>> df = substructure_search("c1ccccc1", max_records=50)  # Benzene ring
        >>> print(df[['CID', 'MolecularFormula']])
    """
    if client is None:
        client = PubChemClient()
    
    try:
        cids = client.substructure_search(smiles, max_records=max_records)
        
        if not cids:
            return pd.DataFrame()
        
        # Get properties for first 10 results
        display_cids = cids[:10]
        results = []
        
        for cid in display_cids:
            try:
                props = client.get_compound_properties(cid, properties=[
                    'MolecularFormula', 'MolecularWeight', 'CanonicalSMILES'
                ])
                props['CID'] = cid
                results.append(props)
            except:
                continue
        
        return pd.DataFrame(results)
        
    except Exception as e:
        raise Exception(f"Error in substructure search: {str(e)}")


def superstructure_search(
    smiles: str,
    max_records: int = 100,
    client: Optional[PubChemClient] = None
) -> pd.DataFrame:
    """
    Find larger compounds that contain the query structure.
    
    Args:
        smiles: SMILES string of query structure
        max_records: Maximum number of results
        client: Optional PubChemClient instance
        
    Returns:
        DataFrame with matching compounds
        
    Example:
        >>> df = superstructure_search("CC", max_records=50)  # Ethyl group
        >>> print(df[['CID', 'MolecularFormula']])
    """
    if client is None:
        client = PubChemClient()
    
    try:
        cids = client.superstructure_search(smiles, max_records=max_records)
        
        if not cids:
            return pd.DataFrame()
        
        # Get properties for first 10 results
        display_cids = cids[:10]
        results = []
        
        for cid in display_cids:
            try:
                props = client.get_compound_properties(cid, properties=[
                    'MolecularFormula', 'MolecularWeight', 'CanonicalSMILES'
                ])
                props['CID'] = cid
                results.append(props)
            except:
                continue
        
        return pd.DataFrame(results)
        
    except Exception as e:
        raise Exception(f"Error in superstructure search: {str(e)}")


def get_3d_conformers(
    cid: Union[int, str],
    client: Optional[PubChemClient] = None
) -> Dict[str, Any]:
    """
    Get 3D conformer data and structural information.
    
    Args:
        cid: PubChem Compound ID
        client: Optional PubChemClient instance
        
    Returns:
        Dict with 3D conformer data
        
    Example:
        >>> conformers = get_3d_conformers(2244)
        >>> print(f"3D Volume: {conformers.get('Volume3D')}")
        >>> print(f"Conformer Count: {conformers.get('ConformerCount3D')}")
    """
    if client is None:
        client = PubChemClient()
    
    try:
        return client.get_3d_conformers(cid)
    except Exception as e:
        raise Exception(f"Error getting 3D conformers: {str(e)}")


def analyze_stereochemistry(
    cid: Union[int, str],
    client: Optional[PubChemClient] = None
) -> Dict[str, Any]:
    """
    Analyze stereochemistry, chirality, and isomer information.
    
    Args:
        cid: PubChem Compound ID
        client: Optional PubChemClient instance
        
    Returns:
        Dict with stereochemistry data
        
    Example:
        >>> stereo = analyze_stereochemistry(2244)
        >>> print(f"Atom stereo centers: {stereo.get('AtomStereoCount')}")
        >>> print(f"Defined centers: {stereo.get('DefinedAtomStereoCount')}")
    """
    if client is None:
        client = PubChemClient()
    
    try:
        return client.analyze_stereochemistry(cid)
    except Exception as e:
        raise Exception(f"Error analyzing stereochemistry: {str(e)}")

