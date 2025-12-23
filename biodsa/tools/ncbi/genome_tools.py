"""
NCBI Datasets API - Genome Operations

High-level functions for genome-related operations.
"""

from typing import Optional, Dict, Any
import pandas as pd
from biodsa.tools.ncbi.client import NCBIDatasetsClient


def search_genomes(
    tax_id: int,
    assembly_level: Optional[str] = None,
    assembly_source: Optional[str] = None,
    max_results: int = 50,
    page_token: Optional[str] = None,
    client: Optional[NCBIDatasetsClient] = None
) -> pd.DataFrame:
    """
    Search genome assemblies by taxonomy ID.
    
    Args:
        tax_id: NCBI taxonomy ID
        assembly_level: Filter by assembly level (complete, chromosome, scaffold, contig)
        assembly_source: Filter by source (refseq, genbank, all)
        max_results: Maximum number of results (1-1000)
        page_token: Pagination token
        client: Optional NCBIDatasetsClient instance
        
    Returns:
        DataFrame with genome search results
        
    Example:
        >>> genomes = search_genomes(tax_id=9606, assembly_level='complete')
        >>> print(genomes[['accession', 'organism_name', 'assembly_name']].head())
    """
    if client is None:
        client = NCBIDatasetsClient()
    
    try:
        response = client.search_genomes(
            tax_id=tax_id,
            assembly_level=assembly_level,
            assembly_source=assembly_source,
            max_results=max_results,
            page_token=page_token
        )
        
        reports = response.get('reports', [])
        
        if not reports:
            return pd.DataFrame()
        
        # Extract key information
        records = []
        for report in reports:
            accession = report.get('accession', '')
            organism = report.get('organism', {})
            assembly_info = report.get('assembly_info', {})
            assembly_stats = report.get('assembly_stats', {})
            
            record = {
                'accession': accession,
                'organism_name': organism.get('organism_name', ''),
                'tax_id': organism.get('tax_id', ''),
                'common_name': organism.get('common_name', ''),
                'assembly_name': assembly_info.get('assembly_name', ''),
                'assembly_level': assembly_info.get('assembly_level', ''),
                'assembly_type': assembly_info.get('assembly_type', ''),
                'submission_date': assembly_info.get('submission_date', ''),
                'submitter': assembly_info.get('submitter', ''),
                'total_sequence_length': assembly_stats.get('total_sequence_length', 0),
                'number_of_contigs': assembly_stats.get('number_of_contigs', 0),
                'number_of_scaffolds': assembly_stats.get('number_of_scaffolds', 0),
                'scaffold_n50': assembly_stats.get('scaffold_n50', 0),
                'contig_n50': assembly_stats.get('contig_n50', 0),
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error searching genomes: {str(e)}")


def get_genome_info(
    accession: str,
    include_annotation: bool = True,
    client: Optional[NCBIDatasetsClient] = None
) -> Dict[str, Any]:
    """
    Get detailed information for a specific genome assembly.
    
    Args:
        accession: Genome assembly accession (e.g., GCF_000001405.40)
        include_annotation: Include annotation information
        client: Optional NCBIDatasetsClient instance
        
    Returns:
        Dictionary with detailed genome information
        
    Example:
        >>> info = get_genome_info('GCF_000001405.40')
        >>> print(f"Assembly: {info['assembly_info']['assembly_name']}")
    """
    if client is None:
        client = NCBIDatasetsClient()
    
    try:
        return client.get_genome_info(
            accession=accession,
            include_annotation=include_annotation
        )
    except Exception as e:
        raise Exception(f"Error getting genome info: {str(e)}")


def get_genome_summary(
    accession: str,
    client: Optional[NCBIDatasetsClient] = None
) -> Dict[str, Any]:
    """
    Get summary statistics for a genome assembly.
    
    Args:
        accession: Genome assembly accession (e.g., GCF_000001405.40)
        client: Optional NCBIDatasetsClient instance
        
    Returns:
        Dictionary with genome summary
        
    Example:
        >>> summary = get_genome_summary('GCF_000001405.40')
        >>> print(f"Total length: {summary['assembly_stats']['total_sequence_length']}")
    """
    if client is None:
        client = NCBIDatasetsClient()
    
    try:
        response = client.get_genome_info(accession=accession, include_annotation=False)
        
        # Extract summary information
        reports = response.get('reports', [])
        if reports:
            report = reports[0]
            return {
                'accession': accession,
                'organism': report.get('organism', {}),
                'assembly_info': report.get('assembly_info', {}),
                'assembly_stats': report.get('assembly_stats', {}),
            }
        
        return {}
        
    except Exception as e:
        raise Exception(f"Error getting genome summary: {str(e)}")


def download_genome_data(
    accession: str,
    include_annotation: bool = True,
    file_format: str = 'all',
    client: Optional[NCBIDatasetsClient] = None
) -> Dict[str, Any]:
    """
    Get download URLs and information for genome data files.
    
    Args:
        accession: Genome assembly accession
        include_annotation: Include annotation files
        file_format: File format filter (fasta, genbank, gff3, gtf, all)
        client: Optional NCBIDatasetsClient instance
        
    Returns:
        Dictionary with download information
        
    Example:
        >>> download_info = download_genome_data('GCF_000001405.40', file_format='fasta')
        >>> print(download_info)
    """
    if client is None:
        client = NCBIDatasetsClient()
    
    try:
        return client.download_genome_data(
            accession=accession,
            include_annotation=include_annotation,
            file_format=file_format
        )
    except Exception as e:
        raise Exception(f"Error getting download info: {str(e)}")

