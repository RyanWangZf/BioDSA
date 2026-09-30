"""Unified drug search and retrieval across multiple APIs.

This module aggregates drug information from:
- BioThings (MyChem.info)
- OpenFDA (Drugs@FDA and Drug Labeling)
- KEGG Drug Database
- Open Targets Platform
- ChEMBL Database
"""

import logging
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import individual API modules
from biodsa.tools.biothings.drugs import search_drugs as biothings_search_drugs
from biodsa.tools.openfda.drug import search_openfda_drugs
from biodsa.tools.openfda.product_labeling import search_drug_labels
from biodsa.tools.kegg.client import KEGGClient
from biodsa.tools.opentargets.drug_tools import search_drugs as opentargets_search_drugs, get_drug_details
from biodsa.tools.chembl.compound_tools import search_compounds as chembl_search_compounds
from biodsa.tools.chembl.drug_tools import get_drug_clinical_data as chembl_get_drug_clinical_data

# ================================================
# Unified Search Function
# ================================================

def search_drugs_unified(
    search_term: str,
    limit_per_source: int = 10,
    sources: Optional[List[str]] = None,
    save_path: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Search for drugs across multiple databases with a simple search term.
    
    This function queries multiple drug databases in parallel and aggregates
    the results, providing a comprehensive view of drug information.
    
    Args:
        search_term: Simple search term (drug name, condition, etc.)
        limit_per_source: Maximum results per source (default: 10)
        sources: List of sources to search. If None, searches all.
                 Options: ['biothings', 'openfda_approval', 'openfda_label', 'kegg', 'opentargets', 'chembl']
        save_path: Optional path to save aggregated results
    
    Returns:
        Tuple of (dict of results by source, formatted output string)
        
    Examples:
        >>> # Search for aspirin across all sources
        >>> results, output = search_drugs_unified("aspirin", limit_per_source=5)
        >>> print(output)  # Prints formatted results
    """
    if sources is None:
        sources = ['biothings', 'openfda_approval', 'openfda_label', 'kegg', 'opentargets', 'chembl']
    
    results = {}
    summaries = []
    errors = []
    
    # Search BioThings (MyChem.info)
    if 'biothings' in sources:
        try:
            df, summary = biothings_search_drugs(
                search=search_term,
                limit=limit_per_source
            )
            results['biothings'] = df
            summaries.append(f"**BioThings (MyChem.info):** {summary}")
        except Exception as e:
            logging.error(f"BioThings search failed: {e}")
            results['biothings'] = pd.DataFrame()
            errors.append(f"BioThings: {str(e)}")
    
    # Search OpenFDA Drugs@FDA (Approval Data)
    if 'openfda_approval' in sources:
        try:
            # Try multiple search strategies
            df = pd.DataFrame()
            
            # Strategy 1: Search by all fields
            df1, _ = search_openfda_drugs(
                search_term=search_term,
                limit=limit_per_source
            )
            
            # Strategy 2: Search by brand name
            df2, _ = search_openfda_drugs(
                brand_name=search_term,
                limit=limit_per_source
            )
            
            # Strategy 3: Search by substance
            df3, _ = search_openfda_drugs(
                substance_name=search_term.upper(),
                limit=limit_per_source
            )
            
            # Combine and deduplicate
            df = pd.concat([df1, df2, df3], ignore_index=True)
            if not df.empty:
                df = df.drop_duplicates(subset=['application_number'], keep='first')
                df = df.head(limit_per_source)
            
            results['openfda_approval'] = df
            summaries.append(f"**OpenFDA Approval:** Found {len(df)} drug products")
        except Exception as e:
            logging.error(f"OpenFDA approval search failed: {e}")
            results['openfda_approval'] = pd.DataFrame()
            errors.append(f"OpenFDA Approval: {str(e)}")
    
    # Search OpenFDA Drug Labels
    if 'openfda_label' in sources:
        try:
            # Try multiple search strategies
            df = pd.DataFrame()
            
            # Strategy 1: Search by brand name
            df1, _ = search_drug_labels(
                brand_name=search_term,
                limit=limit_per_source
            )
            
            # Strategy 2: Search by generic name
            df2, _ = search_drug_labels(
                generic_name=search_term,
                limit=limit_per_source
            )
            
            # Strategy 3: Search by substance
            df3, _ = search_drug_labels(
                substance_name=search_term.upper(),
                limit=limit_per_source
            )
            
            # Strategy 4: Search in indications
            df4, _ = search_drug_labels(
                indications_and_usage=search_term,
                limit=limit_per_source
            )
            
            # Combine and deduplicate by set_id
            df = pd.concat([df1, df2, df3, df4], ignore_index=True)
            if not df.empty:
                df = df.drop_duplicates(subset=['set_id'], keep='first')
                df = df.head(limit_per_source)
            
            results['openfda_label'] = df
            summaries.append(f"**OpenFDA Labels:** Found {len(df)} drug labels")
        except Exception as e:
            logging.error(f"OpenFDA label search failed: {e}")
            results['openfda_label'] = pd.DataFrame()
            errors.append(f"OpenFDA Labels: {str(e)}")
    
    # Search KEGG Drug Database
    if 'kegg' in sources:
        try:
            kegg_client = KEGGClient()
            kegg_results = kegg_client.search_drugs(search_term, max_results=limit_per_source)
            results['kegg'] = kegg_results  # List of dicts
            summaries.append(f"**KEGG Drug:** Found {len(kegg_results)} drugs")
        except Exception as e:
            logging.error(f"KEGG search failed: {e}")
            results['kegg'] = []
            errors.append(f"KEGG: {str(e)}")
    
    # Search Open Targets
    if 'opentargets' in sources:
        try:
            df, summary = opentargets_search_drugs(
                query=search_term,
                size=limit_per_source
            )
            results['opentargets'] = df
            summaries.append(f"**Open Targets:** Found {len(df)} drugs")
        except Exception as e:
            logging.error(f"Open Targets search failed: {e}")
            results['opentargets'] = pd.DataFrame()
            errors.append(f"Open Targets: {str(e)}")
    
    # Search ChEMBL
    if 'chembl' in sources:
        try:
            df, summary = chembl_search_compounds(
                query=search_term,
                limit=limit_per_source
            )
            results['chembl'] = df
            summaries.append(f"**ChEMBL:** Found {len(df)} compounds")
        except Exception as e:
            logging.error(f"ChEMBL search failed: {e}")
            results['chembl'] = pd.DataFrame()
            errors.append(f"ChEMBL: {str(e)}")
    
    # Build formatted output string
    output = "# Unified Drug Search Results\n\n"
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
            output += f"Found {len(source_data)} drugs from BioThings (MyChem.info):\n\n"
            for idx, row in source_data.iterrows():
                output += f"**{idx + 1}. {row.get('name', 'N/A')}**\n"
                if pd.notna(row.get('drug_id')):
                    output += f"  - Drug ID: {row['drug_id']}\n"
                if pd.notna(row.get('drugbank_id')):
                    output += f"  - DrugBank: {row['drugbank_id']}\n"
                if pd.notna(row.get('chembl_id')):
                    output += f"  - ChEMBL: {row['chembl_id']}\n"
                if pd.notna(row.get('formula')):
                    output += f"  - Formula: {row['formula']}\n"
                output += "\n"
        
        elif source_name == 'openfda_approval':
            output += f"Found {len(source_data)} FDA-approved products:\n\n"
            for idx, row in source_data.iterrows():
                brand = row.get('brand_name', '')
                generic = row.get('generic_name', '')
                output += f"**{idx + 1}. {brand or generic or 'N/A'}**\n"
                if brand and generic:
                    output += f"  - Generic: {generic}\n"
                if pd.notna(row.get('application_number')):
                    output += f"  - Application: {row['application_number']}\n"
                if pd.notna(row.get('marketing_status')):
                    output += f"  - Status: {row['marketing_status']}\n"
                if pd.notna(row.get('dosage_form')):
                    output += f"  - Form: {row['dosage_form']}\n"
                output += "\n"
        
        elif source_name == 'openfda_label':
            output += f"Found {len(source_data)} drug labels:\n\n"
            for idx, row in source_data.iterrows():
                brand = row.get('brand_name', '')
                generic = row.get('generic_name', '')
                output += f"**{idx + 1}. {brand or generic or 'N/A'}**\n"
                if brand and generic:
                    output += f"  - Generic: {generic}\n"
                if pd.notna(row.get('substance_name')):
                    substance = str(row['substance_name'])[:100]
                    output += f"  - Active Ingredient: {substance}\n"
                if pd.notna(row.get('route')):
                    output += f"  - Route: {row['route']}\n"
                if pd.notna(row.get('indications_and_usage')):
                    indication = str(row['indications_and_usage'])[:150]
                    output += f"  - Indication: {indication}...\n"
                if pd.notna(row.get('boxed_warning')):
                    output += f"  - ⚠️ Has Boxed Warning\n"
                output += "\n"
        
        elif source_name == 'kegg':
            output += f"Found {len(source_data)} drugs from KEGG:\n\n"
            for idx, drug in enumerate(source_data, 1):
                drug_id = drug.get('id', 'N/A')
                description = drug.get('description', 'N/A')
                output += f"**{idx}. {drug_id}** - {description}\n"
                output += "\n"
        
        elif source_name == 'opentargets':
            output += f"Found {len(source_data)} drugs from Open Targets:\n\n"
            for idx, row in source_data.iterrows():
                output += f"**{idx + 1}. {row.get('name', 'N/A')}**\n"
                if pd.notna(row.get('id')):
                    output += f"  - ChEMBL ID: {row['id']}\n"
                if pd.notna(row.get('description')):
                    desc = str(row['description'])[:150]
                    output += f"  - Description: {desc}...\n"
                if pd.notna(row.get('entity')):
                    output += f"  - Entity Type: {row['entity']}\n"
                output += "\n"
        
        elif source_name == 'chembl':
            output += f"Found {len(source_data)} compounds from ChEMBL:\n\n"
            for idx, row in source_data.iterrows():
                output += f"**{idx + 1}. {row.get('pref_name', 'N/A')}**\n"
                if pd.notna(row.get('molecule_chembl_id')):
                    output += f"  - ChEMBL ID: {row['molecule_chembl_id']}\n"
                if pd.notna(row.get('molecule_type')):
                    output += f"  - Type: {row['molecule_type']}\n"
                if pd.notna(row.get('max_phase')):
                    phases = ['Preclinical', 'Phase I', 'Phase II', 'Phase III', 'Approved']
                    phase = row.get('max_phase')
                    try:
                        phase = int(phase)
                        phase_str = phases[phase] if 0 <= phase < len(phases) else str(phase)
                        output += f"  - Development Phase: {phase_str}\n"
                    except (ValueError, TypeError):
                        output += f"  - Development Phase: {phase}\n"
                # Add molecular properties if available
                props = row.get('molecule_properties', {})
                if isinstance(props, dict) and props:
                    if props.get('full_mwt') or props.get('molecular_weight'):
                        mw = props.get('full_mwt', props.get('molecular_weight'))
                        output += f"  - MW: {mw} Da\n"
                output += "\n"
    
    # Aggregate information
    output += "\n" + "="*80 + "\n"
    output += "\n## Aggregated Information\n\n"
    
    all_names = aggregate_drug_names(results)
    if all_names:
        output += f"**All Drug Names Found ({len(all_names)}):**\n"
        for name in all_names[:20]:
            output += f"  - {name}\n"
        if len(all_names) > 20:
            output += f"  ... and {len(all_names) - 20} more\n"
        output += "\n"
    
    all_ids = aggregate_drug_identifiers(results)
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

def fetch_drug_details_unified(
    drug_id: str,
    id_type: Optional[str] = None,
    sources: Optional[List[str]] = None,
    save_path: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Fetch detailed drug information using any drug identifier.
    
    This function automatically detects the ID type (if not specified) and
    queries relevant databases to fetch comprehensive drug information.
    
    Args:
        drug_id: Drug identifier (DrugBank ID, ChEBI ID, ChEMBL ID, 
                 PubChem CID, KEGG ID, OpenFDA application number, etc.)
        id_type: Type of ID. If None, will attempt to detect.
                 Options: 'drugbank', 'chebi', 'chembl', 'pubchem', 
                         'kegg', 'openfda_app', 'name'
        sources: List of sources to fetch from. If None, fetches from all relevant.
                 Options: ['biothings', 'openfda_approval', 'openfda_label', 'kegg', 'opentargets', 'chembl']
        save_path: Optional path to save results as JSON
    
    Returns:
        Tuple of (dict of drug details by source, formatted output string)
        
    Examples:
        >>> # Fetch by DrugBank ID
        >>> details, output = fetch_drug_details_unified("DB00945")
        >>> print(output)  # Prints formatted details
    """
    # Auto-detect ID type if not specified
    if id_type is None:
        id_type = _detect_id_type(drug_id)
    
    if sources is None:
        sources = ['biothings', 'openfda_approval', 'openfda_label', 'kegg', 'opentargets', 'chembl']
    
    details = {}
    summaries = []
    errors = []
    
    # Fetch from BioThings
    if 'biothings' in sources and id_type in ['drugbank', 'chebi', 'chembl', 'pubchem', 'name']:
        try:
            # Build search query based on ID type
            search_params = {'limit': 1}
            
            if id_type == 'drugbank':
                search_params['drugbank_id'] = drug_id
            elif id_type == 'chebi':
                search_params['chebi_id'] = drug_id
            elif id_type == 'chembl':
                search_params['chembl_id'] = drug_id
            elif id_type == 'pubchem':
                search_params['pubchem_cid'] = drug_id
            elif id_type == 'name':
                search_params['name'] = drug_id
            
            df, summary = biothings_search_drugs(**search_params)
            
            if not df.empty:
                details['biothings'] = df.iloc[0].to_dict()
                summaries.append(f"**BioThings:** Found drug information")
            else:
                summaries.append(f"**BioThings:** No results found")
        except Exception as e:
            logging.error(f"BioThings fetch failed: {e}")
            errors.append(f"BioThings: {str(e)}")
    
    # Fetch from OpenFDA Approval Data
    if 'openfda_approval' in sources:
        try:
            df = pd.DataFrame()
            
            if id_type == 'openfda_app':
                from biodsa.tools.openfda.drug import fetch_openfda_drug_by_application
                df, _ = fetch_openfda_drug_by_application(drug_id)
            elif id_type == 'name':
                # Try brand name and generic name
                df1, _ = search_openfda_drugs(brand_name=drug_id, limit=1)
                df2, _ = search_openfda_drugs(generic_name=drug_id, limit=1)
                df = df1 if not df1.empty else df2
            elif id_type in ['drugbank', 'chebi', 'chembl']:
                # These IDs are not directly searchable in OpenFDA
                # Try searching by substance name if we have it from BioThings
                if 'biothings' in details:
                    substance_name = details['biothings'].get('name')
                    if substance_name:
                        df, _ = search_openfda_drugs(substance_name=substance_name.upper(), limit=1)
            
            if not df.empty:
                details['openfda_approval'] = df.iloc[0].to_dict()
                summaries.append(f"**OpenFDA Approval:** Found drug product")
            else:
                summaries.append(f"**OpenFDA Approval:** No results found")
        except Exception as e:
            logging.error(f"OpenFDA approval fetch failed: {e}")
            errors.append(f"OpenFDA Approval: {str(e)}")
    
    # Fetch from OpenFDA Labels
    if 'openfda_label' in sources:
        try:
            df = pd.DataFrame()
            
            if id_type == 'name':
                # Try brand name and generic name
                df1, _ = search_drug_labels(brand_name=drug_id, limit=1)
                df2, _ = search_drug_labels(generic_name=drug_id, limit=1)
                df = df1 if not df1.empty else df2
            elif id_type == 'openfda_app':
                df, _ = search_drug_labels(application_number=drug_id, limit=1)
            elif id_type in ['drugbank', 'chebi', 'chembl']:
                # Try using substance name from BioThings
                if 'biothings' in details:
                    substance_name = details['biothings'].get('name')
                    if substance_name:
                        df, _ = search_drug_labels(substance_name=substance_name.upper(), limit=1)
            
            if not df.empty:
                details['openfda_label'] = df.iloc[0].to_dict()
                summaries.append(f"**OpenFDA Labels:** Found drug label")
            else:
                summaries.append(f"**OpenFDA Labels:** No results found")
        except Exception as e:
            logging.error(f"OpenFDA label fetch failed: {e}")
            errors.append(f"OpenFDA Labels: {str(e)}")
    
    # Fetch from KEGG
    if 'kegg' in sources:
        try:
            kegg_client = KEGGClient()
            
            if id_type == 'kegg':
                # Direct fetch by KEGG drug ID
                drug_info = kegg_client.get_drug_info(drug_id)
                details['kegg'] = drug_info
                summaries.append(f"**KEGG:** Found drug information")
            elif id_type == 'name':
                # Search first, then fetch
                search_results = kegg_client.search_drugs(drug_id, max_results=1)
                if search_results:
                    kegg_id = search_results[0]['id']
                    drug_info = kegg_client.get_drug_info(kegg_id)
                    details['kegg'] = drug_info
                    summaries.append(f"**KEGG:** Found drug information")
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
            # Get ChEMBL ID for Open Targets fetch
            chembl_id = drug_id if id_type == 'chembl' else None
            
            # If we fetched from BioThings, extract the ChEMBL ID
            if not chembl_id and 'biothings' in details:
                biothings_data = details['biothings']
                if isinstance(biothings_data, dict) and 'chembl_id' in biothings_data:
                    chembl_id = biothings_data['chembl_id']
            
            if chembl_id:
                drug_details, drug_summary = get_drug_details(chembl_id)
                if drug_details:
                    details['opentargets'] = drug_details
                    summaries.append(f"**Open Targets:** Found drug information")
                else:
                    summaries.append(f"**Open Targets:** No drug found for ChEMBL ID")
            else:
                summaries.append(f"**Open Targets:** Could not determine ChEMBL ID for drug fetch")
        except Exception as e:
            logging.error(f"Open Targets fetch failed: {e}")
            errors.append(f"Open Targets: {str(e)}")
    
    # Fetch from ChEMBL
    if 'chembl' in sources:
        try:
            # Get ChEMBL ID
            chembl_id = drug_id if id_type == 'chembl' else None
            
            # If we fetched from BioThings, extract the ChEMBL ID
            if not chembl_id and 'biothings' in details:
                biothings_data = details['biothings']
                if isinstance(biothings_data, dict) and 'chembl_id' in biothings_data:
                    chembl_id = biothings_data['chembl_id']
            
            # Try name search if no ChEMBL ID
            if not chembl_id and id_type == 'name':
                search_df, _ = chembl_search_compounds(query=drug_id, limit=1)
                if not search_df.empty:
                    chembl_id = search_df.iloc[0].get('molecule_chembl_id')
            
            if chembl_id:
                clinical_data, _ = chembl_get_drug_clinical_data(chembl_id)
                if clinical_data:
                    details['chembl'] = clinical_data
                    summaries.append(f"**ChEMBL:** Found comprehensive drug data")
                else:
                    summaries.append(f"**ChEMBL:** No data found for ChEMBL ID")
            else:
                summaries.append(f"**ChEMBL:** Could not determine ChEMBL ID for drug fetch")
        except Exception as e:
            logging.error(f"ChEMBL fetch failed: {e}")
            errors.append(f"ChEMBL: {str(e)}")
    
    # Build formatted output
    output = "# Drug Details\n\n"
    output += f"## Drug ID: '{drug_id}' (ID Type: {id_type})\n\n"
    output += f"**Sources found:** {len([d for d in details.values() if d])} / {len(sources)}\n\n"
    output += "### Results by Source:\n"
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
        
        output += f"\n## {source_name.upper()} Data\n\n"
        
        if source_name == 'biothings':
            output += "**Chemical and Pharmacological Information:**\n\n"
            if 'name' in source_data:
                output += f"- **Name:** {source_data['name']}\n"
            if 'drugbank_id' in source_data:
                output += f"- **DrugBank ID:** {source_data['drugbank_id']}\n"
            if 'chebi_id' in source_data:
                output += f"- **ChEBI ID:** {source_data['chebi_id']}\n"
            if 'chembl_id' in source_data:
                output += f"- **ChEMBL ID:** {source_data['chembl_id']}\n"
            if 'pubchem_cid' in source_data:
                output += f"- **PubChem CID:** {source_data['pubchem_cid']}\n"
            if 'formula' in source_data:
                output += f"- **Formula:** {source_data['formula']}\n"
            if 'inchikey' in source_data:
                inchikey = str(source_data['inchikey'])[:50]
                output += f"- **InChI Key:** {inchikey}...\n"
            output += "\n"
        
        elif source_name == 'openfda_approval':
            output += "**FDA Approval Information:**\n\n"
            if 'application_number' in source_data:
                output += f"- **Application:** {source_data['application_number']}\n"
            if 'brand_name' in source_data:
                output += f"- **Brand Name:** {source_data['brand_name']}\n"
            if 'generic_name' in source_data:
                output += f"- **Generic Name:** {source_data['generic_name']}\n"
            if 'marketing_status' in source_data:
                output += f"- **Marketing Status:** {source_data['marketing_status']}\n"
            if 'dosage_form' in source_data:
                output += f"- **Dosage Form:** {source_data['dosage_form']}\n"
            if 'route' in source_data:
                output += f"- **Route:** {source_data['route']}\n"
            if 'sponsor_name' in source_data:
                output += f"- **Sponsor:** {source_data['sponsor_name']}\n"
            output += "\n"
        
        elif source_name == 'openfda_label':
            output += "**Product Labeling Information:**\n\n"
            if 'brand_name' in source_data:
                output += f"- **Brand Name:** {source_data['brand_name']}\n"
            if 'generic_name' in source_data:
                output += f"- **Generic Name:** {source_data['generic_name']}\n"
            
            if 'indications_and_usage' in source_data and source_data['indications_and_usage']:
                indication = str(source_data['indications_and_usage'])[:300]
                output += f"\n**Indications:**\n{indication}...\n\n"
            
            if 'boxed_warning' in source_data and source_data['boxed_warning']:
                warning = str(source_data['boxed_warning'])[:200]
                output += f"**⚠️ BOXED WARNING:**\n{warning}...\n\n"
            
            if 'contraindications' in source_data and source_data['contraindications']:
                contra = str(source_data['contraindications'])[:200]
                output += f"**Contraindications:**\n{contra}...\n\n"
            
            if 'warnings' in source_data and source_data['warnings']:
                warn = str(source_data['warnings'])[:200]
                output += f"**Warnings:**\n{warn}...\n\n"
            
            if 'drug_interactions' in source_data and source_data['drug_interactions']:
                interact = str(source_data['drug_interactions'])[:200]
                output += f"**Drug Interactions:**\n{interact}...\n\n"
        
        elif source_name == 'kegg':
            output += "**KEGG Drug Information:**\n\n"
            if 'ENTRY' in source_data:
                output += f"- **Entry:** {source_data['ENTRY']}\n"
            if 'NAME' in source_data:
                output += f"- **Name:** {source_data['NAME']}\n"
            if 'FORMULA' in source_data:
                output += f"- **Formula:** {source_data['FORMULA']}\n"
            if 'MOL_WEIGHT' in source_data:
                output += f"- **Molecular Weight:** {source_data['MOL_WEIGHT']}\n"
            
            if 'target_gene_ids' in source_data and source_data['target_gene_ids']:
                output += f"\n**Target Genes:** {', '.join(source_data['target_gene_ids'][:5])}\n"
            
            if 'pathways' in source_data and source_data['pathways']:
                output += f"\n**Pathways:**\n"
                for pathway_id, pathway_name in source_data['pathways'][:5]:
                    output += f"  - {pathway_id}: {pathway_name}\n"
            
            if 'efficacy' in source_data and source_data['efficacy']:
                output += f"\n**Efficacy:** {source_data['efficacy'][0]}\n"
            
            if 'disease' in source_data and source_data['disease']:
                output += f"\n**Disease:** {', '.join(source_data['disease'])}\n"
            
            output += "\n"
        
        elif source_name == 'opentargets':
            drug = source_data.get('data', {}).get('drug', {})
            if drug:
                output += "**Open Targets Drug Information:**\n\n"
                output += f"- **Name:** {drug.get('name', 'N/A')}\n"
                output += f"- **ChEMBL ID:** {drug.get('id', 'N/A')}\n"
                output += f"- **Drug Type:** {drug.get('drugType', 'N/A')}\n"
                output += f"- **Maximum Clinical Trial Phase:** {drug.get('maximumClinicalTrialPhase', 'N/A')}\n"
                output += f"- **Has Been Withdrawn:** {drug.get('hasBeenWithdrawn', False)}\n"
                
                # Synonyms
                synonyms = drug.get('synonyms', [])
                if synonyms:
                    output += f"\n**Synonyms ({len(synonyms)} total):**\n"
                    for syn in synonyms[:5]:
                        output += f"  - {syn}\n"
                
                # Linked entities
                linked_diseases = drug.get('linkedDiseases', {})
                linked_targets = drug.get('linkedTargets', {})
                if linked_diseases or linked_targets:
                    output += f"\n**Associated Entities:**\n"
                    output += f"  - Linked Diseases: {linked_diseases.get('count', 0)}\n"
                    output += f"  - Linked Targets: {linked_targets.get('count', 0)}\n"
                
                output += "\n"
        
        elif source_name == 'chembl':
            output += "**ChEMBL Database Information:**\n\n"
            
            # Compound information
            compound = source_data.get('compound', {})
            if compound:
                output += f"- **Name:** {compound.get('pref_name', 'N/A')}\n"
                output += f"- **ChEMBL ID:** {compound.get('molecule_chembl_id', 'N/A')}\n"
                output += f"- **Type:** {compound.get('molecule_type', 'N/A')}\n"
                
                # Development phase
                if compound.get('max_phase') is not None:
                    phases = ['Preclinical', 'Phase I', 'Phase II', 'Phase III', 'Approved']
                    phase = compound.get('max_phase')
                    try:
                        phase = int(phase)
                        phase_str = phases[phase] if 0 <= phase < len(phases) else str(phase)
                        output += f"- **Development Phase:** {phase_str}\n"
                    except (ValueError, TypeError):
                        output += f"- **Development Phase:** {phase}\n"
                
                # Molecular properties
                props = compound.get('molecule_properties', {})
                if props:
                    output += f"\n**Molecular Properties:**\n"
                    if props.get('full_mwt') or props.get('molecular_weight'):
                        mw = props.get('full_mwt', props.get('molecular_weight'))
                        output += f"  - MW: {mw} Da\n"
                    if props.get('alogp'):
                        output += f"  - LogP: {props['alogp']}\n"
                    if props.get('num_ro5_violations') is not None:
                        output += f"  - Lipinski Violations: {props['num_ro5_violations']}\n"
            
            # Indications
            indications = source_data.get('indications', [])
            if indications:
                output += f"\n**Therapeutic Indications ({len(indications)} found):**\n"
                for ind in indications[:5]:
                    ind_name = ind.get('indication', 'N/A')
                    output += f"  - {ind_name}"
                    if ind.get('max_phase_for_ind') is not None:
                        output += f" (Phase {ind['max_phase_for_ind']})"
                    output += "\n"
                if len(indications) > 5:
                    output += f"  ... and {len(indications) - 5} more\n"
            
            # Mechanisms
            mechanisms = source_data.get('mechanisms', [])
            if mechanisms:
                output += f"\n**Mechanisms of Action ({len(mechanisms)} found):**\n"
                for mech in mechanisms[:5]:
                    mech_desc = mech.get('mechanism_of_action', 'N/A')
                    target = mech.get('target_pref_name', 'N/A')
                    action = mech.get('action_type', 'N/A')
                    output += f"  - {mech_desc}\n"
                    output += f"    Target: {target} ({action})\n"
                if len(mechanisms) > 5:
                    output += f"  ... and {len(mechanisms) - 5} more\n"
            
            output += "\n"
    
    output += "="*80 + "\n"
    
    # Save results if requested
    if save_path:
        try:
            import json
            save_data = {
                'drug_id': drug_id,
                'id_type': id_type,
                'sources': sources,
                'details': details
            }
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent=2, default=str)
            output += f"\n**Results saved to:** {save_path}\n"
        except Exception as e:
            logging.error(f"Error saving results: {e}")
            output += f"\n⚠️ **Error saving results:** {e}\n"
    
    return details, output


