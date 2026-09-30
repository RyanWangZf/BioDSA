"""
OpenGenes API - Gene Operations

High-level functions for gene-related operations focused on aging and longevity.
"""

from typing import Optional, Dict, Any, List
import pandas as pd
from biodsa.tools.opengenes.client import OpenGenesClient


def search_genes(
    by_gene_symbol: Optional[str] = None,
    by_diseases: Optional[str] = None,
    by_aging_mechanism: Optional[str] = None,
    by_protein_class: Optional[str] = None,
    by_species: Optional[str] = None,
    confidence_level: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    lang: str = 'en',
    client: Optional[OpenGenesClient] = None
) -> pd.DataFrame:
    """
    Search for aging-related genes with multiple filter parameters.
    
    Args:
        by_gene_symbol: Filter by gene symbol
        by_diseases: Filter by diseases
        by_aging_mechanism: Filter by aging mechanism
        by_protein_class: Filter by protein class
        by_species: Filter by species
        confidence_level: Filter by confidence level
        page: Page number
        page_size: Page size
        lang: Language (en or ru)
        client: Optional OpenGenesClient instance
        
    Returns:
        DataFrame with gene search results
        
    Example:
        >>> genes = search_genes(by_aging_mechanism='cellular_senescence')
        >>> print(genes[['symbol', 'name', 'ncbi_id']].head())
    """
    if client is None:
        client = OpenGenesClient()
    
    try:
        response = client.search_genes(
            lang=lang,
            page=page,
            page_size=page_size,
            by_gene_symbol=by_gene_symbol,
            by_diseases=by_diseases,
            by_aging_mechanism=by_aging_mechanism,
            by_protein_class=by_protein_class,
            by_species=by_species,
            confidence_level=confidence_level
        )
        
        if 'items' not in response:
            return pd.DataFrame()
        
        items = response['items']
        if not items:
            return pd.DataFrame()
        
        # Format results
        records = []
        for gene in items:
            record = {
                'id': gene.get('id'),
                'symbol': gene.get('symbol'),
                'name': gene.get('name'),
                'ncbi_id': gene.get('ncbiId'),
                'aliases': ', '.join(gene.get('aliases', [])) if gene.get('aliases') else '',
                'protein_class': gene.get('proteinClass'),
                'confidence_level': gene.get('confidenceLevel'),
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error searching genes: {str(e)}")


def get_gene_by_symbol(
    symbol: str,
    lang: str = 'en',
    client: Optional[OpenGenesClient] = None
) -> Dict[str, Any]:
    """
    Get detailed information for a gene by its symbol.
    
    Args:
        symbol: Gene symbol (e.g., TP53, FOXO3)
        lang: Language (en or ru)
        client: Optional OpenGenesClient instance
        
    Returns:
        Dictionary with gene details
        
    Example:
        >>> gene = get_gene_by_symbol('FOXO3')
        >>> print(f"Gene: {gene['name']}")
        >>> print(f"Function: {gene.get('functionalDescription')}")
    """
    if client is None:
        client = OpenGenesClient()
    
    try:
        return client.get_gene_by_symbol(symbol=symbol, lang=lang)
    except Exception as e:
        raise Exception(f"Error getting gene by symbol: {str(e)}")


def get_gene_by_ncbi_id(
    ncbi_id: str,
    lang: str = 'en',
    client: Optional[OpenGenesClient] = None
) -> Dict[str, Any]:
    """
    Get detailed information for a gene by its NCBI ID.
    
    Args:
        ncbi_id: NCBI Gene ID
        lang: Language (en or ru)
        client: Optional OpenGenesClient instance
        
    Returns:
        Dictionary with gene details
        
    Example:
        >>> gene = get_gene_by_ncbi_id('2309')  # FOXO3
        >>> print(f"Symbol: {gene['symbol']}")
    """
    if client is None:
        client = OpenGenesClient()
    
    try:
        return client.get_gene_by_ncbi_id(ncbi_id=ncbi_id, lang=lang)
    except Exception as e:
        raise Exception(f"Error getting gene by NCBI ID: {str(e)}")


def get_latest_genes(
    page: int = 1,
    page_size: int = 20,
    lang: str = 'en',
    client: Optional[OpenGenesClient] = None
) -> pd.DataFrame:
    """
    Get recently added genes.
    
    Args:
        page: Page number
        page_size: Page size
        lang: Language (en or ru)
        client: Optional OpenGenesClient instance
        
    Returns:
        DataFrame with recently added genes
        
    Example:
        >>> latest = get_latest_genes(page_size=10)
        >>> print(latest[['symbol', 'name']].head())
    """
    if client is None:
        client = OpenGenesClient()
    
    try:
        response = client.get_latest_genes(lang=lang, page=page, page_size=page_size)
        
        if 'items' not in response:
            return pd.DataFrame()
        
        items = response['items']
        if not items:
            return pd.DataFrame()
        
        records = []
        for gene in items:
            record = {
                'id': gene.get('id'),
                'symbol': gene.get('symbol'),
                'name': gene.get('name'),
                'ncbi_id': gene.get('ncbiId'),
                'added_date': gene.get('addedDate'),
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error getting latest genes: {str(e)}")


def get_genes_increase_lifespan(
    page: int = 1,
    page_size: int = 20,
    lang: str = 'en',
    client: Optional[OpenGenesClient] = None
) -> pd.DataFrame:
    """
    Get genes that have been shown to increase lifespan in model organisms.
    
    Args:
        page: Page number
        page_size: Page size
        lang: Language (en or ru)
        client: Optional OpenGenesClient instance
        
    Returns:
        DataFrame with lifespan-extending genes
        
    Example:
        >>> lifespan_genes = get_genes_increase_lifespan()
        >>> print(lifespan_genes[['symbol', 'name', 'confidence_level']].head())
    """
    if client is None:
        client = OpenGenesClient()
    
    try:
        response = client.get_genes_increase_lifespan(lang=lang, page=page, page_size=page_size)
        
        if 'items' not in response:
            return pd.DataFrame()
        
        items = response['items']
        if not items:
            return pd.DataFrame()
        
        records = []
        for gene in items:
            record = {
                'id': gene.get('id'),
                'symbol': gene.get('symbol'),
                'name': gene.get('name'),
                'ncbi_id': gene.get('ncbiId'),
                'confidence_level': gene.get('confidenceLevel'),
                'lifespan_effect': gene.get('lifespanEffect'),
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error getting lifespan-extending genes: {str(e)}")


def get_gene_symbols(
    lang: str = 'en',
    client: Optional[OpenGenesClient] = None
) -> List[str]:
    """
    Get all gene symbols in the database.
    
    Args:
        lang: Language (en or ru)
        client: Optional OpenGenesClient instance
        
    Returns:
        List of gene symbols
        
    Example:
        >>> symbols = get_gene_symbols()
        >>> print(f"Total genes: {len(symbols)}")
    """
    if client is None:
        client = OpenGenesClient()
    
    try:
        return client.get_gene_symbols(lang=lang)
    except Exception as e:
        raise Exception(f"Error getting gene symbols: {str(e)}")


from typing import List

def get_genes_by_go_term(
    go_term: str,
    page: int = 1,
    page_size: int = 20,
    lang: str = 'en',
    client: Optional[OpenGenesClient] = None
) -> pd.DataFrame:
    """
    Get genes associated with a specific GO term.
    
    Args:
        go_term: Gene Ontology term
        page: Page number
        page_size: Page size
        lang: Language (en or ru)
        client: Optional OpenGenesClient instance
        
    Returns:
        DataFrame with genes for the GO term
        
    Example:
        >>> genes = get_genes_by_go_term('DNA repair')
        >>> print(genes[['symbol', 'name']].head())
    """
    if client is None:
        client = OpenGenesClient()
    
    try:
        response = client.get_genes_by_go_term(term=go_term, lang=lang, page=page, page_size=page_size)
        
        if 'items' not in response:
            return pd.DataFrame()
        
        items = response['items']
        if not items:
            return pd.DataFrame()
        
        records = []
        for gene in items:
            record = {
                'id': gene.get('id'),
                'symbol': gene.get('symbol'),
                'name': gene.get('name'),
                'ncbi_id': gene.get('ncbiId'),
            }
            records.append(record)
        
        return pd.DataFrame(records)
        
    except Exception as e:
        raise Exception(f"Error getting genes by GO term: {str(e)}")

