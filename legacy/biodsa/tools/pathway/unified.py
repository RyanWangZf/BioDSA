"""Unified pathway search and retrieval across multiple APIs.

This module aggregates pathway information from:
- KEGG Pathways
- Gene Ontology Biological Processes
"""

import logging
import json
from typing import Optional, Dict, Any, List, Tuple

from biodsa.tools.kegg.client import KEGGClient
from biodsa.tools.gene_ontology.client import GeneOntologyClient


# ================================================
# Unified Pathway Search Function
# ================================================

def search_pathways_unified(
    search_term: str,
    limit_per_source: int = 20,
    sources: Optional[List[str]] = None,
    save_path: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Search for pathways across multiple databases with a simple search term.
    
    This function queries KEGG Pathways and Gene Ontology databases and aggregates
    the results, providing a comprehensive view of pathway information.
    
    Args:
        search_term: Search query (pathway name, biological process, etc.)
        limit_per_source: Maximum results per source (default: 20)
        sources: List of sources to search. If None, searches all.
                 Options: ['kegg', 'go']
        save_path: Optional path to save aggregated results
    
    Returns:
        Tuple of (dict of results by source, formatted output string)
        
    Examples:
        >>> # Search for apoptosis pathways across all sources
        >>> results, output = search_pathways_unified("apoptosis", limit_per_source=10)
        >>> print(output)
    """
    if sources is None:
        sources = ['kegg', 'go']
    
    results = {}
    summaries = []
    errors = []
    
    # Search KEGG Pathways
    if 'kegg' in sources:
        try:
            kegg_client = KEGGClient()
            kegg_results = kegg_client.search_pathways(
                query=search_term,
                max_results=limit_per_source
            )
            results['kegg'] = kegg_results
            summaries.append(f"**KEGG Pathways:** Found {len(kegg_results)} pathways")
        except Exception as e:
            logging.error(f"KEGG search failed: {e}")
            results['kegg'] = []
            errors.append(f"KEGG: {str(e)}")
    
    # Search Gene Ontology Biological Processes
    if 'go' in sources:
        try:
            go_client = GeneOntologyClient()
            go_results = go_client.search_terms(
                query=search_term,
                ontology="biological_process",
                limit=limit_per_source
            )
            go_terms = go_results.get('results', [])
            results['go'] = go_terms
            summaries.append(f"**Gene Ontology:** Found {len(go_terms)} biological processes")
        except Exception as e:
            logging.error(f"GO search failed: {e}")
            results['go'] = []
            errors.append(f"Gene Ontology: {str(e)}")
    
    # Build formatted output string
    output = "# Unified Pathway Search Results\n\n"
    output += f"## Search Term: '{search_term}'\n"
    output += "\n"
    
    # Count total results
    total_results = 0
    if 'kegg' in results:
        total_results += len(results['kegg']) if isinstance(results['kegg'], list) else 0
    if 'go' in results:
        total_results += len(results['go']) if isinstance(results['go'], list) else 0
    
    output += f"**Total results:** {total_results} across {len(sources)} sources\n\n"
    output += "### Results by Source:\n"
    for s in summaries:
        output += f"- {s}\n"
    
    if errors:
        output += "\n### Errors:\n"
        for e in errors:
            output += f"- ⚠️ {e}\n"
    
    output += "\n" + "="*80 + "\n\n"
    
    # Format KEGG results
    if 'kegg' in results and results['kegg']:
        kegg_pathways = results['kegg']
        output += f"## KEGG PATHWAYS Results\n\n"
        output += f"Found {len(kegg_pathways)} pathways from KEGG:\n\n"
        for idx, pathway in enumerate(kegg_pathways[:10], 1):
            pathway_id = pathway.get('id', 'N/A')
            description = pathway.get('description', 'N/A')
            output += f"**{idx}. {pathway_id}** - {description}\n"
        if len(kegg_pathways) > 10:
            output += f"\n... and {len(kegg_pathways) - 10} more pathways\n"
        output += "\n"
    
    # Format GO results
    if 'go' in results and results['go']:
        go_terms = results['go']
        output += f"## GENE ONTOLOGY Biological Processes\n\n"
        output += f"Found {len(go_terms)} terms from Gene Ontology:\n\n"
        for idx, term in enumerate(go_terms[:10], 1):
            term_id = term.get('id', 'N/A')
            term_name = term.get('name', 'N/A')
            term_def = term.get('definition', {}).get('text', 'No definition')
            if len(term_def) > 150:
                term_def = term_def[:150] + "..."
            output += f"**{idx}. {term_id}** - {term_name}\n"
            output += f"  Definition: {term_def}\n\n"
        if len(go_terms) > 10:
            output += f"... and {len(go_terms) - 10} more terms\n"
        output += "\n"
    
    # Save results if requested
    if save_path:
        try:
            save_data = {
                'search_term': search_term,
                'sources': sources,
                'results': results
            }
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            output += f"\n**Results saved to:** {save_path}\n"
        except Exception as e:
            logging.error(f"Error saving results: {e}")
            output += f"\n⚠️ **Error saving results:** {e}\n"
    
    return results, output


# ================================================
# Unified Pathway Fetch Function
# ================================================

def fetch_pathway_details_unified(
    pathway_id: str,
    id_type: Optional[str] = None,
    sources: Optional[List[str]] = None,
    include_genes: bool = True,
    include_compounds: bool = True,
    include_reactions: bool = False,
    save_path: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Fetch detailed pathway information using any pathway identifier.
    
    This function automatically detects the ID type (if not specified) and
    queries relevant databases to fetch comprehensive pathway information.
    
    Args:
        pathway_id: Pathway identifier (KEGG ID like hsa04210, GO ID like GO:0006915)
        id_type: Type of ID. If None, will attempt to detect.
                 Options: 'kegg', 'go'
        sources: List of sources to fetch from. If None, fetches from detected source.
                 Options: ['kegg', 'go']
        include_genes: Include genes associated with the pathway (default: True)
        include_compounds: Include compounds in the pathway (KEGG only, default: True)
        include_reactions: Include reactions in the pathway (KEGG only, default: False)
        save_path: Optional path to save results as JSON
    
    Returns:
        Tuple of (dict of pathway details by source, formatted output string)
        
    Examples:
        >>> # Fetch KEGG pathway details
        >>> details, output = fetch_pathway_details_unified("hsa04210")
        >>> print(output)
        
        >>> # Fetch GO term details
        >>> details, output = fetch_pathway_details_unified("GO:0006915")
        >>> print(output)
    """
    # Auto-detect ID type if not specified
    if id_type is None:
        id_type = _detect_pathway_id_type(pathway_id)
    
    if sources is None:
        sources = ['kegg'] if id_type == 'kegg' else ['go']
    
    details = {}
    summaries = []
    errors = []
    
    # Fetch from KEGG
    if 'kegg' in sources and id_type == 'kegg':
        try:
            kegg_client = KEGGClient()
            
            # Get pathway information
            pathway_info = kegg_client.get_pathway_info(pathway_id, format='json')
            details['kegg'] = {
                'pathway_id': pathway_id,
                'pathway_info': pathway_info
            }
            summaries.append(f"**KEGG:** Found pathway information")
            
            # Get pathway genes
            if include_genes:
                try:
                    genes = kegg_client.get_pathway_genes(pathway_id)
                    details['kegg']['genes'] = genes
                except Exception as e:
                    details['kegg']['genes_error'] = str(e)
            
            # Get pathway compounds
            if include_compounds:
                try:
                    compounds = kegg_client.get_pathway_compounds(pathway_id)
                    details['kegg']['compounds'] = compounds
                except Exception as e:
                    details['kegg']['compounds_error'] = str(e)
            
            # Get pathway reactions
            if include_reactions:
                try:
                    reactions = kegg_client.get_pathway_reactions(pathway_id)
                    details['kegg']['reactions'] = reactions
                except Exception as e:
                    details['kegg']['reactions_error'] = str(e)
                    
        except Exception as e:
            logging.error(f"KEGG fetch failed: {e}")
            errors.append(f"KEGG: {str(e)}")
    
    # Fetch from Gene Ontology
    if 'go' in sources and id_type == 'go':
        try:
            go_client = GeneOntologyClient()
            
            # Get term information
            term_response = go_client.get_term(pathway_id)
            term_info = term_response.get('results', [{}])[0]
            
            details['go'] = {
                'term_id': pathway_id,
                'term_info': term_info
            }
            summaries.append(f"**Gene Ontology:** Found term information")
            
            # Get term ancestors
            if include_genes:
                try:
                    ancestors_response = go_client.get_term_ancestors(pathway_id)
                    ancestors = ancestors_response.get('results', [])
                    details['go']['ancestors'] = ancestors
                except Exception as e:
                    details['go']['ancestors_error'] = str(e)
            
            # Get term children
            try:
                children_response = go_client.get_term_children(pathway_id)
                children = children_response.get('results', [])
                details['go']['children'] = children
            except Exception as e:
                details['go']['children_error'] = str(e)
            
            # Get annotations
            if include_genes:
                try:
                    annotations_response = go_client.get_annotations(go_id=pathway_id, limit=50)
                    annotations = annotations_response.get('results', [])
                    details['go']['annotations'] = annotations
                except Exception as e:
                    details['go']['annotations_error'] = str(e)
                    
        except Exception as e:
            logging.error(f"GO fetch failed: {e}")
            errors.append(f"Gene Ontology: {str(e)}")
    
    # Build formatted output string
    output = "# Unified Pathway Details\n\n"
    output += f"## Query: '{pathway_id}' (Type: {id_type})\n\n"
    
    output += "### Fetch Summary:\n"
    for s in summaries:
        output += f"- {s}\n"
    
    if errors:
        output += "\n### Errors:\n"
        for e in errors:
            output += f"- ⚠️ {e}\n"
    
    output += "\n" + "="*80 + "\n\n"
    
    # Format KEGG details
    if 'kegg' in details:
        kegg_data = details['kegg']
        pathway_info = kegg_data.get('pathway_info', {})
        
        output += "## KEGG Pathway Details\n\n"
        output += f"**ID:** {kegg_data.get('pathway_id', 'N/A')}\n"
        output += f"**Name:** {pathway_info.get('NAME', 'Unknown')}\n"
        
        if 'DESCRIPTION' in pathway_info:
            output += f"**Description:** {pathway_info['DESCRIPTION']}\n"
        if 'CLASS' in pathway_info:
            output += f"**Class:** {pathway_info['CLASS']}\n"
        
        # Genes
        genes = kegg_data.get('genes', [])
        if genes:
            output += f"\n**Pathway Genes ({len(genes)}):**\n"
            for i, gene in enumerate(genes[:10], 1):
                output += f"  {i}. {gene.get('target', 'Unknown')}\n"
            if len(genes) > 10:
                output += f"  ... and {len(genes) - 10} more\n"
        
        # Compounds
        compounds = kegg_data.get('compounds', [])
        if compounds:
            output += f"\n**Pathway Compounds ({len(compounds)}):**\n"
            for i, compound in enumerate(compounds[:10], 1):
                output += f"  {i}. {compound.get('target', 'Unknown')}\n"
            if len(compounds) > 10:
                output += f"  ... and {len(compounds) - 10} more\n"
        
        # Reactions
        reactions = kegg_data.get('reactions', [])
        if reactions:
            output += f"\n**Pathway Reactions ({len(reactions)}):**\n"
            for i, rxn in enumerate(reactions[:10], 1):
                output += f"  {i}. {rxn.get('target', 'Unknown')}\n"
            if len(reactions) > 10:
                output += f"  ... and {len(reactions) - 10} more\n"
        
        pathway_id = kegg_data.get('pathway_id', '')
        output += f"\n**KEGG Pathway Map:** https://www.kegg.jp/pathway/{pathway_id}\n"
        output += f"**KEGG Entry:** https://www.kegg.jp/entry/{pathway_id}\n\n"
    
    # Format GO details
    if 'go' in details:
        go_data = details['go']
        term_info = go_data.get('term_info', {})
        
        output += "## Gene Ontology Term Details\n\n"
        output += f"**ID:** {go_data.get('term_id', 'N/A')}\n"
        output += f"**Name:** {term_info.get('name', 'Unknown')}\n"
        output += f"**Aspect:** {term_info.get('aspect', 'Unknown')}\n"
        
        term_def = term_info.get('definition', {}).get('text', 'No definition')
        output += f"**Definition:** {term_def}\n"
        
        # Ancestors
        ancestors = go_data.get('ancestors', [])
        if ancestors:
            output += f"\n**Ancestor Terms ({len(ancestors)}):**\n"
            for i, ancestor in enumerate(ancestors[:5], 1):
                output += f"  {i}. {ancestor.get('id')}: {ancestor.get('name')}\n"
            if len(ancestors) > 5:
                output += f"  ... and {len(ancestors) - 5} more\n"
        
        # Children
        children = go_data.get('children', [])
        if children:
            output += f"\n**Child Terms ({len(children)}):**\n"
            for i, child in enumerate(children[:5], 1):
                output += f"  {i}. {child.get('id')}: {child.get('name')}\n"
            if len(children) > 5:
                output += f"  ... and {len(children) - 5} more\n"
        
        # Annotations
        annotations = go_data.get('annotations', [])
        if annotations:
            output += f"\n**Gene Annotations ({len(annotations)}):**\n"
            unique_genes = set()
            for annotation in annotations[:20]:
                gene_id = annotation.get('geneProductId', 'Unknown')
                gene_symbol = annotation.get('symbol', gene_id)
                unique_genes.add(f"{gene_symbol} ({gene_id})")
            
            for i, gene in enumerate(sorted(list(unique_genes))[:10], 1):
                output += f"  {i}. {gene}\n"
            if len(unique_genes) > 10:
                output += f"  ... and {len(unique_genes) - 10} more genes\n"
        
        output += f"\n**QuickGO URL:** https://www.ebi.ac.uk/QuickGO/term/{go_data.get('term_id', '')}\n\n"
    
    # Save results if requested
    if save_path:
        try:
            save_data = {
                'pathway_id': pathway_id,
                'id_type': id_type,
                'sources': sources,
                'details': details
            }
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent=2, default=str)
            output += f"\n**Details saved to:** {save_path}\n"
        except Exception as e:
            logging.error(f"Error saving details: {e}")
            output += f"\n⚠️ **Error saving details:** {e}\n"
    
    return details, output


# ================================================
# Helper Functions
# ================================================

def _detect_pathway_id_type(pathway_id: str) -> str:
    """
    Detect the type of pathway identifier.
    
    Args:
        pathway_id: Pathway identifier string
    
    Returns:
        Detected ID type: 'kegg', 'go', or 'name'
    """
    pathway_id = pathway_id.strip()
    
    # GO term: GO:0000000
    if pathway_id.upper().startswith('GO:'):
        return 'go'
    
    # KEGG pathway: map00010, hsa00010, ko00010, etc.
    import re
    if re.match(r'^(map|hsa|mmu|rno|dme|cel|sce|eco|ath|ko)\d{5}$', pathway_id.lower()):
        return 'kegg'
    
    # Default to name search
    return 'name'

