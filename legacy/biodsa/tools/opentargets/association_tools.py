"""Target-disease association and evidence tools for Open Targets Platform.

This module provides tools for retrieving and analyzing target-disease associations
and supporting evidence from the Open Targets Platform.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .client import OpenTargetsClient

logger = logging.getLogger(__name__)


def get_target_disease_evidence(
    target_id: str,
    disease_id: str,
    size: int = 10,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Get evidence linking a specific target to a specific disease.
    
    Args:
        target_id: Target Ensembl gene ID (e.g., "ENSG00000139618")
        disease_id: Disease EFO ID (e.g., "EFO_0000508")
        size: Number of evidence items to return (default: 10)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with evidence, formatted output string)
        
    Examples:
        >>> df, output = get_target_disease_evidence(
        ...     "ENSG00000139618",
        ...     "EFO_0000508",
        ...     size=5
        ... )
        >>> print(output)
        >>> print(df[['datasourceId', 'datatypeId', 'score']])
    """
    try:
        client = OpenTargetsClient()
        response = client.get_target_disease_evidence(
            target_id,
            disease_id,
            size=size
        )
        
        disease_data = response.get('data', {}).get('disease', {})
        evidences = disease_data.get('evidences', {})
        rows = evidences.get('rows', [])
        
        # Convert to DataFrame
        data_records = []
        for row in rows:
            target = row.get('target', {})
            disease = row.get('disease', {})
            record = {
                'target_id': target.get('id'),
                'target_symbol': target.get('approvedSymbol'),
                'disease_id': disease.get('id'),
                'disease_name': disease.get('name'),
                'score': row.get('score'),
                'datasourceId': row.get('datasourceId'),
                'datatypeId': row.get('datatypeId')
            }
            data_records.append(record)
        
        df = pd.DataFrame(data_records)
        
        # Format output
        output = f"# Target-Disease Evidence\n\n"
        output += f"**Target ID:** {target_id}\n"
        output += f"**Disease ID:** {disease_id}\n"
        output += f"**Total evidence items:** {evidences.get('count', 0)}\n"
        output += f"**Showing:** {len(rows)} items\n\n"
        
        if not rows:
            output += "No evidence found for this target-disease pair.\n"
        else:
            output += "## Evidence Items:\n\n"
            
            # Group by datasource for better readability
            by_datasource = {}
            for row in rows:
                datasource = row.get('datasourceId', 'unknown')
                if datasource not in by_datasource:
                    by_datasource[datasource] = []
                by_datasource[datasource].append(row)
            
            for datasource, evidence_items in by_datasource.items():
                output += f"### {datasource}\n"
                for item in evidence_items[:5]:  # Show up to 5 per datasource
                    output += f"- **Data Type:** {item.get('datatypeId', 'N/A')}\n"
                    output += f"  **Score:** {item.get('score', 'N/A'):.4f}\n"
                output += "\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error getting target-disease evidence: {e}")
        error_msg = f"Error getting target-disease evidence: {str(e)}"
        return pd.DataFrame(), error_msg


def analyze_association_evidence(
    target_id: Optional[str] = None,
    disease_id: Optional[str] = None,
    min_score: float = 0.5,
    size: int = 25,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Analyze target-disease associations with evidence breakdown.
    
    This function provides a comprehensive analysis of associations for either
    a target or a disease, including evidence type breakdown.
    
    Args:
        target_id: Target Ensembl gene ID (provide either this or disease_id)
        disease_id: Disease EFO ID (provide either this or target_id)
        min_score: Minimum association score threshold (0-1, default: 0.5)
        size: Number of associations to analyze (default: 25)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with associations and evidence, formatted output string)
        
    Examples:
        >>> # Analyze associations for a target
        >>> df, output = analyze_association_evidence(
        ...     target_id="ENSG00000139618",
        ...     min_score=0.6,
        ...     size=10
        ... )
        >>> print(output)
    """
    try:
        if not target_id and not disease_id:
            raise ValueError("Must provide either target_id or disease_id")
        
        if target_id and disease_id:
            raise ValueError("Provide only one of target_id or disease_id")
        
        client = OpenTargetsClient()
        
        if target_id:
            response = client.get_target_associations(
                target_id,
                size=size,
                min_score=min_score
            )
            entity_type = "target"
            entity_data = response.get('data', {}).get('target', {})
            entity_name = f"{entity_data.get('approvedSymbol', 'N/A')} ({entity_data.get('approvedName', 'N/A')})"
            associations = entity_data.get('associatedDiseases', {})
        else:
            response = client.get_disease_associations(
                disease_id,
                size=size,
                min_score=min_score
            )
            entity_type = "disease"
            entity_data = response.get('data', {}).get('disease', {})
            entity_name = entity_data.get('name', 'N/A')
            associations = entity_data.get('associatedTargets', {})
        
        rows = associations.get('rows', [])
        
        # Convert to DataFrame with detailed evidence breakdown
        data_records = []
        for row in rows:
            if entity_type == "target":
                partner = row.get('disease', {})
                partner_id = partner.get('id')
                partner_name = partner.get('name')
            else:
                partner = row.get('target', {})
                partner_id = partner.get('id')
                partner_name = f"{partner.get('approvedSymbol', 'N/A')} - {partner.get('approvedName', 'N/A')}"
            
            record = {
                'partner_id': partner_id,
                'partner_name': partner_name,
                'overall_score': row.get('score')
            }
            
            # Add datatype scores
            datatype_scores = row.get('datatypeScores', [])
            for ds in datatype_scores:
                record[f"score_{ds.get('id', 'unknown')}"] = ds.get('score')
            
            data_records.append(record)
        
        df = pd.DataFrame(data_records)
        
        # Format output
        output = f"# Association Evidence Analysis\n\n"
        output += f"**{entity_type.capitalize()}:** {entity_name}\n"
        output += f"**Total associations:** {associations.get('count', 0)}\n"
        output += f"**Minimum score filter:** {min_score}\n"
        output += f"**Showing:** {len(rows)} associations\n\n"
        
        if not rows:
            output += f"No associations found meeting the criteria.\n"
        else:
            # Calculate evidence type statistics
            evidence_types = set()
            for row in rows:
                for ds in row.get('datatypeScores', []):
                    evidence_types.add(ds.get('id', 'unknown'))
            
            output += f"## Evidence Types Observed:\n"
            for ev_type in sorted(evidence_types):
                output += f"- {ev_type}\n"
            output += "\n"
            
            output += f"## Top Associations:\n\n"
            for i, row in enumerate(rows[:10], 1):
                if entity_type == "target":
                    partner = row.get('disease', {})
                    partner_name = partner.get('name', 'N/A')
                else:
                    partner = row.get('target', {})
                    partner_name = f"{partner.get('approvedSymbol', 'N/A')} - {partner.get('approvedName', 'N/A')}"
                
                output += f"### {i}. {partner_name}\n"
                output += f"   - **Overall Score:** {row.get('score', 'N/A'):.4f}\n"
                
                # Show evidence breakdown
                datatype_scores = row.get('datatypeScores', [])
                if datatype_scores:
                    output += "   - **Evidence Breakdown:**\n"
                    sorted_scores = sorted(
                        datatype_scores,
                        key=lambda x: x.get('score', 0),
                        reverse=True
                    )
                    for ds in sorted_scores:
                        output += f"     - {ds.get('id', 'unknown')}: {ds.get('score', 'N/A'):.4f}\n"
                output += "\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error analyzing associations: {e}")
        error_msg = f"Error analyzing associations: {str(e)}"
        return pd.DataFrame(), error_msg

