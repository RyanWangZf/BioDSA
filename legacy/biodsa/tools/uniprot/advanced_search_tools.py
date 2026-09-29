"""
UniProt Advanced Search Tools

Functions for batch processing and complex queries.
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from .client import UniProtClient


def batch_protein_lookup(
    accessions: List[str],
    format: str = 'json',
    client: Optional[UniProtClient] = None
) -> List[Dict[str, Any]]:
    """
    Process multiple accessions efficiently.
    
    Args:
        accessions: List of UniProt accession numbers (1-100)
        format: Output format (json, tsv, fasta)
        client: Optional UniProtClient instance
        
    Returns:
        List of results for each accession
        
    Example:
        >>> results = batch_protein_lookup(["P04637", "P53039", "Q16637"])
        >>> for r in results:
        >>>     if r['success']:
        >>>         print(f"{r['accession']}: Success")
    """
    if client is None:
        client = UniProtClient()
    
    if len(accessions) < 1 or len(accessions) > 100:
        raise ValueError("Please provide between 1 and 100 accessions")
    
    try:
        return client.batch_protein_lookup(accessions, format=format)
    
    except Exception as e:
        raise Exception(f"Error in batch lookup: {str(e)}")


def advanced_search(
    query: Optional[str] = None,
    organism: Optional[str] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    min_mass: Optional[int] = None,
    max_mass: Optional[int] = None,
    keywords: Optional[List[str]] = None,
    size: int = 25,
    client: Optional[UniProtClient] = None
) -> pd.DataFrame:
    """
    Complex queries with multiple filters (length, mass, organism, function).
    
    Args:
        query: Base search query
        organism: Organism name or taxonomy ID
        min_length: Minimum sequence length
        max_length: Maximum sequence length
        min_mass: Minimum molecular mass (Da)
        max_mass: Maximum molecular mass (Da)
        keywords: List of keywords to include
        size: Number of results to return (1-500, default: 25)
        client: Optional UniProtClient instance
        
    Returns:
        DataFrame with search results
        
    Example:
        >>> df = advanced_search(
        >>>     query="kinase",
        >>>     organism="human",
        >>>     min_length=300,
        >>>     max_length=500
        >>> )
        >>> print(df[['primaryAccession', 'proteinName', 'sequenceLength']])
    """
    if client is None:
        client = UniProtClient()
    
    try:
        data = client.advanced_search(
            query=query,
            organism=organism,
            min_length=min_length,
            max_length=max_length,
            min_mass=min_mass,
            max_mass=max_mass,
            keywords=keywords,
            size=size
        )
        
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
                'sequenceLength': entry.get('sequence', {}).get('length', 0),
                'molecularWeight': entry.get('sequence', {}).get('molWeight', 0)
            })
        
        return pd.DataFrame(results)
    
    except Exception as e:
        raise Exception(f"Error in advanced search: {str(e)}")


def search_by_taxonomy(
    taxonomy_id: Optional[int] = None,
    taxonomy_name: Optional[str] = None,
    size: int = 25,
    client: Optional[UniProtClient] = None
) -> pd.DataFrame:
    """
    Search by detailed taxonomic classification.
    
    Args:
        taxonomy_id: NCBI taxonomy ID
        taxonomy_name: Taxonomic name (e.g., Mammalia, Bacteria)
        size: Number of results to return (1-500, default: 25)
        client: Optional UniProtClient instance
        
    Returns:
        DataFrame with search results
        
    Example:
        >>> df = search_by_taxonomy(taxonomy_id=9606, size=10)
        >>> print(df[['primaryAccession', 'proteinName', 'organism']])
    """
    if client is None:
        client = UniProtClient()
    
    if not taxonomy_id and not taxonomy_name:
        raise ValueError("Please provide at least one of: taxonomy_id or taxonomy_name")
    
    try:
        data = client.search_by_taxonomy(
            taxonomy_id=taxonomy_id,
            taxonomy_name=taxonomy_name,
            size=size
        )
        
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
                'sequenceLength': entry.get('sequence', {}).get('length', 0)
            })
        
        return pd.DataFrame(results)
    
    except Exception as e:
        raise Exception(f"Error searching by taxonomy: {str(e)}")

