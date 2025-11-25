"""
Ensembl Comparative Tools

Functions for comparative genomics and evolutionary analysis.
"""

from typing import Dict, Any, Optional
from .client import EnsemblClient


def get_homologs(
    gene_id: str,
    species: Optional[str] = None,
    target_species: Optional[str] = None,
    client: Optional[EnsemblClient] = None
) -> Dict[str, Any]:
    """
    Find orthologous and paralogous genes across species.
    
    Args:
        gene_id: Ensembl gene ID
        species: Source species name (default: homo_sapiens)
        target_species: Target species to search (default: mus_musculus)
        client: Optional EnsemblClient instance
        
    Returns:
        Dict with homolog information
        
    Example:
        >>> homologs = get_homologs("ENSG00000139618", target_species="mus_musculus")
        >>> print(f"Source: {homologs['source_gene']['symbol']}")
        >>> if 'ortholog' in homologs:
        >>>     print(f"Ortholog: {homologs['ortholog']['symbol']}")
    """
    if client is None:
        client = EnsemblClient()
    
    try:
        return client.get_homologs(
            gene_id,
            species=species,
            target_species=target_species
        )
    except Exception as e:
        raise Exception(f"Error getting homologs: {str(e)}")


def get_gene_tree(
    gene_id: str,
    clusterset_id: Optional[str] = None,
    client: Optional[EnsemblClient] = None
) -> Dict[str, Any]:
    """
    Get phylogenetic tree for gene family.
    
    Args:
        gene_id: Ensembl gene ID
        clusterset_id: Specific clusterset ID
        client: Optional EnsemblClient instance
        
    Returns:
        Dict with gene tree data
        
    Example:
        >>> tree = get_gene_tree("ENSG00000139618")
        >>> print(f"Tree ID: {tree.get('id')}")
    """
    if client is None:
        client = EnsemblClient()
    
    try:
        return client.get_gene_tree(gene_id, clusterset_id=clusterset_id)
    except Exception as e:
        raise Exception(f"Error getting gene tree: {str(e)}")


def compare_genes_across_species(
    gene_symbol: str,
    species_list: list,
    client: Optional[EnsemblClient] = None
) -> Dict[str, Any]:
    """
    Compare a gene across multiple species.
    
    Args:
        gene_symbol: Gene symbol to search
        species_list: List of species to compare
        client: Optional EnsemblClient instance
        
    Returns:
        Dict with comparative gene data
        
    Example:
        >>> comparison = compare_genes_across_species(
        >>>     "TP53",
        >>>     ["homo_sapiens", "mus_musculus", "rattus_norvegicus"]
        >>> )
    """
    if client is None:
        client = EnsemblClient()
    
    results = {}
    for species in species_list:
        try:
            gene = client.lookup_gene(gene_symbol, species=species)
            results[species] = {
                'id': gene.get('id'),
                'display_name': gene.get('display_name'),
                'description': gene.get('description'),
                'biotype': gene.get('biotype'),
                'location': f"{gene.get('seq_region_name')}:{gene.get('start')}-{gene.get('end')}",
                'strand': gene.get('strand'),
                'assembly_name': gene.get('assembly_name'),
                'found': True
            }
        except Exception as e:
            results[species] = {
                'found': False,
                'error': str(e)
            }
    
    return results

