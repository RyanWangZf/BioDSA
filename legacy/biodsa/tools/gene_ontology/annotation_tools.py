"""Gene Ontology annotation tools.

This module provides tools for retrieving and analyzing GO annotations
for genes and proteins.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .client import GeneOntologyClient

logger = logging.getLogger(__name__)


def get_gene_annotations(
    gene_product_id: str,
    taxon_id: Optional[int] = None,
    ontology: Optional[str] = None,
    evidence_code: Optional[str] = None,
    limit: int = 100,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Get GO annotations for a specific gene.
    
    Args:
        gene_product_id: Gene product identifier (e.g., UniProt ID, gene symbol)
        taxon_id: NCBI taxonomy ID (e.g., 9606 for human)
        ontology: GO ontology filter ("molecular_function", "biological_process",
                 "cellular_component", or None for all)
        evidence_code: Evidence code filter (e.g., "IDA", "IEA")
        limit: Number of results to return (default: 100)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with annotations, formatted output string)
        
    Examples:
        >>> df, output = get_gene_annotations("P31749", taxon_id=9606)
        >>> print(output)
        >>> print(df[['goId', 'goName', 'evidenceCode']])
    """
    try:
        client = GeneOntologyClient()
        response = client.get_gene_annotations(
            gene_product_id,
            taxon_id=taxon_id,
            ontology=ontology,
            evidence_code=evidence_code,
            limit=limit
        )
        
        annotations = response.get('results', [])
        
        # Convert to DataFrame
        annotation_data = []
        for ann in annotations:
            aspect = ann.get('goAspect', '')
            namespace = (
                'molecular_function' if aspect == 'F' else
                'biological_process' if aspect == 'P' else
                'cellular_component' if aspect == 'C' else
                'unknown'
            )
            
            annotation_data.append({
                'gene_product_id': ann.get('geneProductId'),
                'gene_symbol': ann.get('symbol'),
                'go_id': ann.get('goId'),
                'go_name': ann.get('goName'),
                'ontology': namespace,
                'evidence_code': ann.get('evidenceCode'),
                'reference': ann.get('reference'),
                'taxon_id': ann.get('taxonId'),
                'qualifier': ann.get('qualifier')
            })
        
        df = pd.DataFrame(annotation_data)
        
        # Format output
        output = f"# Gene Annotations\n\n"
        output += f"**Gene product:** {gene_product_id}\n"
        if taxon_id:
            output += f"**Taxonomy ID:** {taxon_id}\n"
        if ontology:
            output += f"**Ontology filter:** {ontology}\n"
        if evidence_code:
            output += f"**Evidence code filter:** {evidence_code}\n"
        output += f"**Annotations found:** {response.get('numberOfHits', 0)}\n"
        output += f"**Returned:** {len(annotations)}\n\n"
        
        if not annotations:
            output += "No annotations found for this gene.\n"
        else:
            # Group by ontology
            by_ontology = {}
            for ann in annotations:
                aspect = ann.get('goAspect', '')
                namespace = (
                    'molecular_function' if aspect == 'F' else
                    'biological_process' if aspect == 'P' else
                    'cellular_component' if aspect == 'C' else
                    'unknown'
                )
                if namespace not in by_ontology:
                    by_ontology[namespace] = []
                by_ontology[namespace].append(ann)
            
            for namespace, anns in by_ontology.items():
                output += f"## {namespace.replace('_', ' ').title()} ({len(anns)} annotations)\n\n"
                
                for i, ann in enumerate(anns[:10], 1):
                    output += f"### {i}. {ann.get('goName', 'N/A')}\n"
                    output += f"   - **GO ID:** {ann.get('goId', 'N/A')}\n"
                    output += f"   - **Evidence:** {ann.get('evidenceCode', 'N/A')}\n"
                    output += f"   - **Reference:** {ann.get('reference', 'N/A')}\n"
                    if ann.get('qualifier'):
                        output += f"   - **Qualifier:** {ann.get('qualifier')}\n"
                    output += "\n"
                
                if len(anns) > 10:
                    output += f"   *(and {len(anns) - 10} more...)*\n\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error getting gene annotations: {e}")
        error_msg = f"Error getting gene annotations: {str(e)}"
        return pd.DataFrame(), error_msg


