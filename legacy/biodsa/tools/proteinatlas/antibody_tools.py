"""
Human Protein Atlas Antibody Tools

Functions for antibody validation and information.
"""

from typing import Dict, Any, Optional
from .client import ProteinAtlasClient


def get_antibody_info(
    gene: str,
    client: Optional[ProteinAtlasClient] = None
) -> Dict[str, Any]:
    """
    Get antibody validation and staining information for a protein.
    
    Args:
        gene: Gene symbol
        client: Optional ProteinAtlasClient instance
        
    Returns:
        Dict with antibody information
        
    Example:
        >>> ab_info = get_antibody_info("TP53")
        >>> print(f"Antibody: {ab_info.get('Antibody')}")
        >>> print(f"Reliability: {ab_info.get('Antibody reliability rating')}")
    """
    if client is None:
        client = ProteinAtlasClient()
    
    try:
        return client.get_antibody_info(gene)
    except Exception as e:
        raise Exception(f"Error getting antibody info: {str(e)}")

