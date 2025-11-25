"""
NCBI Datasets API - Gene Operations

High-level functions for gene-related operations.
"""

from typing import Optional, Dict, Any
import pandas as pd
from biodsa.tools.ncbi.client import NCBIDatasetsClient


def search_genes(
    gene_symbol: Optional[str] = None,
    gene_id: Optional[int] = None,
    organism: Optional[str] = None,
    tax_id: Optional[int] = None,
    chromosome: Optional[str] = None,
    max_results: int = 50,
    page_token: Optional[str] = None,
    client: Optional[NCBIDatasetsClient] = None
) -> pd.DataFrame:
    """
    Search genes by symbol and taxonomy ID.
    Note: NCBI Datasets API v2alpha requires gene_symbol and tax_id.
    
    Args:
        gene_symbol: Gene symbol (e.g., BRCA1, TP53) - required
        gene_id: NCBI Gene ID (not used in search, use get_gene_info instead)
        organism: Organism name (not used in v2alpha, use tax_id)
        tax_id: NCBI taxonomy ID - required (defaults to human if not provided)
        chromosome: Chromosome name (not used in v2alpha)
        max_results: Maximum number of results (not used in v2alpha)
        page_token: Pagination token (not used in v2alpha)
        client: Optional NCBIDatasetsClient instance
        
    Returns:
        DataFrame with gene search results
        
    Example:
        >>> genes = search_genes(gene_symbol='TP53', tax_id=9606)
        >>> print(genes[['gene_id', 'symbol', 'description']].head())
    """
    if client is None:
        client = NCBIDatasetsClient()
    
    try:
        response = client.search_genes(
            gene_symbol=gene_symbol,
            gene_id=gene_id,
            organism=organism,
            tax_id=tax_id,
            chromosome=chromosome,
            max_results=max_results,
            page_token=page_token
        )
        
        # Extract gene info from reports
        reports = response.get('reports', [])
        
        if not reports:
            return pd.DataFrame()
        
        # Extract key information
        records = []
        for report in reports:
            gene = report.get('gene', {})
            
            # Get first genomic annotation if available
            annotations = gene.get('annotations', [])
            location_info = {}
            if annotations:
                annotation = annotations[0]
                genomic_locations = annotation.get('genomic_locations', [])
                if genomic_locations:
                    loc = genomic_locations[0]
                    genomic_range = loc.get('genomic_range', {})
                    location_info = {
                        'chromosome': loc.get('sequence_name', ''),
                        'assembly_name': annotation.get('assembly_name', ''),
                        'start': genomic_range.get('begin', 0),
                        'end': genomic_range.get('end', 0),
                        'strand': genomic_range.get('orientation', ''),
                    }
            
            record = {
                'gene_id': gene.get('gene_id', ''),
                'symbol': gene.get('symbol', ''),
                'description': gene.get('description', ''),
                'gene_type': gene.get('type', ''),
                'organism_name': gene.get('taxname', ''),
                'tax_id': gene.get('tax_id', ''),
                **location_info,
                'synonyms': ', '.join(gene.get('synonyms', [])),
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error searching genes: {str(e)}")


def get_gene_info(
    gene_id: int,
    include_sequences: bool = False,
    client: Optional[NCBIDatasetsClient] = None
) -> Dict[str, Any]:
    """
    Get detailed information for a specific gene.
    
    Args:
        gene_id: NCBI Gene ID
        include_sequences: Include gene sequences
        client: Optional NCBIDatasetsClient instance
        
    Returns:
        Dictionary with detailed gene information
        
    Example:
        >>> info = get_gene_info(7157)  # TP53
        >>> gene = info['reports'][0]['gene']
        >>> print(f"Gene: {gene['symbol']} - {gene['description']}")
    """
    if client is None:
        client = NCBIDatasetsClient()
    
    try:
        response = client.get_gene_info(
            gene_id=gene_id,
            include_sequences=include_sequences
        )
        
        # Return the full response which contains reports
        return response
        
    except Exception as e:
        raise Exception(f"Error getting gene info: {str(e)}")


def get_gene_sequences(
    gene_id: int,
    sequence_type: Optional[str] = None,
    client: Optional[NCBIDatasetsClient] = None
) -> Dict[str, Any]:
    """
    Retrieve sequences for a specific gene.
    
    Args:
        gene_id: NCBI Gene ID
        sequence_type: Type of sequence (genomic, transcript, protein, all)
        client: Optional NCBIDatasetsClient instance
        
    Returns:
        Dictionary with gene sequences
        
    Example:
        >>> sequences = get_gene_sequences(7157, sequence_type='protein')
        >>> print(sequences)
    """
    if client is None:
        client = NCBIDatasetsClient()
    
    try:
        return client.get_gene_sequences(
            gene_id=gene_id,
            sequence_type=sequence_type
        )
    except Exception as e:
        raise Exception(f"Error getting gene sequences: {str(e)}")

