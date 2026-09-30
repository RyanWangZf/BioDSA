"""
UniProt Comparative and Evolutionary Analysis Tools

Functions for comparing proteins and analyzing evolutionary relationships.
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from .client import UniProtClient


def compare_proteins(
    accessions: List[str],
    client: Optional[UniProtClient] = None
) -> pd.DataFrame:
    """
    Compare multiple proteins side-by-side with sequence and feature comparison.
    
    Args:
        accessions: List of UniProt accession numbers (2-10)
        client: Optional UniProtClient instance
        
    Returns:
        DataFrame with protein comparison
        
    Example:
        >>> df = compare_proteins(["P04637", "Q16637"])
        >>> print(df[['accession', 'name', 'organism', 'length']])
    """
    if client is None:
        client = UniProtClient()
    
    if len(accessions) < 2 or len(accessions) > 10:
        raise ValueError("Please provide between 2 and 10 accessions for comparison")
    
    try:
        comparisons = []
        
        for accession in accessions:
            protein = client.get_protein_info(accession, format='json')
            
            domains = [f for f in protein.get('features', []) if f.get('type') == 'Domain']
            
            comparisons.append({
                'accession': protein.get('primaryAccession', ''),
                'name': protein.get('uniProtkbId', ''),
                'organism': protein.get('organism', {}).get('scientificName', ''),
                'length': protein.get('sequence', {}).get('length', 0),
                'mass': protein.get('sequence', {}).get('molWeight', 0),
                'features': len(protein.get('features', [])),
                'domains': len(domains)
            })
        
        return pd.DataFrame(comparisons)
    
    except Exception as e:
        raise Exception(f"Error comparing proteins: {str(e)}")


def get_protein_homologs(
    accession: str,
    organism: Optional[str] = None,
    size: int = 25,
    client: Optional[UniProtClient] = None
) -> pd.DataFrame:
    """
    Find homologous proteins across different species.
    
    Args:
        accession: UniProt accession number
        organism: Target organism to find homologs in
        size: Number of results to return (1-100, default: 25)
        client: Optional UniProtClient instance
        
    Returns:
        DataFrame with homologous proteins
        
    Example:
        >>> df = get_protein_homologs("P04637", organism="mouse")
        >>> print(df[['primaryAccession', 'proteinName', 'organism']])
    """
    if client is None:
        client = UniProtClient()
    
    try:
        # Get the protein info first to build a homology search
        protein = client.get_protein_info(accession, format='json')
        
        # Build search query for homologs
        query = 'reviewed:true'
        
        # Use protein name if available
        if 'proteinDescription' in protein:
            desc = protein['proteinDescription']
            if 'recommendedName' in desc and 'fullName' in desc['recommendedName']:
                protein_name = desc['recommendedName']['fullName'].get('value', '')
                if protein_name:
                    query += f' AND ({protein_name})'
        
        if organism:
            query += f' AND organism_name:"{organism}"'
        
        query += f' NOT accession:"{accession}"'
        
        data = client.advanced_search(query=query.replace('reviewed:true AND ', ''), size=min(size, 100))
        
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
        raise Exception(f"Error finding homologs: {str(e)}")


def get_protein_orthologs(
    accession: str,
    organism: Optional[str] = None,
    size: int = 25,
    client: Optional[UniProtClient] = None
) -> pd.DataFrame:
    """
    Identify orthologous proteins for evolutionary studies.
    
    Args:
        accession: UniProt accession number
        organism: Target organism to find orthologs in
        size: Number of results to return (1-100, default: 25)
        client: Optional UniProtClient instance
        
    Returns:
        DataFrame with orthologous proteins
        
    Example:
        >>> df = get_protein_orthologs("P04637", organism="mouse")
        >>> print(df[['primaryAccession', 'geneName', 'organism']])
    """
    if client is None:
        client = UniProtClient()
    
    try:
        # Get the protein info first
        protein = client.get_protein_info(accession, format='json')
        
        # Build ortholog search (similar gene, different organism)
        query = 'reviewed:true'
        
        if 'genes' in protein and len(protein['genes']) > 0:
            gene_name = protein['genes'][0].get('geneName', {}).get('value', '')
            if gene_name:
                query += f' AND gene:"{gene_name}"'
        
        if organism:
            query += f' AND organism_name:"{organism}"'
        
        query += f' NOT accession:"{accession}"'
        
        data = client.advanced_search(query=query.replace('reviewed:true AND ', ''), size=min(size, 100))
        
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
        raise Exception(f"Error finding orthologs: {str(e)}")


def get_phylogenetic_info(
    accession: str,
    client: Optional[UniProtClient] = None
) -> Dict[str, Any]:
    """
    Retrieve evolutionary relationships and phylogenetic data.
    
    Args:
        accession: UniProt accession number
        client: Optional UniProtClient instance
        
    Returns:
        Dict with phylogenetic information
        
    Example:
        >>> info = get_phylogenetic_info("P04637")
        >>> print(info['taxonomicLineage'])
    """
    if client is None:
        client = UniProtClient()
    
    try:
        protein = client.get_protein_info(accession, format='json')
        
        phylogenetic_info = {
            'accession': protein.get('primaryAccession', ''),
            'organism': protein.get('organism', {}),
            'taxonomicLineage': protein.get('organism', {}).get('lineage', []),
            'evolutionaryOrigin': [c for c in protein.get('comments', []) 
                                   if c.get('commentType') == 'EVOLUTIONARY ORIGIN'],
            'phylogeneticRange': [c for c in protein.get('comments', []) 
                                  if c.get('commentType') == 'PHYLOGENETIC RANGE']
        }
        
        return phylogenetic_info
    
    except Exception as e:
        raise Exception(f"Error fetching phylogenetic info: {str(e)}")


def get_taxonomy_info(
    accession: str,
    client: Optional[UniProtClient] = None
) -> Dict[str, Any]:
    """
    Get detailed taxonomic information for a protein's organism.
    
    Args:
        accession: UniProt accession number
        client: Optional UniProtClient instance
        
    Returns:
        Dict with taxonomy information
        
    Example:
        >>> info = get_taxonomy_info("P04637")
        >>> print(f"Organism: {info['scientificName']}")
    """
    if client is None:
        client = UniProtClient()
    
    try:
        protein = client.get_protein_info(accession, format='json')
        organism = protein.get('organism', {})
        
        taxonomy_info = {
            'accession': protein.get('primaryAccession', ''),
            'organism': organism,
            'taxonomyId': organism.get('taxonId'),
            'scientificName': organism.get('scientificName'),
            'commonName': organism.get('commonName'),
            'lineage': organism.get('lineage', []),
            'taxonomicDivision': organism.get('lineage', ['Unknown'])[0] if organism.get('lineage') else 'Unknown'
        }
        
        return taxonomy_info
    
    except Exception as e:
        raise Exception(f"Error fetching taxonomy info: {str(e)}")

