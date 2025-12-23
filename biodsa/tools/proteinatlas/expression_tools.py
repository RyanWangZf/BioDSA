"""
Human Protein Atlas Expression Tools

Functions for tissue, blood, and brain expression analysis.
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from .client import ProteinAtlasClient


def get_tissue_expression(
    gene: str,
    client: Optional[ProteinAtlasClient] = None
) -> Dict[str, Any]:
    """
    Get tissue-specific expression data for a protein.
    
    Args:
        gene: Gene symbol
        client: Optional ProteinAtlasClient instance
        
    Returns:
        Dict with tissue expression data
        
    Example:
        >>> expr = get_tissue_expression("TP53")
        >>> print(f"Liver expression: {expr.get('t_RNA_liver')}")
    """
    if client is None:
        client = ProteinAtlasClient()
    
    try:
        return client.get_tissue_expression(gene)
    except Exception as e:
        raise Exception(f"Error getting tissue expression: {str(e)}")


def get_blood_expression(
    gene: str,
    client: Optional[ProteinAtlasClient] = None
) -> Dict[str, Any]:
    """
    Get blood cell expression data for a protein.
    
    Args:
        gene: Gene symbol
        client: Optional ProteinAtlasClient instance
        
    Returns:
        Dict with blood expression data
        
    Example:
        >>> expr = get_blood_expression("CD4")
        >>> print(f"NK-cell expression: {expr.get('blood_RNA_NK-cell')}")
    """
    if client is None:
        client = ProteinAtlasClient()
    
    try:
        return client.get_blood_expression(gene)
    except Exception as e:
        raise Exception(f"Error getting blood expression: {str(e)}")


def get_brain_expression(
    gene: str,
    client: Optional[ProteinAtlasClient] = None
) -> Dict[str, Any]:
    """
    Get brain region expression data for a protein.
    
    Args:
        gene: Gene symbol
        client: Optional ProteinAtlasClient instance
        
    Returns:
        Dict with brain expression data
        
    Example:
        >>> expr = get_brain_expression("APP")
        >>> print(f"Hippocampus expression: {expr.get('brain_RNA_hippocampal_formation')}")
    """
    if client is None:
        client = ProteinAtlasClient()
    
    try:
        return client.get_brain_expression(gene)
    except Exception as e:
        raise Exception(f"Error getting brain expression: {str(e)}")


def search_by_tissue(
    tissue: str,
    expression_level: Optional[str] = None,
    max_results: Optional[int] = 100,
    client: Optional[ProteinAtlasClient] = None
) -> pd.DataFrame:
    """
    Find proteins highly expressed in specific tissues.
    
    Args:
        tissue: Tissue name (e.g., liver, brain, heart)
        expression_level: Expression level filter (high, medium, low, not detected)
        max_results: Maximum number of results
        client: Optional ProteinAtlasClient instance
        
    Returns:
        DataFrame with proteins expressed in the tissue
        
    Example:
        >>> df = search_by_tissue("liver", expression_level="high")
        >>> print(df[['Gene', 'Gene description']])
    """
    if client is None:
        client = ProteinAtlasClient()
    
    try:
        search_query = f'tissue:"{tissue}"'
        if expression_level:
            search_query += f' AND expression:"{expression_level}"'
        
        results = client.search_proteins(search_query, max_results=max_results)
        return pd.DataFrame(results)
    except Exception as e:
        raise Exception(f"Error searching by tissue: {str(e)}")


def compare_expression_profiles(
    genes: List[str],
    expression_type: str = 'tissue',
    client: Optional[ProteinAtlasClient] = None
) -> List[Dict[str, Any]]:
    """
    Compare expression profiles between multiple proteins.
    
    Args:
        genes: List of gene symbols to compare (2-10)
        expression_type: Type of expression (tissue, brain, blood)
        client: Optional ProteinAtlasClient instance
        
    Returns:
        List of expression data for each gene
        
    Example:
        >>> comparison = compare_expression_profiles(["TP53", "BRCA1"])
        >>> for item in comparison:
        >>>     print(f"{item['gene']}: {item['expressionData']}")
    """
    if client is None:
        client = ProteinAtlasClient()
    
    if len(genes) < 2 or len(genes) > 10:
        raise ValueError("Please provide between 2 and 10 genes for comparison")
    
    try:
        comparisons = []
        for gene in genes:
            if expression_type == 'tissue':
                expr_data = client.get_tissue_expression(gene)
            elif expression_type == 'brain':
                expr_data = client.get_brain_expression(gene)
            elif expression_type == 'blood':
                expr_data = client.get_blood_expression(gene)
            else:
                expr_data = client.get_tissue_expression(gene)
            
            comparisons.append({
                'gene': gene,
                'expressionData': expr_data
            })
        
        return comparisons
    except Exception as e:
        raise Exception(f"Error comparing expression profiles: {str(e)}")

