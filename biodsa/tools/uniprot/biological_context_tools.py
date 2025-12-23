"""
UniProt Biological Context Tools

Functions for analyzing protein pathways, interactions, and biological functions.
"""

import pandas as pd
from typing import Dict, Any, Optional
from .client import UniProtClient


def get_protein_pathways(
    accession: str,
    client: Optional[UniProtClient] = None
) -> Dict[str, Any]:
    """
    Get associated biological pathways (KEGG, Reactome).
    
    Args:
        accession: UniProt accession number
        client: Optional UniProtClient instance
        
    Returns:
        Dict with pathway information
        
    Example:
        >>> pathways = get_protein_pathways("P04637")
        >>> print(f"KEGG pathways: {len(pathways['keggReferences'])}")
    """
    if client is None:
        client = UniProtClient()
    
    try:
        protein = client.get_protein_info(accession, format='json')
        
        # Extract pathway-related cross-references
        cross_refs = protein.get('uniProtKBCrossReferences', [])
        kegg_refs = [ref for ref in cross_refs if ref.get('database') == 'KEGG']
        reactome_refs = [ref for ref in cross_refs if ref.get('database') == 'Reactome']
        
        # Extract pathway comments
        pathway_comments = [c for c in protein.get('comments', []) 
                            if c.get('commentType') == 'PATHWAY']
        
        # Extract function comments
        function_comments = [c for c in protein.get('comments', []) 
                             if c.get('commentType') == 'FUNCTION']
        
        pathway_info = {
            'accession': protein.get('primaryAccession', ''),
            'keggReferences': kegg_refs,
            'reactomeReferences': reactome_refs,
            'pathwayComments': pathway_comments,
            'biologicalProcess': function_comments
        }
        
        return pathway_info
    
    except Exception as e:
        raise Exception(f"Error fetching protein pathways: {str(e)}")


def get_protein_interactions(
    accession: str,
    client: Optional[UniProtClient] = None
) -> Dict[str, Any]:
    """
    Get protein-protein interaction networks.
    
    Args:
        accession: UniProt accession number
        client: Optional UniProtClient instance
        
    Returns:
        Dict with interaction information
        
    Example:
        >>> interactions = get_protein_interactions("P04637")
        >>> print(f"Interaction comments: {len(interactions['interactionComments'])}")
    """
    if client is None:
        client = UniProtClient()
    
    try:
        protein = client.get_protein_info(accession, format='json')
        
        # Extract interaction-related cross-references
        cross_refs = protein.get('uniProtKBCrossReferences', [])
        string_refs = [ref for ref in cross_refs if ref.get('database') == 'STRING']
        intact_refs = [ref for ref in cross_refs if ref.get('database') == 'IntAct']
        
        # Extract interaction comments
        interaction_comments = [c for c in protein.get('comments', []) 
                                if c.get('commentType') == 'INTERACTION']
        
        # Extract subunit comments
        subunit_comments = [c for c in protein.get('comments', []) 
                            if c.get('commentType') == 'SUBUNIT']
        
        interaction_info = {
            'accession': protein.get('primaryAccession', ''),
            'stringReferences': string_refs,
            'intactReferences': intact_refs,
            'interactionComments': interaction_comments,
            'subunitComments': subunit_comments
        }
        
        return interaction_info
    
    except Exception as e:
        raise Exception(f"Error fetching protein interactions: {str(e)}")


def search_by_function(
    go_term: Optional[str] = None,
    function: Optional[str] = None,
    organism: Optional[str] = None,
    size: int = 25,
    client: Optional[UniProtClient] = None
) -> pd.DataFrame:
    """
    Search proteins by GO terms or functional annotations.
    
    Args:
        go_term: Gene Ontology term (e.g., GO:0005524)
        function: Functional description or keyword
        organism: Organism name or taxonomy ID to filter results
        size: Number of results to return (1-500, default: 25)
        client: Optional UniProtClient instance
        
    Returns:
        DataFrame with search results
        
    Example:
        >>> df = search_by_function(go_term="GO:0005524", organism="human")
        >>> print(df[['primaryAccession', 'proteinName', 'organism']])
    """
    if client is None:
        client = UniProtClient()
    
    if not go_term and not function:
        raise ValueError("Please provide at least one of: go_term or function")
    
    try:
        data = client.search_by_function(
            go_term=go_term,
            function=function,
            organism=organism,
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
                'taxonId': entry.get('organism', {}).get('taxonId', '')
            })
        
        return pd.DataFrame(results)
    
    except Exception as e:
        raise Exception(f"Error searching by function: {str(e)}")


