"""
PubChem Cross-References and Integration Tools

Functions for accessing external database references and literature.
"""

from typing import Dict, Any, Optional, List, Union
from .client import PubChemClient


def get_external_references(
    cid: Union[int, str],
    client: Optional[PubChemClient] = None
) -> Dict[str, Any]:
    """
    Get links to external databases (ChEMBL, DrugBank, KEGG, etc.).
    
    Note: This function returns compound information which includes cross-references.
    
    Args:
        cid: PubChem Compound ID
        client: Optional PubChemClient instance
        
    Returns:
        Dict with external references
        
    Example:
        >>> refs = get_external_references(2244)
        >>> print(refs)
    """
    if client is None:
        client = PubChemClient()
    
    try:
        # Get full compound record which includes xrefs
        return client.get_compound_info(cid)
    except Exception as e:
        raise Exception(f"Error getting external references: {str(e)}")


def get_literature_references(
    cid: Union[int, str],
    client: Optional[PubChemClient] = None
) -> Dict[str, Any]:
    """
    Get PubMed citations and scientific literature references.
    
    Note: This function returns compound information which may include literature references.
    
    Args:
        cid: PubChem Compound ID
        client: Optional PubChemClient instance
        
    Returns:
        Dict with literature references
        
    Example:
        >>> refs = get_literature_references(2244)
        >>> print(refs)
    """
    if client is None:
        client = PubChemClient()
    
    try:
        # Get full compound record which includes references
        return client.get_compound_info(cid)
    except Exception as e:
        raise Exception(f"Error getting literature references: {str(e)}")

