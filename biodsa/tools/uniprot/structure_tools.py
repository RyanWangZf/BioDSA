"""
UniProt Structure and Function Analysis Tools

Functions for analyzing protein structure, domains, and variants.
"""

import pandas as pd
from typing import Dict, Any, Optional
from .client import UniProtClient


def get_protein_structure(
    accession: str,
    client: Optional[UniProtClient] = None
) -> Dict[str, Any]:
    """
    Retrieve 3D structure information from PDB references.
    
    Args:
        accession: UniProt accession number
        client: Optional UniProtClient instance
        
    Returns:
        Dict with protein structure information
        
    Example:
        >>> structure = get_protein_structure("P04637")
        >>> print(f"PDB entries: {len(structure['pdbReferences'])}")
    """
    if client is None:
        client = UniProtClient()
    
    try:
        protein = client.get_protein_info(accession, format='json')
        
        # Filter cross-references for PDB
        pdb_refs = [ref for ref in protein.get('uniProtKBCrossReferences', []) 
                    if ref.get('database') == 'PDB']
        
        # Filter features for structural features
        structural_features = [f for f in protein.get('features', []) 
                               if f.get('type') in ['Secondary structure', 'Turn', 'Helix', 'Beta strand']]
        
        # Filter comments for structural information
        structural_comments = [c for c in protein.get('comments', []) 
                               if c.get('commentType') == 'SUBUNIT']
        
        structure_info = {
            'accession': protein.get('primaryAccession', ''),
            'pdbReferences': pdb_refs,
            'structuralFeatures': structural_features,
            'structuralComments': structural_comments
        }
        
        return structure_info
    
    except Exception as e:
        raise Exception(f"Error fetching protein structure: {str(e)}")


def get_protein_domains_detailed(
    accession: str,
    client: Optional[UniProtClient] = None
) -> Dict[str, Any]:
    """
    Enhanced domain analysis with InterPro, Pfam, and SMART annotations.
    
    Args:
        accession: UniProt accession number
        client: Optional UniProtClient instance
        
    Returns:
        Dict with detailed domain information
        
    Example:
        >>> domains = get_protein_domains_detailed("P04637")
        >>> print(f"Domains: {len(domains['domains'])}")
    """
    if client is None:
        client = UniProtClient()
    
    try:
        protein = client.get_protein_info(accession, format='json')
        
        # Extract domain-related features
        domains = [f for f in protein.get('features', []) if f.get('type') == 'Domain']
        regions = [f for f in protein.get('features', []) if f.get('type') == 'Region']
        repeats = [f for f in protein.get('features', []) if f.get('type') == 'Repeat']
        
        # Extract domain database cross-references
        cross_refs = protein.get('uniProtKBCrossReferences', [])
        interpro_refs = [ref for ref in cross_refs if ref.get('database') == 'InterPro']
        pfam_refs = [ref for ref in cross_refs if ref.get('database') == 'Pfam']
        smart_refs = [ref for ref in cross_refs if ref.get('database') == 'SMART']
        
        domain_info = {
            'accession': protein.get('primaryAccession', ''),
            'domains': domains,
            'regions': regions,
            'repeats': repeats,
            'interproReferences': interpro_refs,
            'pfamReferences': pfam_refs,
            'smartReferences': smart_refs
        }
        
        return domain_info
    
    except Exception as e:
        raise Exception(f"Error fetching protein domains: {str(e)}")


def get_protein_variants(
    accession: str,
    client: Optional[UniProtClient] = None
) -> Dict[str, Any]:
    """
    Get disease-associated variants and mutations.
    
    Args:
        accession: UniProt accession number
        client: Optional UniProtClient instance
        
    Returns:
        Dict with variant information
        
    Example:
        >>> variants = get_protein_variants("P04637")
        >>> print(f"Natural variants: {len(variants['naturalVariants'])}")
    """
    if client is None:
        client = UniProtClient()
    
    try:
        protein = client.get_protein_info(accession, format='json')
        
        # Extract variant features
        features = protein.get('features', [])
        natural_variants = [f for f in features if f.get('type') == 'Natural variant']
        mutagenesis = [f for f in features if f.get('type') == 'Mutagenesis']
        disease_variants = [f for f in natural_variants 
                            if f.get('association', {}).get('disease')]
        
        # Extract polymorphism comments
        polymorphisms = [c for c in protein.get('comments', []) 
                         if c.get('commentType') == 'POLYMORPHISM']
        
        variant_info = {
            'accession': protein.get('primaryAccession', ''),
            'naturalVariants': natural_variants,
            'mutagenesisFeatures': mutagenesis,
            'diseaseVariants': disease_variants,
            'polymorphisms': polymorphisms
        }
        
        return variant_info
    
    except Exception as e:
        raise Exception(f"Error fetching protein variants: {str(e)}")


def get_annotation_confidence(
    accession: str,
    client: Optional[UniProtClient] = None
) -> Dict[str, Any]:
    """
    Get quality scores for different annotations.
    
    Args:
        accession: UniProt accession number
        client: Optional UniProtClient instance
        
    Returns:
        Dict with annotation confidence information
        
    Example:
        >>> confidence = get_annotation_confidence("P04637")
        >>> print(f"Review status: {confidence['reviewStatus']}")
    """
    if client is None:
        client = UniProtClient()
    
    try:
        protein = client.get_protein_info(accession, format='json')
        
        # Extract evidence codes from features
        evidence_codes = []
        for feature in protein.get('features', []):
            if 'evidences' in feature:
                evidence_codes.extend(feature['evidences'])
        
        confidence_info = {
            'accession': protein.get('primaryAccession', ''),
            'entryType': protein.get('entryType', ''),
            'proteinExistence': protein.get('proteinExistence', ''),
            'annotationScore': protein.get('annotationScore', 'Not available'),
            'evidenceCodes': [e for e in evidence_codes if e is not None],
            'reviewStatus': 'Reviewed' if protein.get('entryType') == 'UniProtKB reviewed (Swiss-Prot)' else 'Unreviewed',
            'referenceCount': len(protein.get('references', []))
        }
        
        return confidence_info
    
    except Exception as e:
        raise Exception(f"Error fetching annotation confidence: {str(e)}")

