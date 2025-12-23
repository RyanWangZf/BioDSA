"""
PubChem Safety and Toxicity Tools

Functions for retrieving safety classifications and toxicity information.
"""

from typing import Dict, Any, Optional, Union
from .client import PubChemClient


def get_safety_data(
    cid: Union[int, str],
    client: Optional[PubChemClient] = None
) -> Dict[str, Any]:
    """
    Get GHS hazard classifications and safety information.
    
    Args:
        cid: PubChem Compound ID
        client: Optional PubChemClient instance
        
    Returns:
        Dict with safety data
        
    Example:
        >>> safety = get_safety_data(2244)
        >>> print(safety)
    """
    if client is None:
        client = PubChemClient()
    
    try:
        return client.get_safety_data(cid)
    except Exception as e:
        raise Exception(f"Error getting safety data: {str(e)}")


def get_toxicity_info(
    cid: Union[int, str],
    client: Optional[PubChemClient] = None
) -> Dict[str, Any]:
    """
    Get toxicity data including LD50, carcinogenicity, and mutagenicity.
    
    Note: This function returns classification data which may include toxicity information.
    
    Args:
        cid: PubChem Compound ID
        client: Optional[PubChemClient instance
        
    Returns:
        Dict with toxicity information
        
    Example:
        >>> toxicity = get_toxicity_info(2244)
        >>> print(toxicity)
    """
    if client is None:
        client = PubChemClient()
    
    try:
        return client.get_safety_data(cid)
    except Exception as e:
        raise Exception(f"Error getting toxicity info: {str(e)}")

