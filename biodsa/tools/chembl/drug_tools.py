"""Drug-specific tools for ChEMBL Database.

This module provides tools for retrieving drug-specific information
including indications, mechanisms of action, and clinical development data.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .client import ChEMBLClient

logger = logging.getLogger(__name__)


def get_drug_indications(
    molecule_chembl_id: Optional[str] = None,
    indication: Optional[str] = None,
    limit: int = 25,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Search for therapeutic indications and disease areas.
    
    Args:
        molecule_chembl_id: ChEMBL compound ID filter (e.g., "CHEMBL25")
        indication: Disease or indication search term
        limit: Number of results to return (default: 25)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with indications, formatted output string)
        
    Examples:
        >>> # Get indications for a specific drug
        >>> df, output = get_drug_indications(molecule_chembl_id="CHEMBL25")
        >>> print(output)
        >>> 
        >>> # Search by indication
        >>> df, output = get_drug_indications(indication="cancer")
        >>> print(output)
    """
    try:
        client = ChEMBLClient()
        results = client.get_drug_indications(
            molecule_chembl_id=molecule_chembl_id,
            indication=indication,
            limit=limit
        )
        
        indications = results.get('drug_indications', [])
        
        # Convert to DataFrame
        df = pd.DataFrame(indications)
        
        # Format output
        output = f"# Drug Indications\n\n"
        
        if molecule_chembl_id:
            output += f"**Compound:** {molecule_chembl_id}\n"
        if indication:
            output += f"**Indication Search:** '{indication}'\n"
        
        output += f"**Results found:** {len(indications)}\n\n"
        
        if not indications:
            output += "No indications found.\n"
        else:
            output += "## Therapeutic Indications:\n\n"
            for i, ind in enumerate(indications[:15], 1):
                drug_id = ind.get('molecule_chembl_id', 'N/A')
                ind_name = ind.get('indication', 'N/A')
                
                output += f"### {i}. {ind_name}\n"
                output += f"   - **ChEMBL ID:** {drug_id}\n"
                
                # Max phase
                if ind.get('max_phase_for_ind') is not None:
                    phases = ['Preclinical', 'Phase I', 'Phase II', 'Phase III', 'Approved']
                    phase = ind.get('max_phase_for_ind', 0)
                    try:
                        phase = int(phase)
                        output += f"   - **Max Phase:** {phases[phase] if 0 <= phase < len(phases) else phase}\n"
                    except (ValueError, TypeError):
                        output += f"   - **Max Phase:** {phase}\n"
                
                # EFO info
                if ind.get('efo_term'):
                    output += f"   - **EFO Term:** {ind['efo_term']}\n"
                if ind.get('efo_id'):
                    output += f"   - **EFO ID:** {ind['efo_id']}\n"
                
                output += "\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error getting drug indications: {e}")
        error_msg = f"Error getting drug indications: {str(e)}"
        return pd.DataFrame(), error_msg


