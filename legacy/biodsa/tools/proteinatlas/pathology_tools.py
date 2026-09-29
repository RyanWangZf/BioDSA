"""
Human Protein Atlas Pathology Tools

Functions for cancer and pathology data analysis.
"""

import pandas as pd
from typing import Dict, Any, Optional
from .client import ProteinAtlasClient


def get_pathology_data(
    gene: str,
    client: Optional[ProteinAtlasClient] = None
) -> Dict[str, Any]:
    """
    Get cancer and pathology data for a protein.
    
    Args:
        gene: Gene symbol
        client: Optional ProteinAtlasClient instance
        
    Returns:
        Dict with pathology data
        
    Example:
        >>> pathology = get_pathology_data("TP53")
        >>> print(f"Breast cancer prognosis: {pathology.get('prognostic_Breast_Invasive_Carcinoma_(TCGA)')}")
    """
    if client is None:
        client = ProteinAtlasClient()
    
    try:
        return client.get_pathology_data(gene)
    except Exception as e:
        raise Exception(f"Error getting pathology data: {str(e)}")


def search_cancer_markers(
    cancer: Optional[str] = None,
    prognostic: Optional[str] = None,
    max_results: Optional[int] = 100,
    client: Optional[ProteinAtlasClient] = None
) -> pd.DataFrame:
    """
    Find proteins associated with specific cancers or with prognostic value.
    
    Args:
        cancer: Cancer type (e.g., breast cancer, lung cancer)
        prognostic: Prognostic filter (favorable, unfavorable)
        max_results: Maximum number of results
        client: Optional ProteinAtlasClient instance
        
    Returns:
        DataFrame with cancer-associated proteins
        
    Example:
        >>> df = search_cancer_markers(prognostic="unfavorable")
        >>> print(df[['Gene', 'Gene description']])
    """
    if client is None:
        client = ProteinAtlasClient()
    
    try:
        search_query = ''
        if cancer:
            search_query = f'cancer:"{cancer}"'
        
        if prognostic:
            search_query += ('' if not search_query else ' AND ') + f'prognostic:"{prognostic}"'
        
        if not search_query:
            search_query = 'prognostic:*'  # Search for any prognostic markers
        
        results = client.search_proteins(search_query, max_results=max_results)
        return pd.DataFrame(results)
    except Exception as e:
        raise Exception(f"Error searching cancer markers: {str(e)}")