def search_by_localization(
    localization: str,
    organism: Optional[str] = None,
    size: int = 25,
    client: Optional[UniProtClient] = None
) -> pd.DataFrame:
    """
    Find proteins by subcellular localization.
    
    Args:
        localization: Subcellular localization (e.g., nucleus, mitochondria)
        organism: Organism name or taxonomy ID to filter results
        size: Number of results to return (1-500, default: 25)
        client: Optional UniProtClient instance
        
    Returns:
        DataFrame with search results
        
    Example:
        >>> df = search_by_localization("nucleus", organism="human")
        >>> print(df[['primaryAccession', 'proteinName', 'organism']])
    """
    if client is None:
        client = UniProtClient()
    
    try:
        data = client.search_by_localization(localization=localization, organism=organism, size=size)
        
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
                'taxonId': entry.get('organism', {}).get('taxonId', '')
            })
        
        return pd.DataFrame(results)
    
    except Exception as e:
        raise Exception(f"Error searching by localization: {str(e)}")


def get_external_references(
    accession: str,
    client: Optional[UniProtClient] = None
) -> Dict[str, Any]:
    """
    Get links to other databases (PDB, EMBL, RefSeq, etc.).
    
    Args:
        accession: UniProt accession number
        client: Optional UniProtClient instance
        
    Returns:
        Dict with external database references
        
    Example:
        >>> refs = get_external_references("P04637")
        >>> print(f"Total references: {len(refs['allReferences'])}")
    """
    if client is None:
        client = UniProtClient()
    
    try:
        protein = client.get_protein_info(accession, format='json')
        
        # Extract all cross-references
        all_refs = protein.get('uniProtKBCrossReferences', [])
        
        external_refs = {
            'accession': protein.get('primaryAccession', ''),
            'allReferences': all_refs,
            'pdbReferences': [ref for ref in all_refs if ref.get('database') == 'PDB'],
            'emblReferences': [ref for ref in all_refs if ref.get('database') == 'EMBL'],
            'refseqReferences': [ref for ref in all_refs if ref.get('database') == 'RefSeq'],
            'ensemblReferences': [ref for ref in all_refs if ref.get('database') == 'Ensembl'],
            'goReferences': [ref for ref in all_refs if ref.get('database') == 'GO']
        }
        
        return external_refs
    
    except Exception as e:
        raise Exception(f"Error fetching external references: {str(e)}")


def get_literature_references(
    accession: str,
    client: Optional[UniProtClient] = None
) -> Dict[str, Any]:
    """
    Get associated publications and citations.
    
    Args:
        accession: UniProt accession number
        client: Optional UniProtClient instance
        
    Returns:
        Dict with literature references
        
    Example:
        >>> lit = get_literature_references("P04637")
        >>> print(f"Citation count: {lit['citationCount']}")
    """
    if client is None:
        client = UniProtClient()
    
    try:
        protein = client.get_protein_info(accession, format='json')
        
        # Extract references
        references = protein.get('references', [])
        
        # Extract PubMed cross-references
        cross_refs = protein.get('uniProtKBCrossReferences', [])
        pubmed_refs = [ref for ref in cross_refs if ref.get('database') == 'PubMed']
        
        literature_info = {
            'accession': protein.get('primaryAccession', ''),
            'references': references,
            'pubmedReferences': pubmed_refs,
            'citationCount': len(references)
        }
        
        return literature_info
    
    except Exception as e:
        raise Exception(f"Error fetching literature references: {str(e)}")