# ================================================
# Helper Functions
# ================================================

def _detect_id_type(drug_id: str) -> str:
    """
    Detect the type of drug identifier.
    
    Args:
        drug_id: The drug identifier string
    
    Returns:
        Detected ID type
    """
    drug_id_upper = drug_id.upper()
    
    # DrugBank ID: DB##### (5 digits)
    if drug_id_upper.startswith('DB') and len(drug_id) == 7:
        return 'drugbank'
    
    # ChEBI ID: CHEBI:#####
    if drug_id_upper.startswith('CHEBI:'):
        return 'chebi'
    
    # ChEMBL ID: CHEMBL#####
    if drug_id_upper.startswith('CHEMBL'):
        return 'chembl'
    
    # OpenFDA Application: NDA/ANDA/BLA + 6 digits
    if drug_id_upper.startswith(('NDA', 'ANDA', 'BLA')) and len(drug_id) >= 9:
        return 'openfda_app'
    
    # KEGG Drug: D##### (5 digits)
    if drug_id_upper.startswith('D') and len(drug_id) == 6 and drug_id[1:].isdigit():
        return 'kegg'
    
    # PubChem CID: numeric only
    if drug_id.isdigit():
        return 'pubchem'
    
    # Default to name search
    return 'name'


# ================================================
# Aggregation Helpers
# ================================================

