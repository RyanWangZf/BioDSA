"""
PubChem Chemical Properties and Descriptors Tools

Functions for calculating and retrieving molecular properties.
"""

from typing import Dict, Any, Optional, List, Union
from .client import PubChemClient


def get_compound_properties(
    cid: Union[int, str],
    properties: Optional[List[str]] = None,
    client: Optional[PubChemClient] = None
) -> Dict[str, Any]:
    """
    Get molecular properties (MW, logP, TPSA, etc.).
    
    Args:
        cid: PubChem Compound ID
        properties: Specific properties to retrieve
        client: Optional PubChemClient instance
        
    Returns:
        Dict with molecular properties
        
    Example:
        >>> props = get_compound_properties(2244)
        >>> print(f"MW: {props.get('MolecularWeight')}")
        >>> print(f"LogP: {props.get('XLogP')}")
    """
    if client is None:
        client = PubChemClient()
    
    try:
        return client.get_compound_properties(cid, properties=properties)
    except Exception as e:
        raise Exception(f"Error getting properties: {str(e)}")


def calculate_descriptors(
    cid: Union[int, str],
    descriptor_type: str = 'all',
    client: Optional[PubChemClient] = None
) -> Dict[str, Any]:
    """
    Calculate comprehensive molecular descriptors.
    
    Args:
        cid: PubChem Compound ID
        descriptor_type: Type of descriptors (all, basic, topological, 3d)
        client: Optional PubChemClient instance
        
    Returns:
        Dict with molecular descriptors
        
    Example:
        >>> descriptors = calculate_descriptors(2244, descriptor_type='all')
        >>> print(descriptors)
    """
    if client is None:
        client = PubChemClient()
    
    try:
        if descriptor_type == 'basic':
            properties = ['MolecularWeight', 'MolecularFormula', 'CanonicalSMILES',
                         'InChI', 'InChIKey', 'IUPACName']
        elif descriptor_type == 'topological':
            properties = ['XLogP', 'TPSA', 'Complexity', 'HBondDonorCount',
                         'HBondAcceptorCount', 'RotatableBondCount',
                         'HeavyAtomCount', 'Charge']
        elif descriptor_type == '3d':
            properties = ['Volume3D', 'ConformerCount3D']
        else:  # all
            properties = [
                'MolecularWeight', 'MolecularFormula', 'CanonicalSMILES',
                'InChI', 'InChIKey', 'IUPACName', 'XLogP', 'TPSA',
                'Complexity', 'HBondDonorCount', 'HBondAcceptorCount',
                'RotatableBondCount', 'HeavyAtomCount', 'Charge'
            ]
        
        return client.get_compound_properties(cid, properties=properties)
    except Exception as e:
        raise Exception(f"Error calculating descriptors: {str(e)}")


def assess_drug_likeness(
    cid: Union[int, str],
    client: Optional[PubChemClient] = None
) -> Dict[str, Any]:
    """
    Assess drug-likeness using Lipinski Rule of Five and other metrics.
    
    Args:
        cid: PubChem Compound ID
        client: Optional PubChemClient instance
        
    Returns:
        Dict with drug-likeness assessment
        
    Example:
        >>> assessment = assess_drug_likeness(2244)
        >>> print(f"Passes Lipinski: {assessment['passes_lipinski']}")
    """
    if client is None:
        client = PubChemClient()
    
    try:
        properties = ['MolecularWeight', 'XLogP', 'HBondDonorCount',
                     'HBondAcceptorCount', 'RotatableBondCount', 'TPSA']
        
        props = client.get_compound_properties(cid, properties=properties)
        
        # Lipinski Rule of Five
        # Ensure all values are numeric
        try:
            mw = float(props.get('MolecularWeight', 0))
            logp = float(props.get('XLogP', 0)) if props.get('XLogP') is not None else 0
            hbd = int(props.get('HBondDonorCount', 0))
            hba = int(props.get('HBondAcceptorCount', 0))
        except (ValueError, TypeError):
            mw = logp = hbd = hba = 0
        
        lipinski_violations = 0
        if mw > 500:
            lipinski_violations += 1
        if logp > 5:
            lipinski_violations += 1
        if hbd > 5:
            lipinski_violations += 1
        if hba > 10:
            lipinski_violations += 1
        
        # Veber rules
        try:
            rotatable_bonds = int(props.get('RotatableBondCount', 0))
            tpsa = float(props.get('TPSA', 0))
        except (ValueError, TypeError):
            rotatable_bonds = tpsa = 0
        
        veber_compliant = rotatable_bonds <= 10 and tpsa <= 140
        
        return {
            'cid': cid,
            'properties': props,
            'lipinski_violations': lipinski_violations,
            'passes_lipinski': lipinski_violations <= 1,
            'veber_compliant': veber_compliant,
            'assessment': 'Drug-like' if lipinski_violations <= 1 and veber_compliant else 'Non-drug-like'
        }
    except Exception as e:
        raise Exception(f"Error assessing drug-likeness: {str(e)}")


def analyze_molecular_complexity(
    cid: Union[int, str],
    client: Optional[PubChemClient] = None
) -> Dict[str, Any]:
    """
    Analyze molecular complexity and synthetic accessibility.
    
    Args:
        cid: PubChem Compound ID
        client: Optional PubChemClient instance
        
    Returns:
        Dict with complexity analysis
        
    Example:
        >>> complexity = analyze_molecular_complexity(2244)
        >>> print(f"Complexity score: {complexity['complexity_score']}")
    """
    if client is None:
        client = PubChemClient()
    
    try:
        properties = ['Complexity', 'HeavyAtomCount', 'RotatableBondCount',
                     'MolecularWeight']
        
        props = client.get_compound_properties(cid, properties=properties)
        
        complexity_score = props.get('Complexity', 0)
        heavy_atoms = props.get('HeavyAtomCount', 0)
        
        # Simple complexity categorization
        if complexity_score < 100:
            category = 'Simple'
        elif complexity_score < 300:
            category = 'Moderate'
        elif complexity_score < 600:
            category = 'Complex'
        else:
            category = 'Very Complex'
        
        return {
            'cid': cid,
            'complexity_score': complexity_score,
            'heavy_atom_count': heavy_atoms,
            'complexity_category': category,
            'properties': props
        }
    except Exception as e:
        raise Exception(f"Error analyzing complexity: {str(e)}")

