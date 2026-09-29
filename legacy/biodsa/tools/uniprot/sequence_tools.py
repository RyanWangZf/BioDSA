"""
UniProt Sequence Tools

Functions for protein sequence retrieval and analysis.
"""

import pandas as pd
from typing import Dict, Any, Optional
from .client import UniProtClient


def get_protein_sequence(
    accession: str,
    format: str = 'fasta',
    client: Optional[UniProtClient] = None
) -> str:
    """
    Get the amino acid sequence for a protein.
    
    Args:
        accession: UniProt accession number
        format: Output format (fasta or json)
        client: Optional UniProtClient instance
        
    Returns:
        Protein sequence in the requested format
        
    Example:
        >>> seq = get_protein_sequence("P04637", format="fasta")
        >>> print(seq)
    """
    if client is None:
        client = UniProtClient()
    
    try:
        return client.get_protein_sequence(accession, format=format)
    
    except Exception as e:
        raise Exception(f"Error getting protein sequence: {str(e)}")


def analyze_sequence_composition(
    accession: str,
    client: Optional[UniProtClient] = None
) -> Dict[str, Any]:
    """
    Analyze amino acid composition, hydrophobicity, and other sequence properties.
    
    Args:
        accession: UniProt accession number
        client: Optional UniProtClient instance
        
    Returns:
        Dict with sequence composition analysis
        
    Example:
        >>> analysis = analyze_sequence_composition("P04637")
        >>> print(f"Length: {analysis['sequenceLength']}")
    """
    if client is None:
        client = UniProtClient()
    
    try:
        protein = client.get_protein_info(accession, format='json')
        
        sequence = protein.get('sequence', {}).get('value', '')
        
        # Calculate amino acid composition
        aa_count = {}
        aa_freq = {}
        
        for aa in sequence:
            aa_count[aa] = aa_count.get(aa, 0) + 1
        
        for aa, count in aa_count.items():
            aa_freq[aa] = count / len(sequence) if len(sequence) > 0 else 0
        
        # Calculate residue categories
        hydrophobic = sum(aa_count.get(aa, 0) for aa in ['A', 'I', 'L', 'M', 'F', 'W', 'Y', 'V'])
        charged = sum(aa_count.get(aa, 0) for aa in ['R', 'H', 'K', 'D', 'E'])
        polar = sum(aa_count.get(aa, 0) for aa in ['S', 'T', 'N', 'Q'])
        
        composition = {
            'accession': protein.get('primaryAccession', ''),
            'sequenceLength': len(sequence),
            'molecularWeight': protein.get('sequence', {}).get('molWeight', 0),
            'aminoAcidComposition': aa_count,
            'aminoAcidFrequency': aa_freq,
            'hydrophobicResidues': hydrophobic,
            'chargedResidues': charged,
            'polarResidues': polar
        }
        
        return composition
    
    except Exception as e:
        raise Exception(f"Error analyzing sequence composition: {str(e)}")


def export_protein_data(
    accession: str,
    format: str,
    client: Optional[UniProtClient] = None
) -> str:
    """
    Export data in specialized formats (GFF, GenBank, etc.).
    
    Args:
        accession: UniProt accession number
        format: Export format (gff, genbank, embl, xml)
        client: Optional UniProtClient instance
        
    Returns:
        Exported data as string
        
    Example:
        >>> data = export_protein_data("P04637", format="xml")
    """
    if client is None:
        client = UniProtClient()
    
    try:
        return client.get_protein_info(accession, format=format)
    
    except Exception as e:
        raise Exception(f"Error exporting protein data: {str(e)}")

