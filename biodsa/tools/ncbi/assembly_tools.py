"""
NCBI Datasets API - Assembly Operations

High-level functions for assembly-related operations.
"""

from typing import Optional, Dict, Any, List
import pandas as pd
from biodsa.tools.ncbi.client import NCBIDatasetsClient


def search_assemblies(
    query: Optional[str] = None,
    assembly_level: Optional[str] = None,
    assembly_source: Optional[str] = None,
    tax_id: Optional[int] = None,
    exclude_atypical: bool = False,
    max_results: int = 50,
    page_token: Optional[str] = None,
    client: Optional[NCBIDatasetsClient] = None
) -> pd.DataFrame:
    """
    Search genome assemblies with detailed filtering options.
    
    Args:
        query: Search query (organism name, assembly name, or keywords)
        assembly_level: Assembly level filter (complete, chromosome, scaffold, contig)
        assembly_source: Assembly source filter (refseq, genbank, all)
        tax_id: NCBI taxonomy ID to filter results
        exclude_atypical: Exclude atypical assemblies
        max_results: Maximum number of results (1-1000)
        page_token: Pagination token
        client: Optional NCBIDatasetsClient instance
        
    Returns:
        DataFrame with assembly search results
        
    Example:
        >>> assemblies = search_assemblies(tax_id=9606, assembly_level='complete')
        >>> print(assemblies[['assembly_accession', 'assembly_name', 'organism_name']].head())
    """
    if client is None:
        client = NCBIDatasetsClient()
    
    try:
        response = client.search_assemblies(
            query=query,
            assembly_level=assembly_level,
            assembly_source=assembly_source,
            tax_id=tax_id,
            exclude_atypical=exclude_atypical,
            max_results=max_results,
            page_token=page_token
        )
        
        assemblies = response.get('assemblies', [])
        
        if not assemblies:
            return pd.DataFrame()
        
        # Extract key information
        records = []
        for assembly in assemblies:
            assembly_info = assembly.get('assembly', {})
            assembly_accession = assembly_info.get('assembly_accession', '')
            
            organism = assembly.get('organism', {})
            assembly_stats = assembly_info.get('assembly_stats', {})
            
            record = {
                'assembly_accession': assembly_accession,
                'assembly_name': assembly_info.get('assembly_name', ''),
                'organism_name': organism.get('organism_name', ''),
                'tax_id': organism.get('tax_id', ''),
                'common_name': organism.get('common_name', ''),
                'assembly_level': assembly_info.get('assembly_level', ''),
                'assembly_type': assembly_info.get('assembly_type', ''),
                'submission_date': assembly_info.get('submission_date', ''),
                'submitter': assembly_info.get('submitter', ''),
                'total_sequence_length': assembly_stats.get('total_sequence_length', 0),
                'number_of_contigs': assembly_stats.get('number_of_contigs', 0),
                'scaffold_n50': assembly_stats.get('scaffold_n50', 0),
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error searching assemblies: {str(e)}")


def get_assembly_info(
    assembly_accession: str,
    include_annotation: bool = True,
    client: Optional[NCBIDatasetsClient] = None
) -> Dict[str, Any]:
    """
    Get detailed metadata and statistics for a genome assembly.
    
    Args:
        assembly_accession: Assembly accession (e.g., GCF_000001405.40)
        include_annotation: Include annotation statistics
        client: Optional NCBIDatasetsClient instance
        
    Returns:
        Dictionary with assembly information
        
    Example:
        >>> info = get_assembly_info('GCF_000001405.40')
        >>> print(f"Assembly: {info['assembly_info']['assembly_name']}")
    """
    if client is None:
        client = NCBIDatasetsClient()
    
    try:
        return client.get_assembly_info(
            assembly_accession=assembly_accession,
            include_annotation=include_annotation
        )
    except Exception as e:
        raise Exception(f"Error getting assembly info: {str(e)}")


def get_assembly_reports(
    assembly_accession: str,
    report_type: str = 'assembly_stats',
    client: Optional[NCBIDatasetsClient] = None
) -> Dict[str, Any]:
    """
    Get assembly quality reports and validation information.
    
    Args:
        assembly_accession: Assembly accession (e.g., GCF_000001405.40)
        report_type: Type of report (sequence_report, assembly_stats, annotation_report)
        client: Optional NCBIDatasetsClient instance
        
    Returns:
        Dictionary with assembly report
        
    Example:
        >>> report = get_assembly_reports('GCF_000001405.40', report_type='assembly_stats')
        >>> print(report)
    """
    if client is None:
        client = NCBIDatasetsClient()
    
    try:
        return client.get_assembly_reports(
            assembly_accession=assembly_accession,
            report_type=report_type
        )
    except Exception as e:
        raise Exception(f"Error getting assembly reports: {str(e)}")


def get_assembly_quality(
    accession: str,
    client: Optional[NCBIDatasetsClient] = None
) -> Dict[str, Any]:
    """
    Get quality metrics and validation results for genome assemblies.
    
    Args:
        accession: Assembly accession
        client: Optional NCBIDatasetsClient instance
        
    Returns:
        Dictionary with quality metrics
        
    Example:
        >>> quality = get_assembly_quality('GCF_000001405.40')
        >>> print(f"Quality metrics: {quality}")
    """
    if client is None:
        client = NCBIDatasetsClient()
    
    try:
        # Get assembly info which includes quality metrics
        response = client.get_assembly_info(
            assembly_accession=accession,
            include_annotation=True
        )
        
        # Extract quality information
        assemblies = response.get('assemblies', [])
        if assemblies:
            assembly = assemblies[0]
            assembly_info = assembly.get('assembly', {})
            
            return {
                'accession': accession,
                'assembly_stats': assembly_info.get('assembly_stats', {}),
                'annotation_info': assembly.get('annotation_info', {}),
            }
        
        return {}
        
    except Exception as e:
        raise Exception(f"Error getting assembly quality: {str(e)}")


def batch_assembly_info(
    accessions: List[str],
    include_annotation: bool = False,
    client: Optional[NCBIDatasetsClient] = None
) -> pd.DataFrame:
    """
    Get information for multiple assemblies in a single request.
    
    Args:
        accessions: List of assembly accessions (max 100)
        include_annotation: Include annotation information
        client: Optional NCBIDatasetsClient instance
        
    Returns:
        DataFrame with batch assembly information
        
    Example:
        >>> accessions = ['GCF_000001405.40', 'GCF_000001635.27']
        >>> info = batch_assembly_info(accessions)
        >>> print(info[['assembly_accession', 'assembly_name', 'organism_name']].head())
    """
    if client is None:
        client = NCBIDatasetsClient()
    
    try:
        response = client.batch_assembly_info(
            accessions=accessions,
            include_annotation=include_annotation
        )
        
        assemblies = response.get('assemblies', [])
        
        if not assemblies:
            return pd.DataFrame()
        
        # Extract key information
        records = []
        for assembly in assemblies:
            assembly_info = assembly.get('assembly', {})
            organism = assembly.get('organism', {})
            assembly_stats = assembly_info.get('assembly_stats', {})
            
            record = {
                'assembly_accession': assembly_info.get('assembly_accession', ''),
                'assembly_name': assembly_info.get('assembly_name', ''),
                'organism_name': organism.get('organism_name', ''),
                'tax_id': organism.get('tax_id', ''),
                'assembly_level': assembly_info.get('assembly_level', ''),
                'total_sequence_length': assembly_stats.get('total_sequence_length', 0),
                'number_of_contigs': assembly_stats.get('number_of_contigs', 0),
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error getting batch assembly info: {str(e)}")

