"""
UniProt Protein Tools

High-level functions for protein search and information retrieval.
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from .client import UniProtClient


def search_proteins(
    query: str,
    organism: Optional[str] = None,
    size: int = 25,
    client: Optional[UniProtClient] = None
) -> pd.DataFrame:
    """
    Search UniProt database for proteins.
    
    Args:
        query: Search query (protein name, keyword, or complex search)
        organism: Organism name or taxonomy ID to filter results
        size: Number of results to return (1-500, default: 25)
        client: Optional UniProtClient instance
        
    Returns:
        DataFrame with search results
        
    Example:
        >>> df = search_proteins("kinase", organism="human", size=10)
        >>> print(df[['primaryAccession', 'proteinName', 'organism']])
    """
    if client is None:
        client = UniProtClient()
    
    try:
        data = client.search_proteins(query, organism=organism, size=size, format='json')
        
        if not data or 'results' not in data:
            return pd.DataFrame()
        
        results = []
        for entry in data['results']:
            # Extract protein name
            protein_name = ''
            if 'proteinDescription' in entry:
                desc = entry['proteinDescription']
                if 'recommendedName' in desc and 'fullName' in desc['recommendedName']:
                    protein_name = desc['recommendedName']['fullName'].get('value', '')
                elif 'submissionNames' in desc and len(desc['submissionNames']) > 0:
                    protein_name = desc['submissionNames'][0]['fullName'].get('value', '')
            
            # Extract gene name
            gene_name = ''
            if 'genes' in entry and len(entry['genes']) > 0:
                gene_name = entry['genes'][0].get('geneName', {}).get('value', '')
            
            results.append({
                'primaryAccession': entry.get('primaryAccession', ''),
                'uniProtkbId': entry.get('uniProtkbId', ''),
                'proteinName': protein_name,
                'geneName': gene_name,
                'organism': entry.get('organism', {}).get('scientificName', ''),
                'taxonId': entry.get('organism', {}).get('taxonId', ''),
                'entryType': entry.get('entryType', ''),
                'sequenceLength': entry.get('sequence', {}).get('length', 0),
                'molecularWeight': entry.get('sequence', {}).get('molWeight', 0)
            })
        
        return pd.DataFrame(results)
    
    except Exception as e:
        raise Exception(f"Error searching proteins: {str(e)}")


def get_protein_info(
    accession: str,
    client: Optional[UniProtClient] = None
) -> Dict[str, Any]:
    """
    Get detailed information for a specific protein.
    
    Args:
        accession: UniProt accession number (e.g., P04637)
        client: Optional UniProtClient instance
        
    Returns:
        Dict with detailed protein information
        
    Example:
        >>> info = get_protein_info("P04637")
        >>> print(info['proteinName'])
    """
    if client is None:
        client = UniProtClient()
    
    try:
        data = client.get_protein_info(accession, format='json')
        return data
    
    except Exception as e:
        raise Exception(f"Error getting protein info: {str(e)}")


def search_by_gene(
    gene: str,
    organism: Optional[str] = None,
    size: int = 25,
    client: Optional[UniProtClient] = None
) -> pd.DataFrame:
    """
    Search for proteins by gene name or symbol.
    
    Args:
        gene: Gene name or symbol (e.g., BRCA1, INS)
        organism: Organism name or taxonomy ID to filter results
        size: Number of results to return (1-500, default: 25)
        client: Optional UniProtClient instance
        
    Returns:
        DataFrame with search results
        
    Example:
        >>> df = search_by_gene("TP53", organism="human")
        >>> print(df[['primaryAccession', 'proteinName', 'geneName']])
    """
    if client is None:
        client = UniProtClient()
    
    try:
        data = client.search_by_gene(gene, organism=organism, size=size)
        
        if not data or 'results' not in data:
            return pd.DataFrame()
        
        results = []
        for entry in data['results']:
            # Extract protein name
            protein_name = ''
            if 'proteinDescription' in entry:
                desc = entry['proteinDescription']
                if 'recommendedName' in desc and 'fullName' in desc['recommendedName']:
                    protein_name = desc['recommendedName']['fullName'].get('value', '')
                elif 'submissionNames' in desc and len(desc['submissionNames']) > 0:
                    protein_name = desc['submissionNames'][0]['fullName'].get('value', '')
            
            # Extract gene name
            gene_name = ''
            if 'genes' in entry and len(entry['genes']) > 0:
                gene_name = entry['genes'][0].get('geneName', {}).get('value', '')
            
            results.append({
                'primaryAccession': entry.get('primaryAccession', ''),
                'uniProtkbId': entry.get('uniProtkbId', ''),
                'proteinName': protein_name,
                'geneName': gene_name,
                'organism': entry.get('organism', {}).get('scientificName', ''),
                'taxonId': entry.get('organism', {}).get('taxonId', ''),
                'entryType': entry.get('entryType', '')
            })
        
        return pd.DataFrame(results)
    
    except Exception as e:
        raise Exception(f"Error searching by gene: {str(e)}")


def get_protein_features(
    accession: str,
    client: Optional[UniProtClient] = None
) -> Dict[str, Any]:
    """
    Get functional features and domains for a protein.
    
    Args:
        accession: UniProt accession number
        client: Optional UniProtClient instance
        
    Returns:
        Dict with protein features
        
    Example:
        >>> features = get_protein_features("P04637")
        >>> print(f"Domains: {len(features['domains'])}")
    """
    if client is None:
        client = UniProtClient()
    
    try:
        protein = client.get_protein_info(accession, format='json')
        
        features = {
            'accession': protein.get('primaryAccession', ''),
            'name': protein.get('uniProtkbId', ''),
            'features': protein.get('features', []),
            'comments': protein.get('comments', []),
            'keywords': protein.get('keywords', []),
            'domains': [f for f in protein.get('features', []) if f.get('type') == 'Domain'],
            'activeSites': [f for f in protein.get('features', []) if f.get('type') == 'Active site'],
            'bindingSites': [f for f in protein.get('features', []) if f.get('type') == 'Binding site']
        }
        
        return features
    
    except Exception as e:
        raise Exception(f"Error getting protein features: {str(e)}")


def validate_accession(
    accession: str,
    client: Optional[UniProtClient] = None
) -> Dict[str, Any]:
    """
    Check if an accession number is valid.
    
    Args:
        accession: UniProt accession number to validate
        client: Optional UniProtClient instance
        
    Returns:
        Validation result
        
    Example:
        >>> result = validate_accession("P04637")
        >>> print(f"Valid: {result['isValid']}")
    """
    if client is None:
        client = UniProtClient()
    
    try:
        return client.validate_accession(accession)
    
    except Exception as e:
        raise Exception(f"Error validating accession: {str(e)}")