def aggregate_drug_names(results: Dict[str, Any]) -> List[str]:
    """Extract and deduplicate drug names from all sources."""
    names = set()
    
    for source, data in results.items():
        if isinstance(data, pd.DataFrame):
            if data.empty:
                continue
            
            if source == 'biothings':
                if 'name' in data.columns:
                    names.update(data['name'].dropna().tolist())
                if 'tradename' in data.columns:
                    for tn in data['tradename'].dropna():
                        if isinstance(tn, str):
                            names.update([n.strip() for n in tn.split(',')])
            
            elif source in ['openfda_approval', 'openfda_label']:
                if 'brand_name' in data.columns:
                    for bn in data['brand_name'].dropna():
                        if isinstance(bn, str):
                            names.update([n.strip() for n in bn.split(',')])
                if 'generic_name' in data.columns:
                    for gn in data['generic_name'].dropna():
                        if isinstance(gn, str):
                            names.update([n.strip() for n in gn.split(',')])
            
            elif source == 'opentargets':
                if 'name' in data.columns:
                    names.update(data['name'].dropna().tolist())
            
            elif source == 'chembl':
                if 'pref_name' in data.columns:
                    names.update(data['pref_name'].dropna().tolist())
        
        elif source == 'kegg' and isinstance(data, list):
            for drug in data:
                if 'description' in drug:
                    # Extract drug name from description (usually first part before semicolon)
                    desc = drug['description'].split(';')[0].strip()
                    if desc:
                        names.add(desc)
    
    return sorted(list(names))