def get_term_annotations(
    go_id: str,
    taxon_id: Optional[int] = None,
    evidence_code: Optional[str] = None,
    limit: int = 100,
    save_path: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """Get annotations for a specific GO term.
    
    Args:
        go_id: GO term identifier
        taxon_id: NCBI taxonomy ID filter (e.g., 9606 for human)
        evidence_code: Evidence code filter (e.g., "IDA", "IEA")
        limit: Number of results to return (default: 100)
        save_path: Optional path to save results as CSV
        
    Returns:
        Tuple of (DataFrame with annotations, formatted output string)
        
    Examples:
        >>> df, output = get_term_annotations("GO:0004672", taxon_id=9606)
        >>> print(output)
        >>> print(df[['gene_symbol', 'gene_product_id', 'evidenceCode']])
    """
    try:
        client = GeneOntologyClient()
        go_id = client.normalize_go_id(go_id)
        
        response = client.get_annotations(
            go_id=go_id,
            taxon_id=taxon_id,
            evidence_code=evidence_code,
            limit=limit
        )
        
        annotations = response.get('results', [])
        
        # Convert to DataFrame
        annotation_data = []
        for ann in annotations:
            annotation_data.append({
                'gene_product_id': ann.get('geneProductId'),
                'gene_symbol': ann.get('symbol'),
                'go_id': ann.get('goId'),
                'go_name': ann.get('goName'),
                'evidence_code': ann.get('evidenceCode'),
                'reference': ann.get('reference'),
                'taxon_id': ann.get('taxonId'),
                'assigned_by': ann.get('assignedBy'),
                'qualifier': ann.get('qualifier')
            })
        
        df = pd.DataFrame(annotation_data)
        
        # Format output
        output = f"# GO Term Annotations\n\n"
        output += f"**GO term:** {go_id}\n"
        if taxon_id:
            output += f"**Taxonomy ID:** {taxon_id}\n"
        if evidence_code:
            output += f"**Evidence code filter:** {evidence_code}\n"
        output += f"**Annotations found:** {response.get('numberOfHits', 0)}\n"
        output += f"**Returned:** {len(annotations)}\n\n"
        
        if not annotations:
            output += "No annotations found for this GO term.\n"
        else:
            output += "## Gene Products:\n\n"
            
            # Group by evidence code for summary
            by_evidence = {}
            for ann in annotations:
                evidence = ann.get('evidenceCode', 'Unknown')
                if evidence not in by_evidence:
                    by_evidence[evidence] = []
                by_evidence[evidence].append(ann)
            
            output += "### Summary by Evidence Code:\n"
            for evidence, anns in sorted(by_evidence.items(), key=lambda x: len(x[1]), reverse=True):
                output += f"- **{evidence}:** {len(anns)} annotations\n"
            output += "\n"
            
            output += "### Top Annotated Genes:\n\n"
            for i, ann in enumerate(annotations[:20], 1):
                output += f"{i}. **{ann.get('symbol', 'N/A')}** ({ann.get('geneProductId', 'N/A')})\n"
                output += f"   - Evidence: {ann.get('evidenceCode', 'N/A')}\n"
                output += f"   - Reference: {ann.get('reference', 'N/A')}\n"
                if ann.get('qualifier'):
                    output += f"   - Qualifier: {ann.get('qualifier')}\n"
                output += "\n"
            
            if len(annotations) > 20:
                output += f"   *(and {len(annotations) - 20} more...)*\n\n"
        
        # Save if path provided
        if save_path and not df.empty:
            df.to_csv(save_path, index=False)
            output += f"\n**Results saved to:** {save_path}\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error getting term annotations: {e}")
        error_msg = f"Error getting term annotations: {str(e)}"
        return pd.DataFrame(), error_msg


def get_evidence_codes() -> Tuple[pd.DataFrame, str]:
    """Get list of GO evidence codes.
    
    Returns:
        Tuple of (DataFrame with evidence codes, formatted output string)
        
    Examples:
        >>> df, output = get_evidence_codes()
        >>> print(output)
        >>> print(df[['code', 'category', 'name']])
    """
    try:
        client = GeneOntologyClient()
        codes = client.get_evidence_codes()
        
        df = pd.DataFrame(codes)
        
        # Format output
        output = f"# GO Evidence Codes\n\n"
        output += f"**Total codes:** {len(codes)}\n\n"
        
        # Group by category
        by_category = {}
        for code in codes:
            category = code['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(code)
        
        for category, category_codes in by_category.items():
            output += f"## {category.replace('_', ' ').title()} ({len(category_codes)} codes)\n\n"
            
            for code in category_codes:
                output += f"### {code['code']} - {code['name']}\n"
            output += "\n"
        
        output += "## Evidence Code Hierarchy\n\n"
        output += "**Most reliable (top) to least reliable (bottom):**\n"
        output += "1. Experimental evidence (e.g., IDA, IMP)\n"
        output += "2. High-throughput evidence (e.g., HDA, HMP)\n"
        output += "3. Computational evidence (e.g., ISS, ISO)\n"
        output += "4. Author statements (e.g., TAS, NAS)\n"
        output += "5. Curator statements (e.g., IC, ND)\n"
        output += "6. Electronic annotations (IEA)\n"
        
        return df, output
    
    except Exception as e:
        logger.error(f"Error getting evidence codes: {e}")
        error_msg = f"Error getting evidence codes: {str(e)}"
        return pd.DataFrame(), error_msg

