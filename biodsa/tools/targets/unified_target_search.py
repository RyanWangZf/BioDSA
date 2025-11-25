"""Unified target search and retrieval across multiple APIs.

This module aggregates biological target information from:
- Open Targets Platform (therapeutic targets, target-disease associations)
- KEGG (pathways, genes, molecular interactions)
- Gene Ontology (functional annotations, biological processes)
- Human Protein Atlas (protein expression, cancer markers, pathology)
"""

import logging
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import individual API modules
from biodsa.tools.opentargets.target_tools import (
    search_targets as opentargets_search_targets,
    get_target_details as opentargets_get_target_details,
    get_target_associated_diseases
)
from biodsa.tools.kegg.client import KEGGClient
from biodsa.tools.gene_ontology.term_tools import search_go_terms, get_go_term_details
from biodsa.tools.proteinatlas import (
    search_proteins as proteinatlas_search_proteins,
    search_cancer_markers,
    get_protein_info,
    get_pathology_data
)

# ================================================
# Unified Search Function
# ================================================

def search_targets_unified(
    search_term: str,
    search_type: Optional[str] = None,
    limit_per_source: int = 10,
    sources: Optional[List[str]] = None,
    save_path: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Search for biological targets across multiple databases.
    
    This function queries multiple databases in parallel and aggregates
    the results, providing a comprehensive view of biological targets including
    therapeutic targets, pathways, genes, and functional annotations.
    
    Args:
        search_term: Search term (target name, gene name, pathway name, GO term)
        search_type: Type of search ('target', 'pathway', 'go_term', 'gene', or None for all)
        limit_per_source: Maximum results per source (default: 10)
        sources: List of sources to search. If None, searches all.
                 Options: ['opentargets', 'kegg_pathways', 'kegg_genes', 'gene_ontology', 'proteinatlas']
        save_path: Optional path to save aggregated results
    
    Returns:
        Tuple of (dict of results by source, formatted output string)
        
    Examples:
        >>> # Search for BRCA1 target across all sources
        >>> results, output = search_targets_unified("BRCA1", limit_per_source=5)
        >>> print(output)  # Prints formatted results
        
        >>> # Search specifically for pathways
        >>> results, output = search_targets_unified("apoptosis", search_type='pathway')
        >>> print(output)
    """
    if sources is None:
        if search_type == 'pathway':
            sources = ['kegg_pathways']
        elif search_type == 'go_term':
            sources = ['gene_ontology']
        elif search_type == 'gene':
            sources = ['opentargets', 'kegg_genes', 'proteinatlas']
        elif search_type == 'target':
            sources = ['opentargets', 'proteinatlas']
        else:
            sources = ['opentargets', 'kegg_pathways', 'kegg_genes', 'gene_ontology', 'proteinatlas']
    
    results = {}
    summaries = []
    errors = []
    
    # Search Open Targets (therapeutic targets)
    if 'opentargets' in sources:
        try:
            df, summary = opentargets_search_targets(
                query=search_term,
                size=limit_per_source
            )
            results['opentargets'] = df
            summaries.append(f"**Open Targets:** Found {len(df)} therapeutic targets")
        except Exception as e:
            logging.error(f"Open Targets search failed: {e}")
            results['opentargets'] = pd.DataFrame()
            errors.append(f"Open Targets: {str(e)}")
    
    # Search KEGG Pathways
    if 'kegg_pathways' in sources:
        try:
            kegg_client = KEGGClient()
            pathway_results = kegg_client.search_pathways(search_term, max_results=limit_per_source)
            results['kegg_pathways'] = pathway_results  # List of dicts
            summaries.append(f"**KEGG Pathways:** Found {len(pathway_results)} pathways")
        except Exception as e:
            logging.error(f"KEGG pathway search failed: {e}")
            results['kegg_pathways'] = []
            errors.append(f"KEGG Pathways: {str(e)}")
    
    # Search KEGG Genes
    if 'kegg_genes' in sources:
        try:
            kegg_client = KEGGClient()
            gene_results = kegg_client.search_genes(search_term, organism_code="hsa", max_results=limit_per_source)
            results['kegg_genes'] = gene_results  # List of dicts
            summaries.append(f"**KEGG Genes:** Found {len(gene_results)} genes")
        except Exception as e:
            logging.error(f"KEGG gene search failed: {e}")
            results['kegg_genes'] = []
            errors.append(f"KEGG Genes: {str(e)}")
    
    # Search Gene Ontology
    if 'gene_ontology' in sources:
        try:
            df, summary = search_go_terms(
                query=search_term,
                limit=limit_per_source
            )
            results['gene_ontology'] = df
            summaries.append(f"**Gene Ontology:** Found {len(df)} GO terms")
        except Exception as e:
            logging.error(f"Gene Ontology search failed: {e}")
            results['gene_ontology'] = pd.DataFrame()
            errors.append(f"Gene Ontology: {str(e)}")
    
    # Search Human Protein Atlas
    if 'proteinatlas' in sources:
        try:
            # Use cancer marker search
            df = search_cancer_markers(cancer=search_term, max_results=limit_per_source)
            results['proteinatlas'] = df
            summaries.append(f"**Human Protein Atlas:** Found {len(df)} proteins")
        except Exception as e:
            logging.error(f"Human Protein Atlas search failed: {e}")
            results['proteinatlas'] = pd.DataFrame()
            errors.append(f"Human Protein Atlas: {str(e)}")
    
    # Build formatted output string
    output = "# Unified Biological Target Search Results\n\n"
    output += f"## Search Term: '{search_term}'\n"
    if search_type:
        output += f"**Search Type:** {search_type}\n"
    output += "\n"
    
    # Count total results
    total_results = 0
    for key, val in results.items():
        if isinstance(val, pd.DataFrame):
            total_results += len(val)
        elif isinstance(val, list):
            total_results += len(val)
    
    output += f"**Total results:** {total_results} across {len([s for s in sources if s in results])} sources\n\n"
    output += "### Results by Source:\n"
    for s in summaries:
        output += f"- {s}\n"
    
    if errors:
        output += "\n### Errors:\n"
        for e in errors:
            output += f"- ⚠️ {e}\n"
    
    output += "\n" + "="*80 + "\n\n"
    
    # Format results from each source
    for source_name, source_data in results.items():
        if isinstance(source_data, pd.DataFrame) and source_data.empty:
            continue
        elif isinstance(source_data, list) and not source_data:
            continue
        
        output += f"\n## {source_name.upper().replace('_', ' ')} Results\n\n"
        
        if source_name == 'opentargets':
            output += f"Found {len(source_data)} therapeutic targets from Open Targets:\n\n"
            for idx, row in source_data.iterrows():
                output += f"**{idx + 1}. {row.get('name', 'N/A')}**\n"
                if pd.notna(row.get('id')):
                    output += f"  - Target ID: {row['id']}\n"
                if pd.notna(row.get('description')):
                    desc = str(row['description'])[:150]
                    output += f"  - Description: {desc}...\n"
                if pd.notna(row.get('entity')):
                    output += f"  - Entity Type: {row['entity']}\n"
                output += "\n"
        
        elif source_name == 'kegg_pathways':
            output += f"Found {len(source_data)} pathways from KEGG:\n\n"
            for idx, pathway in enumerate(source_data, 1):
                pathway_id = pathway.get('id', 'N/A')
                description = pathway.get('description', 'N/A')
                output += f"**{idx}. {pathway_id}** - {description}\n"
                output += "\n"
        
        elif source_name == 'kegg_genes':
            output += f"Found {len(source_data)} genes from KEGG:\n\n"
            for idx, gene in enumerate(source_data, 1):
                gene_id = gene.get('id', 'N/A')
                description = gene.get('description', 'N/A')
                output += f"**{idx}. {gene_id}** - {description}\n"
                output += "\n"
        
        elif source_name == 'gene_ontology':
            output += f"Found {len(source_data)} GO terms from Gene Ontology:\n\n"
            for idx, row in source_data.iterrows():
                output += f"**{idx + 1}. {row.get('name', 'N/A')}** ({row.get('id', 'N/A')})\n"
                if pd.notna(row.get('namespace')):
                    output += f"  - Ontology: {row['namespace']}\n"
                if pd.notna(row.get('definition')):
                    definition = str(row['definition'])[:150]
                    output += f"  - Definition: {definition}...\n"
                output += "\n"
        
        elif source_name == 'proteinatlas':
            output += f"Found {len(source_data)} proteins from Human Protein Atlas:\n\n"
            for idx, row in source_data.iterrows():
                gene = row.get('Gene', 'N/A')
                output += f"**{idx + 1}. {gene}**\n"
                if pd.notna(row.get('Gene name')):
                    output += f"  - Gene Name: {row['Gene name']}\n"
                if pd.notna(row.get('Ensembl')):
                    output += f"  - Ensembl ID: {row['Ensembl']}\n"
                if pd.notna(row.get('Gene description')):
                    desc = str(row['Gene description'])[:150]
                    output += f"  - Description: {desc}...\n"
                if pd.notna(row.get('Protein class')):
                    output += f"  - Protein Class: {row['Protein class']}\n"
                # Add cancer-specific information if available
                if pd.notna(row.get('Prognostic')):
                    output += f"  - Prognostic: {row['Prognostic']}\n"
                if pd.notna(row.get('Cancer')):
                    output += f"  - Cancer: {row['Cancer']}\n"
                output += "\n"
    
    # Aggregate information
    output += "\n" + "="*80 + "\n"
    output += "\n## Aggregated Information\n\n"
    
    # Aggregate target/gene names
    all_names = aggregate_target_names(results)
    if all_names:
        output += f"**All Target/Gene Names Found ({len(all_names)}):**\n"
        for name in all_names[:20]:
            output += f"  - {name}\n"
        if len(all_names) > 20:
            output += f"  ... and {len(all_names) - 20} more\n"
        output += "\n"
    
    # Aggregate identifiers
    all_ids = aggregate_target_identifiers(results)
    if all_ids:
        output += "**Cross-Database Identifiers:**\n"
        for id_type, id_list in all_ids.items():
            if id_list:
                output += f"  - {id_type.upper()}: {', '.join(str(x) for x in id_list[:5])}\n"
        output += "\n"
    
    # Save results if requested
    if save_path:
        try:
            import json
            save_data = {
                'search_term': search_term,
                'search_type': search_type,
                'sources': sources,
                'results': {}
            }
            for source, data in results.items():
                if isinstance(data, pd.DataFrame):
                    save_data['results'][source] = data.to_dict('records')
                elif isinstance(data, list):
                    save_data['results'][source] = data
            
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            output += f"\n**Results saved to:** {save_path}\n"
        except Exception as e:
            logging.error(f"Error saving results: {e}")
            output += f"\n⚠️ **Error saving results:** {e}\n"
    
    return results, output


# ================================================
# Unified Fetch Function
# ================================================

def fetch_target_details_unified(
    target_id: str,
    id_type: Optional[str] = None,
    sources: Optional[List[str]] = None,
    include_associations: bool = True,
    save_path: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Fetch detailed target information using any identifier.
    
    This function automatically detects the ID type (if not specified) and
    queries relevant databases to fetch comprehensive target information including
    associated diseases, pathways, GO annotations, and more.
    
    Args:
        target_id: Target identifier (Ensembl ID, gene symbol, pathway ID, GO ID, etc.)
        id_type: Type of ID. If None, will attempt to detect.
                 Options: 'ensembl', 'gene_symbol', 'pathway', 'go_term'
        sources: List of sources to fetch from. If None, fetches from all relevant.
                 Options: ['opentargets', 'kegg', 'gene_ontology', 'proteinatlas']
        include_associations: Whether to include target-disease associations (default: True)
        save_path: Optional path to save results as JSON
    
    Returns:
        Tuple of (dict of target details by source, formatted output string)
        
    Examples:
        >>> # Fetch by Ensembl ID
        >>> details, output = fetch_target_details_unified("ENSG00000139618")
        >>> print(output)  # Prints formatted details
        
        >>> # Fetch pathway details
        >>> details, output = fetch_target_details_unified("hsa04210", id_type='pathway')
        >>> print(output)
    """
    # Auto-detect ID type if not specified
    if id_type is None:
        id_type = _detect_id_type(target_id)
    
    if sources is None:
        if id_type == 'pathway':
            sources = ['kegg']
        elif id_type == 'go_term':
            sources = ['gene_ontology']
        else:
            sources = ['opentargets', 'kegg', 'gene_ontology', 'proteinatlas']
    
    details = {}
    summaries = []
    errors = []
    
    # Fetch from Open Targets
    if 'opentargets' in sources and id_type in ['ensembl', 'gene_symbol']:
        try:
            # If gene_symbol, search first to get Ensembl ID
            ensembl_id = target_id
            if id_type == 'gene_symbol':
                search_df, _ = opentargets_search_targets(query=target_id, size=1)
                if not search_df.empty:
                    ensembl_id = search_df.iloc[0].get('id')
                else:
                    summaries.append(f"**Open Targets:** No target found for gene symbol")
                    ensembl_id = None
            
            if ensembl_id:
                target_details, _ = opentargets_get_target_details(ensembl_id)
                if target_details:
                    details['opentargets'] = {'target': target_details}
                    summaries.append(f"**Open Targets:** Found target information")
                    
                    # Get associated diseases if requested
                    if include_associations:
                        try:
                            disease_df, _ = get_target_associated_diseases(ensembl_id, size=10)
                            details['opentargets']['associated_diseases'] = disease_df
                        except Exception as e:
                            logging.error(f"Error fetching target associations: {e}")
                else:
                    summaries.append(f"**Open Targets:** No target found")
        except Exception as e:
            logging.error(f"Open Targets fetch failed: {e}")
            errors.append(f"Open Targets: {str(e)}")
    
    # Fetch from KEGG
    if 'kegg' in sources:
        try:
            kegg_client = KEGGClient()
            
            if id_type == 'pathway':
                # Fetch pathway details
                pathway_info = kegg_client.get_pathway_info(target_id)
                details['kegg_pathway'] = pathway_info
                
                # Get pathway genes
                try:
                    pathway_genes = kegg_client.get_pathway_genes(target_id)
                    details['kegg_pathway']['genes'] = pathway_genes
                except Exception as e:
                    logging.error(f"Error fetching pathway genes: {e}")
                
                summaries.append(f"**KEGG Pathway:** Found pathway information")
                
            elif id_type in ['ensembl', 'gene_symbol']:
                # Search for gene and fetch details
                gene_results = kegg_client.search_genes(target_id, organism_code="hsa", max_results=1)
                if gene_results:
                    gene_id = gene_results[0]['id']
                    gene_info = kegg_client.get_gene_info(gene_id)
                    details['kegg_gene'] = gene_info
                    summaries.append(f"**KEGG Gene:** Found gene information")
                else:
                    summaries.append(f"**KEGG Gene:** No gene found")
        except Exception as e:
            logging.error(f"KEGG fetch failed: {e}")
            errors.append(f"KEGG: {str(e)}")
    
    # Fetch from Gene Ontology
    if 'gene_ontology' in sources and id_type == 'go_term':
        try:
            go_details, _ = get_go_term_details(target_id)
            if go_details:
                details['gene_ontology'] = go_details
                summaries.append(f"**Gene Ontology:** Found GO term information")
            else:
                summaries.append(f"**Gene Ontology:** No GO term found")
        except Exception as e:
            logging.error(f"Gene Ontology fetch failed: {e}")
            errors.append(f"Gene Ontology: {str(e)}")
    
    # Fetch from Human Protein Atlas
    if 'proteinatlas' in sources and id_type in ['ensembl', 'gene_symbol']:
        try:
            # Get protein info by gene symbol
            protein_info = get_protein_info(target_id)
            if protein_info:
                details['proteinatlas'] = {'protein': protein_info}
                summaries.append(f"**Human Protein Atlas:** Found protein information")
                
                # Get pathology data if available
                try:
                    pathology_data = get_pathology_data(target_id)
                    if pathology_data:
                        details['proteinatlas']['pathology'] = pathology_data
                except Exception as e:
                    logging.error(f"Error fetching pathology data: {e}")
            else:
                summaries.append(f"**Human Protein Atlas:** No protein found")
        except Exception as e:
            logging.error(f"Human Protein Atlas fetch failed: {e}")
            errors.append(f"Human Protein Atlas: {str(e)}")
    
    # Build formatted output string
    output = "# Unified Biological Target Details\n\n"
    output += f"## Query: '{target_id}' (Type: {id_type})\n\n"
    
    output += "### Fetch Summary:\n"
    for s in summaries:
        output += f"- {s}\n"
    
    if errors:
        output += "\n### Errors:\n"
        for e in errors:
            output += f"- ⚠️ {e}\n"
    
    output += "\n" + "="*80 + "\n\n"
    
    # Format details from each source
    for source_name, source_data in details.items():
        if not source_data:
            continue
        
        output += f"\n## {source_name.upper().replace('_', ' ')} Details\n\n"
        
        if source_name == 'opentargets':
            target = source_data.get('target', {}).get('data', {}).get('target', {})
            if target:
                output += f"**Target: {target.get('approvedSymbol', 'N/A')}** - {target.get('approvedName', 'N/A')}\n\n"
                output += f"- **Ensembl ID:** {target.get('id', 'N/A')}\n"
                output += f"- **Biotype:** {target.get('biotype', 'N/A')}\n"
                
                # Function
                func_desc = target.get('functionDescriptions', [])
                if func_desc:
                    output += f"\n**Function:** {func_desc[0][:300]}...\n"
                
                # Pathways
                pathways = target.get('pathways', [])
                if pathways:
                    output += f"\n**Associated Pathways ({len(pathways)} total):**\n"
                    for pathway in pathways[:5]:
                        output += f"  - {pathway.get('pathway', 'N/A')} ({pathway.get('pathwayId', 'N/A')})\n"
                
                # Tractability
                tractability = target.get('tractability', [])
                if tractability:
                    output += f"\n**Tractability:**\n"
                    for tract in tractability[:3]:
                        output += f"  - {tract.get('modality', 'N/A')}: {tract.get('label', 'N/A')}\n"
                
                output += "\n"
            
            # Associated diseases
            if 'associated_diseases' in source_data:
                disease_df = source_data['associated_diseases']
                if not disease_df.empty:
                    output += f"\n**Associated Diseases ({len(disease_df)} found):**\n\n"
                    for idx, row in disease_df.iterrows():
                        if idx >= 5:  # Limit to first 5
                            output += f"  ... and {len(disease_df) - 5} more diseases\n"
                            break
                        output += f"{idx + 1}. {row.get('disease_name', 'N/A')} (Score: {row.get('score', 0):.3f})\n"
                    output += "\n"
        
        elif source_name == 'kegg_pathway':
            output += f"**KEGG Pathway Information**\n\n"
            for key, value in source_data.items():
                if key == 'genes':
                    output += f"\n**Associated Genes ({len(value)} total):**\n"
                    for gene in value[:10]:
                        output += f"  - {gene.get('target', 'N/A')}: {gene.get('source', 'N/A')}\n"
                elif key == 'ENTRY':
                    output += f"- **Entry:** {value}\n"
                elif key == 'NAME':
                    output += f"- **Name:** {value}\n"
                elif key == 'DESCRIPTION':
                    output += f"- **Description:** {value}\n"
                elif key == 'CLASS':
                    output += f"- **Class:** {value}\n"
                elif key == 'PATHWAY_MAP':
                    output += f"- **Pathway Map:** {value}\n"
            output += "\n"
        
        elif source_name == 'kegg_gene':
            output += f"**KEGG Gene Information**\n\n"
            for key, value in source_data.items():
                if key == 'ENTRY':
                    output += f"- **Entry:** {value}\n"
                elif key == 'NAME':
                    output += f"- **Name:** {value}\n"
                elif key == 'DEFINITION':
                    output += f"- **Definition:** {value}\n"
                elif key == 'PATHWAY':
                    pathway_text = value[:300] if len(value) > 300 else value
                    output += f"- **Pathways:** {pathway_text}...\n"
                elif key == 'MODULE':
                    module_text = value[:200] if len(value) > 200 else value
                    output += f"- **Modules:** {module_text}...\n"
                elif key == 'DISEASE':
                    disease_text = value[:300] if len(value) > 300 else value
                    output += f"- **Associated Diseases:** {disease_text}...\n"
            output += "\n"
        
        elif source_name == 'gene_ontology':
            output += f"**GO Term: {source_data.get('name', 'N/A')}** ({source_data.get('id', 'N/A')})\n\n"
            
            aspect = source_data.get('aspect', '')
            namespace = (
                'molecular_function' if aspect == 'F' else
                'biological_process' if aspect == 'P' else
                'cellular_component' if aspect == 'C' else
                'unknown'
            )
            output += f"- **Ontology:** {namespace}\n"
            
            definition = source_data.get('definition', {})
            if isinstance(definition, dict):
                def_text = definition.get('text', 'No definition available')
            else:
                def_text = str(definition) if definition else 'No definition available'
            output += f"- **Definition:** {def_text}\n"
            
            # Synonyms
            synonyms = source_data.get('synonyms', [])
            if synonyms:
                output += f"\n**Synonyms ({len(synonyms)} total):**\n"
                for syn in synonyms[:5]:
                    syn_name = syn.get('name', syn) if isinstance(syn, dict) else syn
                    output += f"  - {syn_name}\n"
            
            output += "\n"
        
        elif source_name == 'proteinatlas':
            protein = source_data.get('protein', {})
            if protein:
                output += f"**Protein: {protein.get('Gene', 'N/A')}** - {protein.get('Gene name', 'N/A')}\n\n"
                
                # Basic information
                if protein.get('Ensembl'):
                    output += f"- **Ensembl ID:** {protein.get('Ensembl')}\n"
                if protein.get('Uniprot'):
                    output += f"- **UniProt ID:** {protein.get('Uniprot')}\n"
                if protein.get('Protein class'):
                    output += f"- **Protein Class:** {protein.get('Protein class')}\n"
                if protein.get('Gene description'):
                    desc = str(protein.get('Gene description'))[:300]
                    output += f"- **Description:** {desc}...\n"
                
                # Subcellular location
                if protein.get('Subcellular location'):
                    output += f"\n**Subcellular Location:** {protein.get('Subcellular location')}\n"
                
                # RNA tissue specificity
                if protein.get('RNA tissue specificity'):
                    output += f"\n**RNA Tissue Specificity:** {protein.get('RNA tissue specificity')}\n"
                
                output += "\n"
            
            # Pathology information
            if 'pathology' in source_data:
                pathology = source_data['pathology']
                output += f"**Pathology Information**\n\n"
                
                # Cancer information
                if pathology.get('Cancer'):
                    output += f"- **Cancer:** {pathology.get('Cancer')}\n"
                if pathology.get('Prognostic'):
                    output += f"- **Prognostic:** {pathology.get('Prognostic')}\n"
                if pathology.get('Cancer type'):
                    output += f"- **Cancer Type:** {pathology.get('Cancer type')}\n"
                
                output += "\n"
    
    # Save results if requested
    if save_path:
        try:
            import json
            save_data = {
                'target_id': target_id,
                'id_type': id_type,
                'sources': sources,
                'details': {}
            }
            for source, data in details.items():
                if isinstance(data, pd.DataFrame):
                    save_data['details'][source] = data.to_dict('records')
                elif isinstance(data, dict):
                    # Convert any DataFrames in the dict to records
                    converted = {}
                    for k, v in data.items():
                        if isinstance(v, pd.DataFrame):
                            converted[k] = v.to_dict('records')
                        else:
                            converted[k] = v
                    save_data['details'][source] = converted
            
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

def _detect_id_type(target_id: str) -> str:
    """
    Detect the type of target identifier.
    
    Args:
        target_id: Target identifier string
    
    Returns:
        Detected ID type: 'ensembl', 'gene_symbol', 'pathway', 'go_term'
    """
    target_id = target_id.strip()
    
    # Ensembl ID: ENSG format
    if target_id.upper().startswith('ENSG'):
        return 'ensembl'
    
    # GO Term: GO:0000000 format
    if target_id.upper().startswith('GO:') or (target_id.startswith('GO') and ':' in target_id):
        return 'go_term'
    
    # KEGG Pathway: organism code + 5 digits (e.g., hsa00010, map00010)
    if len(target_id) >= 8 and target_id[:3].islower() and target_id[3:].isdigit():
        return 'pathway'
    
    # Default to gene symbol
    return 'gene_symbol'


def aggregate_target_names(results: Dict[str, Any]) -> List[str]:
    """
    Aggregate all unique target/gene names from search results.
    
    Args:
        results: Dictionary of results from different sources
    
    Returns:
        List of unique target/gene names
    """
    names = set()
    
    # From Open Targets DataFrame
    if 'opentargets' in results and isinstance(results['opentargets'], pd.DataFrame):
        df = results['opentargets']
        if 'name' in df.columns:
            names.update(df['name'].dropna().astype(str).tolist())
    
    # From KEGG pathways
    if 'kegg_pathways' in results and isinstance(results['kegg_pathways'], list):
        for pathway in results['kegg_pathways']:
            if 'description' in pathway:
                # Extract pathway name from description
                desc = pathway['description'].split(';')[0].strip()
                if desc:
                    names.add(desc)
    
    # From KEGG genes
    if 'kegg_genes' in results and isinstance(results['kegg_genes'], list):
        for gene in results['kegg_genes']:
            if 'description' in gene:
                # Extract gene name from description
                desc = gene['description'].split(';')[0].strip()
                if desc:
                    names.add(desc)
    
    # From Gene Ontology DataFrame
    if 'gene_ontology' in results and isinstance(results['gene_ontology'], pd.DataFrame):
        df = results['gene_ontology']
        if 'name' in df.columns:
            names.update(df['name'].dropna().astype(str).tolist())
    
    # From Human Protein Atlas DataFrame
    if 'proteinatlas' in results and isinstance(results['proteinatlas'], pd.DataFrame):
        df = results['proteinatlas']
        if 'Gene' in df.columns:
            names.update(df['Gene'].dropna().astype(str).tolist())
        if 'Gene name' in df.columns:
            names.update(df['Gene name'].dropna().astype(str).tolist())
    
    return sorted(list(names))


def aggregate_target_identifiers(results: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Aggregate all cross-database identifiers from search results.
    
    Args:
        results: Dictionary of results from different sources
    
    Returns:
        Dictionary mapping identifier types to lists of IDs
    """
    identifiers = {
        'ensembl': [],
        'kegg_pathway': [],
        'kegg_gene': [],
        'go_term': [],
        'uniprot': []
    }
    
    # From Open Targets DataFrame
    if 'opentargets' in results and isinstance(results['opentargets'], pd.DataFrame):
        df = results['opentargets']
        if 'id' in df.columns:
            identifiers['ensembl'].extend(df['id'].dropna().astype(str).tolist())
    
    # From KEGG pathways
    if 'kegg_pathways' in results and isinstance(results['kegg_pathways'], list):
        for pathway in results['kegg_pathways']:
            if 'id' in pathway:
                identifiers['kegg_pathway'].append(pathway['id'])
    
    # From KEGG genes
    if 'kegg_genes' in results and isinstance(results['kegg_genes'], list):
        for gene in results['kegg_genes']:
            if 'id' in gene:
                identifiers['kegg_gene'].append(gene['id'])
    
    # From Gene Ontology DataFrame
    if 'gene_ontology' in results and isinstance(results['gene_ontology'], pd.DataFrame):
        df = results['gene_ontology']
        if 'id' in df.columns:
            identifiers['go_term'].extend(df['id'].dropna().astype(str).tolist())
    
    # From Human Protein Atlas DataFrame
    if 'proteinatlas' in results and isinstance(results['proteinatlas'], pd.DataFrame):
        df = results['proteinatlas']
        if 'Ensembl' in df.columns:
            identifiers['ensembl'].extend(df['Ensembl'].dropna().astype(str).tolist())
        if 'Uniprot' in df.columns:
            identifiers['uniprot'].extend(df['Uniprot'].dropna().astype(str).tolist())
    
    # Remove duplicates and empty lists
    for key in identifiers:
        identifiers[key] = sorted(list(set(identifiers[key])))
    
    # Remove empty identifier types
    identifiers = {k: v for k, v in identifiers.items() if v}
    
    return identifiers