def aggregate_drug_identifiers(results: Dict[str, Any]) -> Dict[str, List[str]]:
    """Extract and organize all drug identifiers from all sources."""
    identifiers = {
        'drugbank': set(),
        'chebi': set(),
        'chembl': set(),
        'pubchem': set(),
        'kegg': set(),
        'openfda_app': set(),
        'chembl': set(),
    }
    
    for source, data in results.items():
        if isinstance(data, pd.DataFrame):
            if data.empty:
                continue
            data_dict = data.iloc[0].to_dict() if len(data) > 0 else {}
        elif isinstance(data, list):
            # Handle KEGG list format
            if source == 'kegg' and data:
                for drug in data:
                    if 'id' in drug:
                        identifiers['kegg'].add(drug['id'])
                continue
            else:
                data_dict = {}
        else:
            data_dict = data or {}
        
        # Extract identifiers based on source
        if source == 'biothings':
            if 'drugbank_id' in data_dict and data_dict['drugbank_id']:
                identifiers['drugbank'].add(str(data_dict['drugbank_id']))
            if 'chebi_id' in data_dict and data_dict['chebi_id']:
                identifiers['chebi'].add(str(data_dict['chebi_id']))
            if 'chembl_id' in data_dict and data_dict['chembl_id']:
                identifiers['chembl'].add(str(data_dict['chembl_id']))
            if 'pubchem_cid' in data_dict and data_dict['pubchem_cid']:
                identifiers['pubchem'].add(str(data_dict['pubchem_cid']))
        
        elif source in ['openfda_approval', 'openfda_label']:
            if 'application_number' in data_dict and data_dict['application_number']:
                app_num = data_dict['application_number']
                if isinstance(app_num, str):
                    identifiers['openfda_app'].add(app_num)
                elif isinstance(app_num, list):
                    identifiers['openfda_app'].update(app_num)
        
        elif source == 'kegg' and isinstance(data_dict, dict):
            if 'ENTRY' in data_dict:
                # Extract drug ID from ENTRY field (format: "D00001      Drug")
                entry = data_dict['ENTRY'].split()[0]
                identifiers['kegg'].add(entry)
        
        elif source == 'opentargets':
            # From Open Targets DataFrame
            if isinstance(data, pd.DataFrame) and not data.empty:
                if 'id' in data.columns:
                    for chembl_id in data['id'].dropna():
                        if isinstance(chembl_id, str):
                            identifiers['chembl'].add(chembl_id)
            # From Open Targets dict (details)
            elif isinstance(data_dict, dict) and 'data' in data_dict:
                drug = data_dict.get('data', {}).get('drug', {})
                if drug and 'id' in drug:
                    identifiers['chembl'].add(drug['id'])
        
        elif source == 'chembl':
            # From ChEMBL DataFrame
            if isinstance(data, pd.DataFrame) and not data.empty:
                if 'molecule_chembl_id' in data.columns:
                    for chembl_id in data['molecule_chembl_id'].dropna():
                        if isinstance(chembl_id, str):
                            identifiers['chembl'].add(chembl_id)
            # From ChEMBL dict (clinical data)
            elif isinstance(data_dict, dict) and 'compound' in data_dict:
                compound = data_dict.get('compound', {})
                if compound and 'molecule_chembl_id' in compound:
                    identifiers['chembl'].add(compound['molecule_chembl_id'])
    
    # Convert sets to sorted lists
    return {k: sorted(list(v)) for k, v in identifiers.items() if v}

