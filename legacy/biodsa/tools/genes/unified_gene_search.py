"""Unified gene search and retrieval across multiple APIs.

This module aggregates gene and variant information from:
- BioThings (MyGene.info) - Gene information
- BioThings (MyVariant.info) - Variant information
- KEGG - Gene and orthology information
- Open Targets - Therapeutic target information
"""

import logging
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import individual API modules
from biodsa.tools.biothings.genes import search_genes as biothings_search_genes, fetch_gene_details_by_ids
from biodsa.tools.biothings.variants import search_variants as biothings_search_variants
from biodsa.tools.kegg.client import KEGGClient
from biodsa.tools.opentargets.target_tools import search_targets as opentargets_search_targets, get_target_details

# ================================================
# Unified Search Function
# ================================================

def search_genes_unified(
    search_term: str,
    limit_per_source: int = 10,
    sources: Optional[List[str]] = None,
    include_variants: bool = False,
    save_path: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Search for genes across multiple databases with a simple search term.
    
    This function queries multiple gene databases in parallel and aggregates
    the results, providing a comprehensive view of gene information.
    
    Args:
        search_term: Simple search term (gene symbol, name, etc.)
        limit_per_source: Maximum results per source (default: 10)
        sources: List of sources to search. If None, searches all.
                 Options: ['biothings', 'kegg', 'variants', 'opentargets']
        include_variants: Whether to search for variants associated with genes (default: False)
        save_path: Optional path to save aggregated results
    
    Returns:
        Tuple of (dict of results by source, formatted output string)
        
    Examples:
        >>> # Search for BRCA1 across all sources
        >>> results, output = search_genes_unified("BRCA1", limit_per_source=5)
        >>> print(output)  # Prints formatted results
    """
    if sources is None:
        sources = ['biothings', 'kegg', 'opentargets']
        if include_variants:
            sources.append('variants')
    
    results = {}
    summaries = []
    errors = []
    
    # Search BioThings (MyGene.info)
    if 'biothings' in sources:
        try:
            df, summary = biothings_search_genes(
                search=search_term,
                limit=limit_per_source,
                species="human"
            )
            results['biothings'] = df
            summaries.append(f"**BioThings (MyGene.info):** {summary}")
        except Exception as e:
            logging.error(f"BioThings gene search failed: {e}")
            results['biothings'] = pd.DataFrame()
            errors.append(f"BioThings Genes: {str(e)}")
    
    # Search KEGG Gene Database
    if 'kegg' in sources:
        try:
            kegg_client = KEGGClient()
            kegg_results = kegg_client.search_genes(
                search_term, 
                max_results=limit_per_source
            )
            results['kegg'] = kegg_results  # List of dicts
            summaries.append(f"**KEGG Gene:** Found {len(kegg_results)} genes")
        except Exception as e:
            logging.error(f"KEGG search failed: {e}")
            results['kegg'] = []
            errors.append(f"KEGG: {str(e)}")
    
    # Search Variants if requested
    if 'variants' in sources or include_variants:
        try:
            # Search for variants associated with the gene
            df, summary = biothings_search_variants(
                gene=search_term,
                limit=limit_per_source
            )
            results['variants'] = df
            summaries.append(f"**BioThings (MyVariant.info):** {summary}")
        except Exception as e:
            logging.error(f"BioThings variant search failed: {e}")
            results['variants'] = pd.DataFrame()
            errors.append(f"BioThings Variants: {str(e)}")
    
    # Search Open Targets
    if 'opentargets' in sources:
        try:
            df, summary = opentargets_search_targets(
                query=search_term,
                size=limit_per_source
            )
            results['opentargets'] = df
            summaries.append(f"**Open Targets:** Found {len(df)} targets")
        except Exception as e:
            logging.error(f"Open Targets search failed: {e}")
            results['opentargets'] = pd.DataFrame()
            errors.append(f"Open Targets: {str(e)}")
    
    # Build formatted output string
    output = "# Unified Gene Search Results\n\n"
    output += f"## Search Term: '{search_term}'\n\n"
    
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
        
        output += f"\n## {source_name.upper()} Results\n\n"
        
        if source_name == 'biothings':
            output += f"Found {len(source_data)} genes from BioThings (MyGene.info):\n\n"
            for idx, row in source_data.iterrows():
                output += f"**{idx + 1}. {row.get('symbol', 'N/A')}** - {row.get('name', 'N/A')}\n"
                if pd.notna(row.get('gene_id')):
                    output += f"  - Gene ID: {row['gene_id']}\n"
                if pd.notna(row.get('entrezgene')):
                    output += f"  - Entrez: {row['entrezgene']}\n"
                if pd.notna(row.get('type_of_gene')):
                    output += f"  - Type: {row['type_of_gene']}\n"
                if pd.notna(row.get('summary')) and row.get('summary'):
                    summary_text = str(row['summary'])[:200]
                    output += f"  - Summary: {summary_text}...\n"
                if pd.notna(row.get('alias')) and row.get('alias'):
                    aliases = str(row['alias'])[:100]
                    output += f"  - Aliases: {aliases}...\n"
                output += "\n"
        
        elif source_name == 'kegg':
            output += f"Found {len(source_data)} genes from KEGG:\n\n"
            for idx, gene in enumerate(source_data, 1):
                gene_id = gene.get('id', 'N/A')
                description = gene.get('description', 'N/A')
                output += f"**{idx}. {gene_id}** - {description}\n"
                output += "\n"
        
        elif source_name == 'variants':
            output += f"Found {len(source_data)} variants from BioThings (MyVariant.info):\n\n"
            for idx, row in source_data.iterrows():
                output += f"**{idx + 1}. {row.get('variant_id', 'N/A')}**\n"
                if pd.notna(row.get('rsid')):
                    output += f"  - rsID: {row['rsid']}\n"
                if pd.notna(row.get('chrom')) and pd.notna(row.get('pos')):
                    output += f"  - Position: chr{row['chrom']}:{row['pos']}\n"
                if pd.notna(row.get('ref')) and pd.notna(row.get('alt')):
                    output += f"  - Change: {row['ref']} → {row['alt']}\n"
                if pd.notna(row.get('gene_symbol')):
                    output += f"  - Gene: {row['gene_symbol']}\n"
                if pd.notna(row.get('variant_type')):
                    output += f"  - Type: {row['variant_type']}\n"
                if pd.notna(row.get('clinical_significance')):
                    output += f"  - Clinical Significance: {row['clinical_significance']}\n"
                output += "\n"
        
        elif source_name == 'opentargets':
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
    
    # Aggregate information
    output += "\n" + "="*80 + "\n"
    output += "\n## Aggregated Information\n\n"
    
    all_symbols = aggregate_gene_symbols(results)
    if all_symbols:
        output += f"**All Gene Symbols Found ({len(all_symbols)}):**\n"
        for symbol in all_symbols[:20]:
            output += f"  - {symbol}\n"
        if len(all_symbols) > 20:
            output += f"  ... and {len(all_symbols) - 20} more\n"
        output += "\n"
    
    all_ids = aggregate_gene_identifiers(results)
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

def fetch_gene_details_unified(
    gene_id: str,
    id_type: Optional[str] = None,
    sources: Optional[List[str]] = None,
    include_variants: bool = False,
    save_path: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Fetch detailed gene information using any gene identifier.
    
    This function automatically detects the ID type (if not specified) and
    queries relevant databases to fetch comprehensive gene information.
    
    Args:
        gene_id: Gene identifier (Gene symbol, Entrez ID, Ensembl ID, 
                 KEGG ID, or gene name)
        id_type: Type of ID. If None, will attempt to detect.
                 Options: 'symbol', 'entrez', 'ensembl', 'kegg', 'name'
        sources: List of sources to fetch from. If None, fetches from all relevant.
                 Options: ['biothings', 'kegg', 'variants', 'opentargets']
        include_variants: Whether to fetch variants associated with the gene (default: False)
        save_path: Optional path to save results as JSON
    
    Returns:
        Tuple of (dict of gene details by source, formatted output string)
        
    Examples:
        >>> # Fetch by gene symbol
        >>> details, output = fetch_gene_details_unified("BRCA1")
        >>> print(output)  # Prints formatted details
        
        >>> # Fetch by KEGG ID
        >>> details, output = fetch_gene_details_unified("hsa:672", id_type='kegg')
        >>> print(output)
    """
    # Auto-detect ID type if not specified
    if id_type is None:
        id_type = _detect_id_type(gene_id)
    
    if sources is None:
        sources = ['biothings', 'kegg', 'opentargets']
        if include_variants:
            sources.append('variants')
    
    details = {}
    summaries = []
    errors = []
    
    # Fetch from BioThings
    if 'biothings' in sources:
        try:
            if id_type == 'symbol' or id_type == 'name':
                # Search first, then fetch details
                df, _ = biothings_search_genes(search=gene_id, limit=1, species="human")
                if not df.empty:
                    gene_ids = df['gene_id'].tolist()
                    details_df, _ = fetch_gene_details_by_ids(gene_ids)
                    details['biothings'] = details_df
                    summaries.append(f"**BioThings:** Found gene by {id_type}")
                else:
                    summaries.append(f"**BioThings:** No results found")
            elif id_type == 'entrez':
                df, _ = biothings_search_genes(entrezgene=gene_id, limit=1, species="human")
                if not df.empty:
                    gene_ids = df['gene_id'].tolist()
                    details_df, _ = fetch_gene_details_by_ids(gene_ids)
                    details['biothings'] = details_df
                    summaries.append(f"**BioThings:** Found gene by Entrez ID")
                else:
                    summaries.append(f"**BioThings:** No results found")
            elif id_type == 'ensembl':
                df, _ = biothings_search_genes(ensembl_gene=gene_id, limit=1, species="human")
                if not df.empty:
                    gene_ids = df['gene_id'].tolist()
                    details_df, _ = fetch_gene_details_by_ids(gene_ids)
                    details['biothings'] = details_df
                    summaries.append(f"**BioThings:** Found gene by Ensembl ID")
                else:
                    summaries.append(f"**BioThings:** No results found")
            else:
                # Try direct ID fetch
                details_df, _ = fetch_gene_details_by_ids([gene_id])
                if not details_df.empty:
                    details['biothings'] = details_df
                    summaries.append(f"**BioThings:** Found gene information")
                else:
                    summaries.append(f"**BioThings:** No results found")
        except Exception as e:
            logging.error(f"BioThings fetch failed: {e}")
            errors.append(f"BioThings: {str(e)}")
    
    # Fetch from KEGG
    if 'kegg' in sources:
        try:
            kegg_client = KEGGClient()
            
            if id_type == 'kegg':
                # Direct fetch by KEGG gene ID
                gene_info = kegg_client.get_gene_info(gene_id)
                details['kegg'] = gene_info
                summaries.append(f"**KEGG:** Found gene information")
            elif id_type in ['symbol', 'name']:
                # Search first, then fetch
                search_results = kegg_client.search_genes(gene_id, max_results=1)
                if search_results:
                    kegg_id = search_results[0]['id']
                    gene_info = kegg_client.get_gene_info(kegg_id)
                    details['kegg'] = gene_info
                    summaries.append(f"**KEGG:** Found gene information")
                else:
                    summaries.append(f"**KEGG:** No results found")
            else:
                summaries.append(f"**KEGG:** ID type '{id_type}' not directly searchable in KEGG")
        except Exception as e:
            logging.error(f"KEGG fetch failed: {e}")
            errors.append(f"KEGG: {str(e)}")
    
    # Fetch variants if requested
    if 'variants' in sources or include_variants:
        try:
            # Get gene symbol for variant search
            gene_symbol = gene_id if id_type in ['symbol', 'name'] else None
            
            # If we fetched from BioThings, extract the symbol
            if not gene_symbol and 'biothings' in details:
                biothings_data = details['biothings']
                if isinstance(biothings_data, pd.DataFrame) and not biothings_data.empty:
                    gene_symbol = biothings_data.iloc[0].get('symbol')
            
            if gene_symbol:
                df, summary = biothings_search_variants(
                    gene=gene_symbol,
                    limit=10
                )
                details['variants'] = df
                summaries.append(f"**BioThings (Variants):** {summary}")
            else:
                summaries.append(f"**BioThings (Variants):** Could not determine gene symbol for variant search")
        except Exception as e:
            logging.error(f"BioThings variant fetch failed: {e}")
            errors.append(f"BioThings Variants: {str(e)}")
    
    # Fetch from Open Targets
    if 'opentargets' in sources:
        try:
            # Get Ensembl ID for Open Targets fetch
            ensembl_id = gene_id if id_type == 'ensembl' else None
            
            # If we fetched from BioThings, extract the Ensembl ID
            if not ensembl_id and 'biothings' in details:
                biothings_data = details['biothings']
                if isinstance(biothings_data, pd.DataFrame) and not biothings_data.empty:
                    ensembl_info = biothings_data.iloc[0].get('ensembl')
                    if isinstance(ensembl_info, dict) and 'gene' in ensembl_info:
                        ensembl_id = ensembl_info['gene']
            
            if ensembl_id:
                target_details, target_summary = get_target_details(ensembl_id)
                if target_details:
                    details['opentargets'] = target_details
                    summaries.append(f"**Open Targets:** Found target information")
                else:
                    summaries.append(f"**Open Targets:** No target found for Ensembl ID")
            else:
                summaries.append(f"**Open Targets:** Could not determine Ensembl ID for target fetch")
        except Exception as e:
            logging.error(f"Open Targets fetch failed: {e}")
            errors.append(f"Open Targets: {str(e)}")
    
    # Build formatted output string
    output = "# Unified Gene Details\n\n"
    output += f"## Query: '{gene_id}' (Type: {id_type})\n\n"
    
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
        if isinstance(source_data, pd.DataFrame) and source_data.empty:
            continue
        elif isinstance(source_data, dict) and not source_data:
            continue
        elif source_data is None:
            continue
        
        output += f"\n## {source_name.upper()} Details\n\n"
        
        if source_name == 'biothings' and isinstance(source_data, pd.DataFrame):
            for idx, row in source_data.iterrows():
                output += f"**Gene: {row.get('symbol', 'N/A')}** - {row.get('name', 'N/A')}\n\n"
                if pd.notna(row.get('gene_id')):
                    output += f"- **Gene ID:** {row['gene_id']}\n"
                if pd.notna(row.get('entrezgene')):
                    output += f"- **Entrez ID:** {row['entrezgene']}\n"
                if pd.notna(row.get('type_of_gene')):
                    output += f"- **Type:** {row['type_of_gene']}\n"
                if pd.notna(row.get('summary')):
                    output += f"- **Summary:** {row['summary']}\n"
                if pd.notna(row.get('alias')) and row.get('alias'):
                    output += f"- **Aliases:** {row['alias']}\n"
                if pd.notna(row.get('ensembl')):
                    output += f"- **Ensembl:** {str(row['ensembl'])[:200]}...\n"
                if pd.notna(row.get('refseq')):
                    output += f"- **RefSeq:** {str(row['refseq'])[:200]}...\n"
                output += "\n"
        
        elif source_name == 'kegg' and isinstance(source_data, dict):
            output += f"**KEGG Gene Information**\n\n"
            for key, value in source_data.items():
                if key == 'ENTRY':
                    output += f"- **Entry:** {value}\n"
                elif key == 'NAME':
                    output += f"- **Name:** {value}\n"
                elif key == 'SYMBOL':
                    output += f"- **Symbol:** {value}\n"
                elif key == 'DEFINITION':
                    output += f"- **Definition:** {value}\n"
                elif key == 'ORTHOLOGY':
                    orthology_text = value[:300] if len(value) > 300 else value
                    output += f"- **Orthology:** {orthology_text}...\n"
                elif key == 'PATHWAY':
                    pathway_text = value[:300] if len(value) > 300 else value
                    output += f"- **Pathways:** {pathway_text}...\n"
                elif key == 'DISEASE':
                    disease_text = value[:300] if len(value) > 300 else value
                    output += f"- **Associated Diseases:** {disease_text}...\n"
                elif key == 'MODULE':
                    module_text = value[:200] if len(value) > 200 else value
                    output += f"- **Modules:** {module_text}...\n"
                elif key == 'BRITE':
                    brite_text = value[:200] if len(value) > 200 else value
                    output += f"- **BRITE:** {brite_text}...\n"
            output += "\n"
        
        elif source_name == 'variants' and isinstance(source_data, pd.DataFrame):
            output += f"**Associated Variants ({len(source_data)} found)**\n\n"
            for idx, row in source_data.iterrows():
                if idx >= 5:  # Limit to first 5 variants in output
                    output += f"... and {len(source_data) - 5} more variants\n"
                    break
                output += f"**{idx + 1}. {row.get('variant_id', 'N/A')}**\n"
                if pd.notna(row.get('rsid')):
                    output += f"  - rsID: {row['rsid']}\n"
                if pd.notna(row.get('chrom')) and pd.notna(row.get('pos')):
                    output += f"  - Position: chr{row['chrom']}:{row['pos']}\n"
                if pd.notna(row.get('clinical_significance')):
                    output += f"  - Clinical Significance: {row['clinical_significance']}\n"
                output += "\n"
        
        elif source_name == 'opentargets' and isinstance(source_data, dict):
            target = source_data.get('data', {}).get('target', {})
            if target:
                output += f"**Open Targets Target Information**\n\n"
                output += f"- **Symbol:** {target.get('approvedSymbol', 'N/A')}\n"
                output += f"- **Name:** {target.get('approvedName', 'N/A')}\n"
                output += f"- **Ensembl ID:** {target.get('id', 'N/A')}\n"
                output += f"- **Biotype:** {target.get('biotype', 'N/A')}\n"
                
                # Function descriptions
                func_desc = target.get('functionDescriptions', [])
                if func_desc:
                    output += f"- **Function:** {func_desc[0][:200]}...\n"
                
                # Pathways
                pathways = target.get('pathways', [])
                if pathways:
                    output += f"- **Pathways ({len(pathways)} total):**\n"
                    for pathway in pathways[:3]:
                        output += f"  - {pathway.get('pathway', 'N/A')}\n"
                
                # Tractability
                tractability = target.get('tractability', [])
                if tractability:
                    output += f"- **Tractability:**\n"
                    for tract in tractability[:3]:
                        output += f"  - {tract.get('modality', 'N/A')}: {tract.get('label', 'N/A')}\n"
                
                output += "\n"
    
    # Aggregate information
    output += "\n" + "="*80 + "\n"
    output += "\n## Aggregated Information\n\n"
    
    all_symbols = aggregate_gene_symbols(details)
    if all_symbols:
        output += f"**Gene Symbols:**\n"
        for symbol in all_symbols[:10]:
            output += f"  - {symbol}\n"
        output += "\n"
    
    all_ids = aggregate_gene_identifiers(details)
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
                'gene_id': gene_id,
                'id_type': id_type,
                'sources': sources,
                'details': {}
            }
            for source, data in details.items():
                if isinstance(data, pd.DataFrame):
                    save_data['details'][source] = data.to_dict('records')
                elif isinstance(data, dict):
                    save_data['details'][source] = data
            
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

