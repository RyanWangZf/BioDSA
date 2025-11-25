"""
PubChem Bioassay and Activity Data Tools

Functions for retrieving bioassay information and activity data.
"""

from typing import Dict, Any, Optional, List, Union
from .client import PubChemClient


def get_assay_info(
    aid: int,
    client: Optional[PubChemClient] = None
) -> Dict[str, Any]:
    """
    Get detailed information for a specific bioassay by AID.
    
    Args:
        aid: PubChem Assay ID
        client: Optional PubChemClient instance
        
    Returns:
        Dict with assay information
        
    Example:
        >>> assay = get_assay_info(1234)
        >>> print(assay)
    """
    if client is None:
        client = PubChemClient()
    
    try:
        return client.get_assay_info(aid)
    except Exception as e:
        raise Exception(f"Error getting assay info: {str(e)}")


def get_compound_bioactivities(
    cid: Union[int, str],
    activity_outcome: str = 'all',
    client: Optional[PubChemClient] = None
) -> List[int]:
    """
    Get all bioassay results and activities for a compound.
    
    Args:
        cid: PubChem Compound ID
        activity_outcome: Filter by activity outcome (active, inactive, all)
        client: Optional PubChemClient instance
        
    Returns:
        List of assay IDs
        
    Example:
        >>> aids = get_compound_bioactivities(2244)
        >>> print(f"Found {len(aids)} bioassays")
    """
    if client is None:
        client = PubChemClient()
    
    try:
        return client.get_compound_bioactivities(cid, activity_outcome=activity_outcome)
    except Exception as e:
        raise Exception(f"Error getting bioactivities: {str(e)}")


def compare_activity_profiles(
    cids: List[int],
    client: Optional[PubChemClient] = None
) -> Dict[str, Any]:
    """
    Compare bioactivity profiles across multiple compounds.
    
    Args:
        cids: List of PubChem CIDs (2-50)
        client: Optional PubChemClient instance
        
    Returns:
        Dict with activity profile comparison
        
    Example:
        >>> comparison = compare_activity_profiles([2244, 3672, 5090])
        >>> print(comparison)
    """
    if client is None:
        client = PubChemClient()
    
    if len(cids) < 2 or len(cids) > 50:
        raise ValueError("Please provide between 2 and 50 compound IDs")
    
    try:
        profiles = []
        for cid in cids:
            try:
                aids = client.get_compound_bioactivities(cid)
                profiles.append({
                    'cid': cid,
                    'assay_count': len(aids),
                    'assay_ids': aids[:20]  # Limit to first 20
                })
            except Exception as e:
                profiles.append({
                    'cid': cid,
                    'error': str(e)
                })
        
        return {
            'compound_count': len(cids),
            'profiles': profiles
        }
    except Exception as e:
        raise Exception(f"Error comparing activity profiles: {str(e)}")

