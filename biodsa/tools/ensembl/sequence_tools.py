"""
Ensembl Sequence Tools

Functions for sequence retrieval and analysis.
"""

from typing import Dict, Any, Optional, List
from .client import EnsemblClient


def get_sequence(
    region: str,
    species: Optional[str] = None,
    mask: Optional[str] = None,
    multiple_sequences: bool = False,
    client: Optional[EnsemblClient] = None
) -> Dict[str, Any]:
    """
    Get DNA sequence for genomic coordinates or gene/transcript ID.
    
    Args:
        region: Genomic region (chr:start-end) or feature ID
        species: Species name (default: homo_sapiens)
        mask: Repeat masking type (hard or soft)
        multiple_sequences: Return multiple sequences if applicable
        client: Optional EnsemblClient instance
        
    Returns:
        Dict with sequence data
        
    Example:
        >>> seq = get_sequence("1:1000000-1001000")
        >>> print(f"Sequence: {seq['seq'][:50]}...")
    """
    if client is None:
        client = EnsemblClient()
    
    try:
        return client.get_sequence(
            region,
            species=species,
            mask=mask,
            multiple_sequences=multiple_sequences
        )
    except Exception as e:
        raise Exception(f"Error getting sequence: {str(e)}")


def get_cds_sequence(
    transcript_id: str,
    species: Optional[str] = None,
    client: Optional[EnsemblClient] = None
) -> Dict[str, Any]:
    """
    Get coding sequence (CDS) for a transcript.
    
    Args:
        transcript_id: Ensembl transcript ID
        species: Species name (default: homo_sapiens)
        client: Optional EnsemblClient instance
        
    Returns:
        Dict with CDS sequence data
        
    Example:
        >>> cds = get_cds_sequence("ENST00000380152")
        >>> print(f"CDS length: {len(cds['seq'])}")
    """
    if client is None:
        client = EnsemblClient()
    
    try:
        return client.get_cds_sequence(transcript_id, species=species)
    except Exception as e:
        raise Exception(f"Error getting CDS sequence: {str(e)}")


def translate_sequence(
    sequence: str,
    genetic_code: int = 1
) -> Dict[str, Any]:
    """
    Translate DNA sequence to protein sequence.
    
    Args:
        sequence: DNA sequence to translate
        genetic_code: Genetic code table (default: 1 for standard)
        
    Returns:
        Dict with translation results
        
    Example:
        >>> result = translate_sequence("ATGGCCTAA")
        >>> print(f"Protein: {result['protein_sequence']}")
    """
    # Standard genetic code
    codon_table = {
        'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L',
        'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S',
        'TAT': 'Y', 'TAC': 'Y', 'TAA': '*', 'TAG': '*',
        'TGT': 'C', 'TGC': 'C', 'TGA': '*', 'TGG': 'W',
        'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L',
        'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
        'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
        'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
        'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M',
        'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
        'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
        'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
        'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V',
        'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
        'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
        'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G',
    }
    
    # Clean sequence
    cleaned_seq = sequence.upper().replace(' ', '').replace('\n', '')
    cleaned_seq = ''.join(c for c in cleaned_seq if c in 'ATCG')
    
    # Translate
    protein = ''
    for i in range(0, len(cleaned_seq) - 2, 3):
        codon = cleaned_seq[i:i+3]
        if len(codon) == 3:
            protein += codon_table.get(codon, 'X')
    
    return {
        'input_sequence': sequence,
        'cleaned_sequence': cleaned_seq,
        'protein_sequence': protein,
        'genetic_code': genetic_code,
        'length': len(protein)
    }


def batch_sequence_fetch(
    regions: List[str],
    species: Optional[str] = None,
    client: Optional[EnsemblClient] = None
) -> List[Dict[str, Any]]:
    """
    Fetch sequences for multiple regions or features.
    
    Args:
        regions: List of regions or feature IDs (max 50)
        species: Species name (default: homo_sapiens)
        client: Optional EnsemblClient instance
        
    Returns:
        List of sequence results
        
    Example:
        >>> results = batch_sequence_fetch(["1:1000-2000", "2:3000-4000"])
        >>> for r in results:
        >>>     if r['success']:
        >>>         print(f"{r['region']}: {len(r['data']['seq'])} bp")
    """
    if client is None:
        client = EnsemblClient()
    
    if len(regions) < 1 or len(regions) > 50:
        raise ValueError("Please provide between 1 and 50 regions")
    
    results = []
    for region in regions:
        try:
            data = client.get_sequence(region, species=species)
            results.append({
                'region': region,
                'success': True,
                'data': data
            })
        except Exception as e:
            results.append({
                'region': region,
                'success': False,
                'error': str(e)
            })
    
    return results