def _detect_id_type(gene_id: str) -> str:
    """
    Detect the type of gene identifier.
    
    Args:
        gene_id: Gene identifier string
    
    Returns:
        Detected ID type: 'symbol', 'entrez', 'ensembl', 'kegg', or 'name'
    """
    gene_id = gene_id.strip()
    
    # KEGG Gene ID: organism:gene_id format (e.g., hsa:672, mmu:11651)
    if ':' in gene_id and len(gene_id.split(':')[0]) <= 4:
        return 'kegg'
    
    # Ensembl ID: ENSG format
    if gene_id.upper().startswith('ENSG'):
        return 'ensembl'
    
    # Entrez ID: numeric only
    if gene_id.isdigit():
        return 'entrez'
    
    # Gene symbol: typically uppercase letters, possibly with numbers
    if gene_id.isupper() and len(gene_id) <= 10:
        return 'symbol'
    
    # Default to name search
    return 'name'


def aggregate_gene_symbols(results: Dict[str, Any]) -> List[str]:
    """
    Aggregate all unique gene symbols from search results.
    
    Args:
        results: Dictionary of results from different sources
    
    Returns:
        List of unique gene symbols
    """
    symbols = set()
    
    # From BioThings DataFrame
    if 'biothings' in results and isinstance(results['biothings'], pd.DataFrame):
        df = results['biothings']
        if 'symbol' in df.columns:
            symbols.update(df['symbol'].dropna().astype(str).tolist())
    
    # From KEGG list results
    if 'kegg' in results and isinstance(results['kegg'], list):
        for gene in results['kegg']:
            if 'id' in gene and gene['id']:
                # Extract gene symbol from KEGG ID (e.g., hsa:BRCA1 -> BRCA1)
                gene_id = gene['id']
                if ':' in gene_id:
                    symbol = gene_id.split(':')[1]
                    symbols.add(symbol)
    
    # From Open Targets DataFrame
    if 'opentargets' in results and isinstance(results['opentargets'], pd.DataFrame):
        df = results['opentargets']
        if 'name' in df.columns:
            symbols.update(df['name'].dropna().astype(str).tolist())
    
    # From Open Targets dict (details)
    if 'opentargets' in results and isinstance(results['opentargets'], dict):
        target = results['opentargets'].get('data', {}).get('target', {})
        if target and 'approvedSymbol' in target:
            symbols.add(target['approvedSymbol'])
    
    return sorted(list(symbols))