def get_drug_mechanisms(
    molecule_chembl_id: Optional[str] = None,
    target_chembl_id: Optional[str] = None,
    limit: int = 50,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Get mechanism of action and target interaction data.
    
    Args:
        molecule_chembl_id: ChEMBL compound ID filter (e.g., "CHEMBL25")
        target_chembl_id: ChEMBL target ID filter (e.g., "CHEMBL2095173")
        limit: Number of results to return (default: 50)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with mechanisms, formatted output string)
        
    Examples:
        >>> # Get mechanisms for a specific drug
        >>> df, output = get_drug_mechanisms(molecule_chembl_id="CHEMBL25")
        >>> print(output)
        >>> 
        >>> # Get drugs targeting a specific target
        >>> df, output = get_drug_mechanisms(target_chembl_id="CHEMBL2095173")
        >>> print(output)
    """
    try:
        client = ChEMBLClient()
        results = client.get_mechanisms(
            molecule_chembl_id=molecule_chembl_id,
            target_chembl_id=target_chembl_id,
            limit=limit
        )
        
        mechanisms = results.get('mechanisms', [])
        
        # Convert to DataFrame
        df = pd.DataFrame(mechanisms)
        
        # Format output
        output = f"# Drug Mechanisms of Action\n\n"
        
        if molecule_chembl_id:
            output += f"**Compound:** {molecule_chembl_id}\n"
        if target_chembl_id:
            output += f"**Target:** {target_chembl_id}\n"
        
        output += f"**Results found:** {len(mechanisms)}\n\n"
        
        if not mechanisms:
            output += "No mechanisms found.\n"
        else:
            output += "## Mechanisms:\n\n"
            for i, mech in enumerate(mechanisms[:20], 1):
                drug_id = mech.get('molecule_chembl_id', 'N/A')
                target_id = mech.get('target_chembl_id', 'N/A')
                action_type = mech.get('action_type', 'N/A')
                mechanism = mech.get('mechanism_of_action', 'N/A')
                
                output += f"### {i}. {mechanism}\n"
                output += f"   - **Drug:** {drug_id}\n"
                output += f"   - **Target:** {target_id}\n"
                output += f"   - **Action Type:** {action_type}\n"
                
                # Target name
                if mech.get('target_pref_name'):
                    output += f"   - **Target Name:** {mech['target_pref_name']}\n"
                
                # Direct interaction
                if mech.get('direct_interaction') is not None:
                    output += f"   - **Direct Interaction:** {mech['direct_interaction']}\n"
                
                # Disease efficacy
                if mech.get('disease_efficacy') is not None:
                    output += f"   - **Disease Efficacy:** {mech['disease_efficacy']}\n"
                
                output += "\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error getting drug mechanisms: {e}")
        error_msg = f"Error getting drug mechanisms: {str(e)}"
        return pd.DataFrame(), error_msg


def get_drug_clinical_data(
    chembl_id: str,
    save_path: Optional[str] = None
) -> Tuple[Dict[str, Any], str]:
    """Get comprehensive clinical and drug development data for a compound.
    
    This function aggregates indications, mechanisms, and basic compound info.
    
    Args:
        chembl_id: ChEMBL compound ID (e.g., "CHEMBL25")
        save_path: Optional path to save results as JSON
        
    Returns:
        Tuple of (dictionary with clinical data, formatted output string)
        
    Examples:
        >>> # Get all clinical data for aspirin
        >>> data, output = get_drug_clinical_data("CHEMBL25")
        >>> print(output)
        >>> print(data.keys())  # ['compound', 'indications', 'mechanisms']
    """
    try:
        client = ChEMBLClient()
        
        # Get compound details
        compound = client.get_compound_by_id(chembl_id)
        
        # Get indications
        indications_result = client.get_drug_indications(
            molecule_chembl_id=chembl_id,
            limit=100
        )
        indications = indications_result.get('drug_indications', [])
        
        # Get mechanisms
        mechanisms_result = client.get_mechanisms(
            molecule_chembl_id=chembl_id,
            limit=100
        )
        mechanisms = mechanisms_result.get('mechanisms', [])
        
        # Compile data
        clinical_data = {
            'compound': compound,
            'indications': indications,
            'mechanisms': mechanisms
        }
        
        # Format output
        output = f"# Clinical Data for {chembl_id}\n\n"
        
        # Compound info
        output += f"## {compound.get('pref_name', 'N/A')} ({chembl_id})\n\n"
        output += f"**Type:** {compound.get('molecule_type', 'N/A')}\n"
        
        # Development phase
        if compound.get('max_phase') is not None:
            phases = ['Preclinical', 'Phase I', 'Phase II', 'Phase III', 'Approved']
            phase = compound.get('max_phase', 0)
            try:
                phase = int(phase)
                output += f"**Development Phase:** {phases[phase] if 0 <= phase < len(phases) else 'Unknown'}\n"
            except (ValueError, TypeError):
                output += f"**Development Phase:** {phase}\n"
        
        output += "\n"
        
        # Molecular properties
        props = compound.get('molecule_properties', {})
        if props:
            output += "### Molecular Properties\n"
            output += f"- **Molecular Weight:** {props.get('full_mwt', props.get('molecular_weight', 'N/A'))} Da\n"
            output += f"- **LogP:** {props.get('alogp', 'N/A')}\n"
            output += f"- **Lipinski Violations:** {props.get('num_ro5_violations', 'N/A')}\n"
            output += "\n"
        
        # Indications
        output += f"## Therapeutic Indications ({len(indications)} found)\n\n"
        if indications:
            for i, ind in enumerate(indications[:10], 1):
                ind_name = ind.get('indication', 'N/A')
                output += f"{i}. **{ind_name}**"
                
                if ind.get('max_phase_for_ind') is not None:
                    phases = ['Preclinical', 'Phase I', 'Phase II', 'Phase III', 'Approved']
                    phase = ind.get('max_phase_for_ind', 0)
                    try:
                        phase = int(phase)
                        phase_str = phases[phase] if 0 <= phase < len(phases) else str(phase)
                        output += f" - {phase_str}"
                    except (ValueError, TypeError):
                        output += f" - {phase}"
                
                output += "\n"
            
            if len(indications) > 10:
                output += f"\n... and {len(indications) - 10} more indications\n"
        else:
            output += "No indications found in ChEMBL.\n"
        
        output += "\n"
        
        # Mechanisms
        output += f"## Mechanisms of Action ({len(mechanisms)} found)\n\n"
        if mechanisms:
            for i, mech in enumerate(mechanisms[:10], 1):
                mechanism = mech.get('mechanism_of_action', 'N/A')
                target = mech.get('target_pref_name', mech.get('target_chembl_id', 'N/A'))
                action = mech.get('action_type', 'N/A')
                
                output += f"{i}. **{mechanism}**\n"
                output += f"   - Target: {target}\n"
                output += f"   - Action: {action}\n"
                output += "\n"
            
            if len(mechanisms) > 10:
                output += f"... and {len(mechanisms) - 10} more mechanisms\n"
        else:
            output += "No mechanisms found in ChEMBL.\n"
        
        # Save if path provided
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(clinical_data, f, indent=2)
            output += f"\n**Full data saved to:** {save_path}\n"
        
        return clinical_data, output
    
    except Exception as e:
        logger.error(f"Error getting clinical data: {e}")
        error_msg = f"Error getting clinical data: {str(e)}"
        return {}, error_msg


def search_drugs_by_indication(
    indication: str,
    min_phase: int = 0,
    limit: int = 25,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Search for drugs treating a specific indication or disease.
    
    Args:
        indication: Disease or indication name
        min_phase: Minimum development phase (0=Preclinical, 4=Approved)
        limit: Number of results to return (default: 25)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with drugs, formatted output string)
        
    Examples:
        >>> # Find all drugs for cancer
        >>> df, output = search_drugs_by_indication("cancer", min_phase=1)
        >>> print(output)
        >>> 
        >>> # Find approved drugs for diabetes
        >>> df, output = search_drugs_by_indication("diabetes", min_phase=4)
        >>> print(output)
    """
    try:
        client = ChEMBLClient()
        
        # Search for indications
        results = client.get_drug_indications(
            indication=indication,
            limit=limit * 3  # Get more to filter by phase
        )
        
        indications = results.get('drug_indications', [])
        
        # Filter by minimum phase
        if min_phase > 0:
            filtered = []
            for ind in indications:
                phase = ind.get('max_phase_for_ind')
                if phase is not None:
                    try:
                        if int(phase) >= min_phase:
                            filtered.append(ind)
                    except (ValueError, TypeError):
                        pass
            indications = filtered[:limit]
        else:
            indications = indications[:limit]
        
        # Get unique drugs
        seen_drugs = set()
        unique_drugs = []
        for ind in indications:
            drug_id = ind.get('molecule_chembl_id')
            if drug_id and drug_id not in seen_drugs:
                unique_drugs.append(ind)
                seen_drugs.add(drug_id)
        
        # Convert to DataFrame
        df = pd.DataFrame(unique_drugs)
        
        # Format output
        output = f"# Drugs for Indication: '{indication}'\n\n"
        output += f"**Minimum Phase:** {min_phase}\n"
        output += f"**Unique drugs found:** {len(unique_drugs)}\n\n"
        
        if not unique_drugs:
            output += "No drugs found for this indication.\n"
        else:
            output += "## Drugs:\n\n"
            
            phases = ['Preclinical', 'Phase I', 'Phase II', 'Phase III', 'Approved']
            
            for i, ind in enumerate(unique_drugs[:20], 1):
                drug_id = ind.get('molecule_chembl_id', 'N/A')
                ind_name = ind.get('indication', 'N/A')
                
                output += f"### {i}. {drug_id}\n"
                output += f"   - **Indication:** {ind_name}\n"
                
                # Phase
                if ind.get('max_phase_for_ind') is not None:
                    phase = ind.get('max_phase_for_ind')
                    try:
                        phase = int(phase)
                        output += f"   - **Phase:** {phases[phase] if 0 <= phase < len(phases) else phase}\n"
                    except (ValueError, TypeError):
                        output += f"   - **Phase:** {phase}\n"
                
                output += "\n"
            
            if len(unique_drugs) > 20:
                output += f"\n... and {len(unique_drugs) - 20} more drugs\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error searching drugs by indication: {e}")
        error_msg = f"Error searching drugs by indication: {str(e)}"
        return pd.DataFrame(), error_msg

