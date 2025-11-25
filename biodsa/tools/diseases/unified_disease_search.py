"""Unified disease search and retrieval across multiple APIs.

This module aggregates disease information from:
- BioThings (MyDisease.info)
- KEGG Disease Database
- Open Targets Platform
- ChEMBL Database (drug indications and treatments)
"""

import logging
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import individual API modules
from biodsa.tools.biothings.diseases import search_diseases as biothings_search_diseases, fetch_disease_details_by_ids
from biodsa.tools.kegg.client import KEGGClient
from biodsa.tools.opentargets.disease_tools import search_diseases as opentargets_search_diseases, get_disease_details
from biodsa.tools.chembl.drug_tools import search_drugs_by_indication, get_drug_indications

# ================================================
# Unified Search Function
# ================================================

def search_diseases_unified(
    search_term: str,
    limit_per_source: int = 10,
    sources: Optional[List[str]] = None,
    save_path: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Search for diseases across multiple databases with a simple search term.
    
    This function queries multiple disease databases in parallel and aggregates
    the results, providing a comprehensive view of disease information.
    
    Args:
        search_term: Simple search term (disease name, condition, symptoms, etc.)
        limit_per_source: Maximum results per source (default: 10)
        sources: List of sources to search. If None, searches all.
                 Options: ['biothings', 'kegg', 'opentargets', 'chembl_drugs']
        save_path: Optional path to save aggregated results
    
    Returns:
        Tuple of (dict of results by source, formatted output string)
        
    Examples:
        >>> # Search for diabetes across all sources
        >>> results, output = search_diseases_unified("diabetes", limit_per_source=5)
        >>> print(output)  # Prints formatted results
    """
    if sources is None:
        sources = ['biothings', 'kegg', 'opentargets', 'chembl_drugs']
    
    results = {}
    summaries = []
    errors = []
    
    # Search BioThings (MyDisease.info)
    if 'biothings' in sources:
        try:
            df, summary = biothings_search_diseases(
                search=search_term,
                limit=limit_per_source
            )
            results['biothings'] = df
            summaries.append(f"**BioThings (MyDisease.info):** {summary}")
        except Exception as e:
            logging.error(f"BioThings search failed: {e}")
            results['biothings'] = pd.DataFrame()
            errors.append(f"BioThings: {str(e)}")
    
    # Search KEGG Disease Database
    if 'kegg' in sources:
        try:
            kegg_client = KEGGClient()
            kegg_results = kegg_client.search_diseases(search_term, max_results=limit_per_source)
            results['kegg'] = kegg_results  # List of dicts
            summaries.append(f"**KEGG Disease:** Found {len(kegg_results)} diseases")
        except Exception as e:
            logging.error(f"KEGG search failed: {e}")
            results['kegg'] = []
            errors.append(f"KEGG: {str(e)}")
    
    # Search Open Targets
    if 'opentargets' in sources:
        try:
            df, summary = opentargets_search_diseases(
                query=search_term,
                size=limit_per_source
            )
            results['opentargets'] = df
            summaries.append(f"**Open Targets:** Found {len(df)} diseases")
        except Exception as e:
            logging.error(f"Open Targets search failed: {e}")
            results['opentargets'] = pd.DataFrame()
            errors.append(f"Open Targets: {str(e)}")
    
    # Search ChEMBL for drugs treating this disease/indication
    if 'chembl_drugs' in sources:
        try:
            df, summary = search_drugs_by_indication(
                indication=search_term,
                min_phase=0,  # Include all phases
                limit=limit_per_source
            )
            results['chembl_drugs'] = df
            summaries.append(f"**ChEMBL Drugs:** Found {len(df)} drugs for this indication")
        except Exception as e:
            logging.error(f"ChEMBL drugs search failed: {e}")
            results['chembl_drugs'] = pd.DataFrame()
            errors.append(f"ChEMBL Drugs: {str(e)}")
    
    # Build formatted output string
    output = "# Unified Disease Search Results\n\n"
    output += f"## Search Term: '{search_term}'\n\n"
    
    # Count total results
    total_results = 0
    for key, val in results.items():
        if isinstance(val, pd.DataFrame):
            total_results += len(val)
        elif isinstance(val, list):
            total_results += len(val)
    
    output += f"**Total results:** {total_results} across {len(sources)} sources\n\n"
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
            output += f"Found {len(source_data)} diseases from BioThings (MyDisease.info):\n\n"
            for idx, row in source_data.iterrows():
                output += f"**{idx + 1}. {row.get('name', 'N/A')}**\n"
                if pd.notna(row.get('disease_id')):
                    output += f"  - Disease ID: {row['disease_id']}\n"
                if pd.notna(row.get('mondo_id')):
                    output += f"  - MONDO ID: {row['mondo_id']}\n"
                if pd.notna(row.get('doid')):
                    output += f"  - DOID: {row['doid']}\n"
                if pd.notna(row.get('definition')):
                    definition = str(row['definition'])[:200]
                    output += f"  - Definition: {definition}...\n"
                if pd.notna(row.get('synonyms')) and row.get('synonyms'):
                    synonyms = str(row['synonyms'])[:100]
                    output += f"  - Synonyms: {synonyms}...\n"
                output += "\n"
        
        elif source_name == 'kegg':
            output += f"Found {len(source_data)} diseases from KEGG:\n\n"
            for idx, disease in enumerate(source_data, 1):
                disease_id = disease.get('id', 'N/A')
                description = disease.get('description', 'N/A')
                output += f"**{idx}. {disease_id}** - {description}\n"
                output += "\n"
        
        elif source_name == 'opentargets':
            output += f"Found {len(source_data)} diseases from Open Targets:\n\n"
            for idx, row in source_data.iterrows():
                output += f"**{idx + 1}. {row.get('name', 'N/A')}**\n"
                if pd.notna(row.get('id')):
                    output += f"  - EFO ID: {row['id']}\n"
                if pd.notna(row.get('description')):
                    desc = str(row['description'])[:150]
                    output += f"  - Description: {desc}...\n"
                if pd.notna(row.get('entity')):
                    output += f"  - Entity Type: {row['entity']}\n"
                output += "\n"
        
        elif source_name == 'chembl_drugs':
            output += f"Found {len(source_data)} drugs treating this indication from ChEMBL:\n\n"
            phases = ['Preclinical', 'Phase I', 'Phase II', 'Phase III', 'Approved']
            for idx, row in source_data.iterrows():
                drug_id = row.get('molecule_chembl_id', 'N/A')
                indication = row.get('indication', 'N/A')
                output += f"**{idx + 1}. {drug_id}**\n"
                if indication != 'N/A':
                    output += f"  - Indication: {indication}\n"
                if pd.notna(row.get('max_phase_for_ind')):
                    phase = row.get('max_phase_for_ind')
                    try:
                        phase = int(phase)
                        phase_str = phases[phase] if 0 <= phase < len(phases) else str(phase)
                        output += f"  - Development Phase: {phase_str}\n"
                    except (ValueError, TypeError):
                        output += f"  - Development Phase: {phase}\n"
                if pd.notna(row.get('efo_id')):
                    output += f"  - EFO ID: {row['efo_id']}\n"
                output += "\n"
    
    # Aggregate information
    output += "\n" + "="*80 + "\n"
    output += "\n## Aggregated Information\n\n"
    
    all_names = aggregate_disease_names(results)
    if all_names:
        output += f"**All Disease Names Found ({len(all_names)}):**\n"
        for name in all_names[:20]:
            output += f"  - {name}\n"
        if len(all_names) > 20:
            output += f"  ... and {len(all_names) - 20} more\n"
        output += "\n"
    
    all_ids = aggregate_disease_identifiers(results)
    if all_ids:
        output += "**Cross-Database Identifiers:**\n"
        for id_type, id_list in all_ids.items():
            if id_list:
                output += f"  - {id_type.upper()}: {', '.join(id_list[:5])}\n"
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

def fetch_disease_details_unified(
    disease_id: str,
    id_type: Optional[str] = None,
    sources: Optional[List[str]] = None,
    save_path: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Fetch detailed disease information using any disease identifier.
    
    This function automatically detects the ID type (if not specified) and
    queries relevant databases to fetch comprehensive disease information.
    
    Args:
        disease_id: Disease identifier (MONDO ID, DOID, OMIM ID, MeSH ID, 
                    KEGG ID, or disease name)
        id_type: Type of ID. If None, will attempt to detect.
                 Options: 'mondo', 'doid', 'omim', 'mesh', 'kegg', 'efo', 'name'
        sources: List of sources to fetch from. If None, fetches from all relevant.
                 Options: ['biothings', 'kegg', 'opentargets', 'chembl_drugs']
        save_path: Optional path to save results as JSON
    
    Returns:
        Tuple of (dict of disease details by source, formatted output string)
        
    Examples:
        >>> # Fetch by MONDO ID
        >>> details, output = fetch_disease_details_unified("MONDO:0004992")
        >>> print(output)  # Prints formatted details
        
        >>> # Fetch by disease name
        >>> details, output = fetch_disease_details_unified("diabetes mellitus", id_type='name')
        >>> print(output)
    """
    # Auto-detect ID type if not specified
    if id_type is None:
        id_type = _detect_id_type(disease_id)
    
    if sources is None:
        sources = ['biothings', 'kegg', 'opentargets', 'chembl_drugs']
    
    details = {}
    summaries = []
    errors = []
    
    # Fetch from BioThings
    if 'biothings' in sources and id_type in ['mondo', 'doid', 'omim', 'mesh', 'name']:
        try:
            if id_type == 'name':
                # Search first, then fetch details
                df, _ = biothings_search_diseases(search=disease_id, limit=1)
                if not df.empty:
                    disease_ids = df['disease_id'].tolist()
                    details_df, _ = fetch_disease_details_by_ids(disease_ids)
                    details['biothings'] = details_df
                    summaries.append(f"**BioThings:** Found disease by name")
                else:
                    summaries.append(f"**BioThings:** No results found")
            elif id_type == 'mondo':
                df, _ = biothings_search_diseases(mondo_id=disease_id, limit=1)
                if not df.empty:
                    disease_ids = df['disease_id'].tolist()
                    details_df, _ = fetch_disease_details_by_ids(disease_ids)
                    details['biothings'] = details_df
                    summaries.append(f"**BioThings:** Found disease by MONDO ID")
                else:
                    summaries.append(f"**BioThings:** No results found")
            elif id_type == 'doid':
                df, _ = biothings_search_diseases(doid=disease_id, limit=1)
                if not df.empty:
                    disease_ids = df['disease_id'].tolist()
                    details_df, _ = fetch_disease_details_by_ids(disease_ids)
                    details['biothings'] = details_df
                    summaries.append(f"**BioThings:** Found disease by DOID")
                else:
                    summaries.append(f"**BioThings:** No results found")
            elif id_type == 'omim':
                df, _ = biothings_search_diseases(omim_id=disease_id, limit=1)
                if not df.empty:
                    disease_ids = df['disease_id'].tolist()
                    details_df, _ = fetch_disease_details_by_ids(disease_ids)
                    details['biothings'] = details_df
                    summaries.append(f"**BioThings:** Found disease by OMIM ID")
                else:
                    summaries.append(f"**BioThings:** No results found")
            elif id_type == 'mesh':
                df, _ = biothings_search_diseases(mesh_id=disease_id, limit=1)
                if not df.empty:
                    disease_ids = df['disease_id'].tolist()
                    details_df, _ = fetch_disease_details_by_ids(disease_ids)
                    details['biothings'] = details_df
                    summaries.append(f"**BioThings:** Found disease by MeSH ID")
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
                # Direct fetch by KEGG disease ID
                disease_info = kegg_client.get_disease_info(disease_id)
                details['kegg'] = disease_info
                summaries.append(f"**KEGG:** Found disease information")
            elif id_type == 'name':
                # Search first, then fetch
                search_results = kegg_client.search_diseases(disease_id, max_results=1)
                if search_results:
                    kegg_id = search_results[0]['id']
                    disease_info = kegg_client.get_disease_info(kegg_id)
                    details['kegg'] = disease_info
                    summaries.append(f"**KEGG:** Found disease information")
                else:
                    summaries.append(f"**KEGG:** No results found")
            else:
                summaries.append(f"**KEGG:** ID type '{id_type}' not directly searchable in KEGG")
        except Exception as e:
            logging.error(f"KEGG fetch failed: {e}")
            errors.append(f"KEGG: {str(e)}")
    
    # Fetch from Open Targets
    if 'opentargets' in sources:
        try:
            # Get EFO ID for Open Targets fetch
            efo_id = disease_id if id_type == 'efo' else None
            
            # If we fetched from BioThings, try to extract EFO ID from mondo or other mappings
            # For now, use direct EFO ID or search by name
            if not efo_id and id_type == 'name':
                # Search first to get EFO ID
                search_df, _ = opentargets_search_diseases(query=disease_id, size=1)
                if not search_df.empty:
                    efo_id = search_df.iloc[0].get('id')
            
            if efo_id:
                disease_details, disease_summary = get_disease_details(efo_id)
                if disease_details:
                    details['opentargets'] = disease_details
                    summaries.append(f"**Open Targets:** Found disease information")
                else:
                    summaries.append(f"**Open Targets:** No disease found for EFO ID")
            else:
                summaries.append(f"**Open Targets:** Could not determine EFO ID for disease fetch")
        except Exception as e:
            logging.error(f"Open Targets fetch failed: {e}")
            errors.append(f"Open Targets: {str(e)}")
    
    # Fetch drugs from ChEMBL for this disease/indication
    if 'chembl_drugs' in sources:
        try:
            # Use the disease name or ID to search for drugs
            search_term = disease_id if id_type == 'name' else disease_id
            
            # If we have disease name from other sources, use that
            if id_type != 'name' and 'biothings' in details:
                biothings_data = details['biothings']
                if isinstance(biothings_data, pd.DataFrame) and not biothings_data.empty:
                    disease_name = biothings_data.iloc[0].get('name')
                    if disease_name:
                        search_term = disease_name
            
            # Search for drugs treating this disease
            df, _ = search_drugs_by_indication(
                indication=search_term,
                min_phase=0,  # Include all development phases
                limit=50
            )
            
            if not df.empty:
                details['chembl_drugs'] = df
                summaries.append(f"**ChEMBL Drugs:** Found {len(df)} drugs for this indication")
            else:
                summaries.append(f"**ChEMBL Drugs:** No drugs found for this indication")
        except Exception as e:
            logging.error(f"ChEMBL drugs fetch failed: {e}")
            errors.append(f"ChEMBL Drugs: {str(e)}")
    
    # Build formatted output string
    output = "# Unified Disease Details\n\n"
    output += f"## Query: '{disease_id}' (Type: {id_type})\n\n"
    
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
                output += f"**Disease: {row.get('name', 'N/A')}**\n\n"
                if pd.notna(row.get('disease_id')):
                    output += f"- **Disease ID:** {row['disease_id']}\n"
                if pd.notna(row.get('definition')):
                    output += f"- **Definition:** {row['definition']}\n"
                if pd.notna(row.get('synonyms')) and row.get('synonyms'):
                    output += f"- **Synonyms:** {row['synonyms']}\n"
                if pd.notna(row.get('mondo')):
                    output += f"- **MONDO:** {str(row['mondo'])[:300]}...\n"
                if pd.notna(row.get('xrefs')):
                    output += f"- **Cross-references:** {str(row['xrefs'])[:300]}...\n"
                if pd.notna(row.get('phenotypes')):
                    output += f"- **Phenotypes:** {str(row['phenotypes'])[:300]}...\n"
                output += "\n"
        
        elif source_name == 'kegg' and isinstance(source_data, dict):
            output += f"**KEGG Disease Information**\n\n"
            for key, value in source_data.items():
                if key == 'ENTRY':
                    output += f"- **Entry:** {value}\n"
                elif key == 'NAME':
                    output += f"- **Name:** {value}\n"
                elif key == 'DESCRIPTION':
                    output += f"- **Description:** {value}\n"
                elif key == 'CATEGORY':
                    output += f"- **Category:** {value}\n"
                elif key == 'GENE':
                    gene_text = value[:300] if len(value) > 300 else value
                    output += f"- **Associated Genes:** {gene_text}...\n"
                elif key == 'PATHWAY':
                    pathway_text = value[:300] if len(value) > 300 else value
                    output += f"- **Associated Pathways:** {pathway_text}...\n"
                elif key == 'DRUG':
                    drug_text = value[:300] if len(value) > 300 else value
                    output += f"- **Related Drugs:** {drug_text}...\n"
                elif key == 'COMMENT':
                    comment_text = value[:500] if len(value) > 500 else value
                    output += f"- **Comment:** {comment_text}...\n"
            output += "\n"
        
        elif source_name == 'opentargets' and isinstance(source_data, dict):
            disease = source_data.get('data', {}).get('disease', {})
            if disease:
                output += f"**Open Targets Disease Information**\n\n"
                output += f"- **Name:** {disease.get('name', 'N/A')}\n"
                output += f"- **EFO ID:** {disease.get('id', 'N/A')}\n"
                output += f"- **Description:** {disease.get('description', 'N/A')}\n"
                
                # Synonyms
                synonyms = disease.get('synonyms', {})
                if synonyms and synonyms.get('terms'):
                    terms = synonyms.get('terms', [])
                    output += f"\n**Synonyms ({len(terms)} total):**\n"
                    for term in terms[:5]:
                        output += f"  - {term}\n"
                
                # Therapeutic Areas
                therapeutic_areas = disease.get('therapeuticAreas', [])
                if therapeutic_areas:
                    output += f"\n**Therapeutic Areas:**\n"
                    for area in therapeutic_areas[:3]:
                        output += f"  - {area.get('name', 'N/A')} ({area.get('id', 'N/A')})\n"
                
                # Parents
                parents = disease.get('parents', [])
                if parents:
                    output += f"\n**Parent Terms ({len(parents)} total):**\n"
                    for parent in parents[:3]:
                        output += f"  - {parent.get('name', 'N/A')}\n"
                
                # Children
                children = disease.get('children', [])
                if children:
                    output += f"\n**Child Terms ({len(children)} total):**\n"
                    for child in children[:3]:
                        output += f"  - {child.get('name', 'N/A')}\n"
                
                output += "\n"
        
        elif source_name == 'chembl_drugs' and isinstance(source_data, pd.DataFrame):
            output += f"**ChEMBL Drugs Treating This Disease**\n\n"
            output += f"Found {len(source_data)} drugs:\n\n"
            
            phases = ['Preclinical', 'Phase I', 'Phase II', 'Phase III', 'Approved']
            
            for idx, row in source_data.iterrows():
                if idx >= 20:  # Limit to first 20
                    output += f"\n... and {len(source_data) - 20} more drugs\n"
                    break
                
                drug_id = row.get('molecule_chembl_id', 'N/A')
                indication = row.get('indication', 'N/A')
                
                output += f"**{idx + 1}. {drug_id}**\n"
                
                if indication != 'N/A':
                    indication_short = indication[:100] + '...' if len(indication) > 100 else indication
                    output += f"  - Indication: {indication_short}\n"
                
                if pd.notna(row.get('max_phase_for_ind')):
                    phase = row.get('max_phase_for_ind')
                    try:
                        phase = int(phase)
                        phase_str = phases[phase] if 0 <= phase < len(phases) else str(phase)
                        output += f"  - Development Phase: {phase_str}\n"
                    except (ValueError, TypeError):
                        output += f"  - Development Phase: {phase}\n"
                
                if pd.notna(row.get('efo_term')):
                    output += f"  - EFO Term: {row['efo_term']}\n"
                
                if pd.notna(row.get('efo_id')):
                    output += f"  - EFO ID: {row['efo_id']}\n"
                
                output += "\n"
            
            # Summary by phase
            if not source_data.empty and 'max_phase_for_ind' in source_data.columns:
                output += "\n**Summary by Development Phase:**\n"
                phase_counts = {}
                for phase in source_data['max_phase_for_ind'].dropna():
                    try:
                        phase_int = int(phase)
                        phase_str = phases[phase_int] if 0 <= phase_int < len(phases) else str(phase)
                        phase_counts[phase_str] = phase_counts.get(phase_str, 0) + 1
                    except (ValueError, TypeError):
                        pass
                
                for phase_name, count in sorted(phase_counts.items()):
                    output += f"  - {phase_name}: {count} drugs\n"
                
                output += "\n"
    
    # Aggregate information
    output += "\n" + "="*80 + "\n"
    output += "\n## Aggregated Information\n\n"
    
    all_names = aggregate_disease_names(details)
    if all_names:
        output += f"**Disease Names:**\n"
        for name in all_names[:10]:
            output += f"  - {name}\n"
        output += "\n"
    
    all_ids = aggregate_disease_identifiers(details)
    if all_ids:
        output += "**Cross-Database Identifiers:**\n"
        for id_type, id_list in all_ids.items():
            if id_list:
                output += f"  - {id_type.upper()}: {', '.join(id_list[:5])}\n"
        output += "\n"
    
    # Save results if requested
    if save_path:
        try:
            import json
            save_data = {
                'disease_id': disease_id,
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

def _detect_id_type(disease_id: str) -> str:
    """
    Detect the type of disease identifier.
    
    Args:
        disease_id: Disease identifier string
    
    Returns:
        Detected ID type: 'mondo', 'doid', 'omim', 'mesh', 'kegg', 'efo', or 'name'
    """
    disease_id = disease_id.strip()
    
    # MONDO ID: MONDO:0000000
    if disease_id.upper().startswith('MONDO:'):
        return 'mondo'
    
    # EFO ID: EFO:0000000 or EFO_0000000
    if disease_id.upper().startswith('EFO:') or disease_id.upper().startswith('EFO_'):
        return 'efo'
    
    # DOID: DOID:0000000 or just numbers
    if disease_id.upper().startswith('DOID:'):
        return 'doid'
    
    # OMIM ID: usually 6 digits or starts with OMIM:
    if disease_id.upper().startswith('OMIM:') or (disease_id.isdigit() and len(disease_id) == 6):
        return 'omim'
    
    # MeSH ID: usually starts with D, C, or mesh:
    if disease_id.upper().startswith('MESH:') or (disease_id.startswith('D') and len(disease_id) == 7):
        return 'mesh'
    
    # KEGG Disease ID: H00000 format
    if disease_id.startswith('H') and disease_id[1:].isdigit() and len(disease_id) == 6:
        return 'kegg'
    
    # Default to name search
    return 'name'


def aggregate_disease_names(results: Dict[str, Any]) -> List[str]:
    """
    Aggregate all unique disease names from search results.
    
    Args:
        results: Dictionary of results from different sources
    
    Returns:
        List of unique disease names
    """
    names = set()
    
    # From BioThings DataFrame
    if 'biothings' in results and isinstance(results['biothings'], pd.DataFrame):
        df = results['biothings']
        if 'name' in df.columns:
            names.update(df['name'].dropna().astype(str).tolist())
    
    # From KEGG list results
    if 'kegg' in results and isinstance(results['kegg'], list):
        for disease in results['kegg']:
            if 'description' in disease and disease['description']:
                # KEGG descriptions often contain the name
                desc = disease['description']
                # Extract first part before semicolon or comma
                if ';' in desc:
                    name = desc.split(';')[0].strip()
                elif ',' in desc:
                    name = desc.split(',')[0].strip()
                else:
                    name = desc.strip()
                names.add(name)
    
    # From Open Targets DataFrame
    if 'opentargets' in results and isinstance(results['opentargets'], pd.DataFrame):
        df = results['opentargets']
        if 'name' in df.columns:
            names.update(df['name'].dropna().astype(str).tolist())
    
    # From Open Targets dict (details)
    if 'opentargets' in results and isinstance(results['opentargets'], dict):
        disease = results['opentargets'].get('data', {}).get('disease', {})
        if disease and 'name' in disease:
            names.add(disease['name'])
    
    return sorted(list(names))


def aggregate_disease_identifiers(results: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Aggregate all cross-database identifiers from search results.
    
    Args:
        results: Dictionary of results from different sources
    
    Returns:
        Dictionary mapping identifier types to lists of IDs
    """
    identifiers = {
        'mondo': [],
        'doid': [],
        'omim': [],
        'mesh': [],
        'kegg': [],
        'efo': [],
        'disease_id': [],
        'chembl_drugs': []
    }
    
    # From BioThings DataFrame
    if 'biothings' in results and isinstance(results['biothings'], pd.DataFrame):
        df = results['biothings']
        
        if 'disease_id' in df.columns:
            identifiers['disease_id'].extend(df['disease_id'].dropna().astype(str).tolist())
        
        if 'mondo_id' in df.columns:
            identifiers['mondo'].extend(df['mondo_id'].dropna().astype(str).tolist())
        
        if 'doid' in df.columns:
            identifiers['doid'].extend(df['doid'].dropna().astype(str).tolist())
    
    # From KEGG list results
    if 'kegg' in results and isinstance(results['kegg'], list):
        for disease in results['kegg']:
            if 'id' in disease and disease['id']:
                identifiers['kegg'].append(disease['id'])
    
    # From Open Targets DataFrame
    if 'opentargets' in results and isinstance(results['opentargets'], pd.DataFrame):
        df = results['opentargets']
        if 'id' in df.columns:
            identifiers['efo'].extend(df['id'].dropna().astype(str).tolist())
    
    # From Open Targets dict (details)
    if 'opentargets' in results and isinstance(results['opentargets'], dict):
        disease = results['opentargets'].get('data', {}).get('disease', {})
        if disease and 'id' in disease:
            identifiers['efo'].append(disease['id'])
    
    # From ChEMBL drugs DataFrame
    if 'chembl_drugs' in results and isinstance(results['chembl_drugs'], pd.DataFrame):
        df = results['chembl_drugs']
        if 'molecule_chembl_id' in df.columns:
            # Store drug ChEMBL IDs that treat this disease
            drug_ids = df['molecule_chembl_id'].dropna().astype(str).tolist()
            if drug_ids:
                identifiers['chembl_drugs'] = drug_ids[:10]  # Limit to first 10
    
    # Remove duplicates and empty lists
    for key in identifiers:
        identifiers[key] = sorted(list(set(identifiers[key])))
    
    # Remove empty identifier types
    identifiers = {k: v for k, v in identifiers.items() if v}
    
    return identifiers
