"""
Ensembl Annotation Tools

Functions for cross-references, assembly information, and species data.
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from .client import EnsemblClient


def get_xrefs(
    gene_id: str,
    species: Optional[str] = None,
    external_db: Optional[str] = None,
    all_levels: bool = False,
    client: Optional[EnsemblClient] = None
) -> pd.DataFrame:
    """
    Get external database cross-references for genes.
    
    Args:
        gene_id: Ensembl gene ID
        species: Species name (default: homo_sapiens)
        external_db: Specific external database (optional)
        all_levels: Include transcript and translation xrefs
        client: Optional EnsemblClient instance
        
    Returns:
        DataFrame with cross-references
        
    Example:
        >>> xrefs = get_xrefs("ENSG00000139618")
        >>> print(xrefs[['dbname', 'display_id', 'primary_id']])
    """
    if client is None:
        client = EnsemblClient()
    
    try:
        data = client.get_xrefs(
            gene_id,
            species=species,
            external_db=external_db,
            all_levels=all_levels
        )
        
        if not data:
            return pd.DataFrame()
        
        results = []
        for xref in data:
            results.append({
                'primary_id': xref.get('primary_id', ''),
                'display_id': xref.get('display_id', ''),
                'dbname': xref.get('dbname', ''),
                'info_type': xref.get('info_type', ''),
                'description': xref.get('description', ''),
                'version': xref.get('version', '')
            })
        
        return pd.DataFrame(results)
    
    except Exception as e:
        raise Exception(f"Error getting cross-references: {str(e)}")


def list_species(
    division: Optional[str] = None,
    client: Optional[EnsemblClient] = None
) -> pd.DataFrame:
    """
    Get list of available species and assemblies.
    
    Args:
        division: Ensembl division (e.g., vertebrates, plants, fungi)
        client: Optional EnsemblClient instance
        
    Returns:
        DataFrame with species information
        
    Example:
        >>> species = list_species(division="vertebrates")
        >>> print(species[['name', 'display_name', 'assembly']])
    """
    if client is None:
        client = EnsemblClient()
    
    try:
        data = client.list_species(division=division)
        
        if not data or 'species' not in data:
            return pd.DataFrame()
        
        results = []
        for sp in data['species']:
            results.append({
                'name': sp.get('name', ''),
                'display_name': sp.get('display_name', ''),
                'taxonomy_id': sp.get('taxon_id', ''),
                'assembly': sp.get('assembly', ''),
                'division': sp.get('division', ''),
                'strain': sp.get('strain', '')
            })
        
        return pd.DataFrame(results)
    
    except Exception as e:
        raise Exception(f"Error listing species: {str(e)}")


def get_assembly_info(
    species: Optional[str] = None,
    bands: bool = False,
    client: Optional[EnsemblClient] = None
) -> Dict[str, Any]:
    """
    Get genome assembly information and statistics.
    
    Args:
        species: Species name (default: homo_sapiens)
        bands: Include chromosome banding patterns
        client: Optional EnsemblClient instance
        
    Returns:
        Dict with assembly information
        
    Example:
        >>> assembly = get_assembly_info("homo_sapiens")
        >>> print(f"Assembly: {assembly['assembly_name']}")
        >>> print(f"Genome length: {assembly['total_genome_length']}")
    """
    if client is None:
        client = EnsemblClient()
    
    try:
        return client.get_assembly_info(species=species, bands=bands)
    except Exception as e:
        raise Exception(f"Error getting assembly info: {str(e)}")


def get_karyotype(
    species: Optional[str] = None,
    client: Optional[EnsemblClient] = None
) -> Dict[str, Any]:
    """
    Get chromosome information and karyotype.
    
    Args:
        species: Species name (default: homo_sapiens)
        client: Optional EnsemblClient instance
        
    Returns:
        Dict with karyotype information
        
    Example:
        >>> karyotype = get_karyotype("homo_sapiens")
        >>> print(f"Chromosomes: {karyotype['karyotype']}")
    """
    if client is None:
        client = EnsemblClient()
    
    try:
        assembly = client.get_assembly_info(species=species, bands=True)
        
        return {
            'species': client.get_default_species(species),
            'assembly_name': assembly.get('assembly_name', ''),
            'karyotype': assembly.get('karyotype', []),
            'chromosomes': assembly.get('top_level_region', [])
        }
    
    except Exception as e:
        raise Exception(f"Error getting karyotype: {str(e)}")