def aggregate_gene_identifiers(results: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Aggregate all cross-database identifiers from search results.
    
    Args:
        results: Dictionary of results from different sources
    
    Returns:
        Dictionary mapping identifier types to lists of IDs
    """
    identifiers = {
        'entrez': [],
        'ensembl': [],
        'kegg': [],
        'gene_id': [],
        'symbol': []
    }
    
    # From BioThings DataFrame
    if 'biothings' in results and isinstance(results['biothings'], pd.DataFrame):
        df = results['biothings']
        
        if 'gene_id' in df.columns:
            identifiers['gene_id'].extend(df['gene_id'].dropna().astype(str).tolist())
        
        if 'symbol' in df.columns:
            identifiers['symbol'].extend(df['symbol'].dropna().astype(str).tolist())
        
        if 'entrezgene' in df.columns:
            identifiers['entrez'].extend(df['entrezgene'].dropna().astype(str).tolist())
    
    # From KEGG list results
    if 'kegg' in results and isinstance(results['kegg'], list):
        for gene in results['kegg']:
            if 'id' in gene and gene['id']:
                identifiers['kegg'].append(gene['id'])
    
    # From KEGG dict (details)
    if 'kegg' in results and isinstance(results['kegg'], dict):
        if 'ENTRY' in results['kegg']:
            identifiers['kegg'].append(results['kegg']['ENTRY'].split()[0])
    
    # From Open Targets DataFrame
    if 'opentargets' in results and isinstance(results['opentargets'], pd.DataFrame):
        df = results['opentargets']
        if 'id' in df.columns:
            identifiers['ensembl'].extend(df['id'].dropna().astype(str).tolist())
        if 'name' in df.columns:
            identifiers['symbol'].extend(df['name'].dropna().astype(str).tolist())
    
    # From Open Targets dict (details)
    if 'opentargets' in results and isinstance(results['opentargets'], dict):
        target = results['opentargets'].get('data', {}).get('target', {})
        if target:
            if 'id' in target:
                identifiers['ensembl'].append(target['id'])
            if 'approvedSymbol' in target:
                identifiers['symbol'].append(target['approvedSymbol'])
    
    # Remove duplicates and empty lists
    for key in identifiers:
        identifiers[key] = sorted(list(set(identifiers[key])))
    
    # Remove empty identifier types
    identifiers = {k: v for k, v in identifiers.items() if v}
    
    return identifiers
