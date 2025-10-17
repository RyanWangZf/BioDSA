from typing import List, Dict, Any
import os
import requests
import time
import xml.etree.ElementTree as ET
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from .ratelimiter import RateLimiter

PUBMED_BASE_URL = "https://pubmed.ncbi.nlm.nih.gov/"
PUBMED_EU_UTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_API_KEY = os.environ.get("PUBMED_API_KEY")

# ===============================
# Helper functions
# ===============================
def _parse_and_extract_citation_relations(xml_response: str, relation_type: str) -> List[Dict[str, Any]]:
    """
    Extract citation relations from PubMed elink XML response.
    
    Args:
        xml_response: XML response from eutils elink API
        relation_type: Either 'cited_by' or 'cites'
    
    Returns:
        List of citation relations with source and target PMIDs
    """
    start_time = time.time()
    results = []
    try:
        root = ET.fromstring(xml_response)
        
        # Find all LinkSets in the response
        for linkset in root.findall(".//LinkSet"):
            # Get the source PMID (DbFrom)
            source_pmid_elem = linkset.find(".//IdList/Id")
            if source_pmid_elem is None:
                continue
            source_pmid = source_pmid_elem.text
            
            # Find LinkSetDb with the appropriate linkname
            linkname_map = {
                'cited_by': 'pubmed_pubmed_citedin',
                'cites': 'pubmed_pubmed_refs'
            }
            target_linkname = linkname_map.get(relation_type)
            
            for linksetdb in linkset.findall(".//LinkSetDb"):
                linkname_elem = linksetdb.find("LinkName")
                if linkname_elem is not None and linkname_elem.text == target_linkname:
                    # Extract all target PMIDs
                    for link_elem in linksetdb.findall(".//Link/Id"):
                        target_pmid = link_elem.text
                        results.append({
                            'source_pmid': source_pmid,
                            'target_pmid': target_pmid,
                            'relation_type': relation_type
                        })
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
    return results

def _get_cites_relations_one_request(pmids: List[str], rate_limiter: RateLimiter = None) -> List[Dict[str, Any]]:
    """
    Get articles that the input PMIDs cite (cites relations).
    
    Args:
        pmids: List of PMIDs to query
        rate_limiter: Rate limiter to control request frequency
    
    Returns:
        List of citation relations
    """
    if not pmids:
        return []

    if rate_limiter is not None:
        rate_limiter.wait_if_needed()
    
    # Construct URL with multiple id parameters: &id=pmid1&id=pmid2&id=pmid3
    id_params = "&".join([f"id={pmid}" for pmid in pmids])
    url = f"{PUBMED_EU_UTILS_BASE_URL}/elink.fcgi?dbfrom=pubmed&linkname=pubmed_pubmed_refs&{id_params}"
    if PUBMED_API_KEY is not None:
        url = f"{url}&api_key={PUBMED_API_KEY}"
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        print(f"Fetched cites relations for PMIDs takes {time.time() - start_time} seconds")
        return _parse_and_extract_citation_relations(response.text, 'cites')
    except requests.RequestException as e:
        print(f"Error fetching cites relations for PMIDs {pmids}: {e}")
        return []


def _get_cites_relations_batch_worker(pmid_batch: List[str], rate_limiter: RateLimiter, batch_id: int) -> Dict[str, Any]:
    """
    Worker function for processing a batch of PMIDs in a thread.
    
    Args:
        pmid_batch: List of PMIDs to process
        rate_limiter: Rate limiter to control request frequency
        batch_id: Identifier for this batch
    
    Returns:
        Dictionary with batch_id and results
    """
    try:
        results = _get_cites_relations_one_request(pmid_batch, rate_limiter)
        return {
            'batch_id': batch_id,
            'pmid_batch': pmid_batch,
            'results': results,
            'success': True
        }
    except Exception as e:
        print(f"Error processing batch {batch_id} with PMIDs {pmid_batch}: {e}")
        return {
            'batch_id': batch_id,
            'pmid_batch': pmid_batch,
            'results': [],
            'success': False,
            'error': str(e)
        }

# ===============================
# Main functions
# ===============================
def pubmed_api_get_paper_references(
    pmids: List[str],
    batch_size: int = 100,
    mini_batch_size: int = 20,  # Size of each sub-batch for threading
    max_workers: int = 4,  # Number of threads
    rate_limit: float = 3.0  # Requests per second
) -> List[Dict[str, Any]]:
    """
    Process paper references using multiple threads while respecting rate limits.
    
    Args:
        pmids: List of PMIDs to process
        batch_size: Number of PMIDs to process in each main batch
        mini_batch_size: Number of PMIDs per thread sub-batch
        max_workers: Maximum number of concurrent threads
        rate_limit: Maximum requests per second
        
    Returns:
        List of all paper references found
    """
    all_results = []
    
    if not pmids:
        print("All PMIDs already processed!")
        return all_results

    rate_limiter = RateLimiter(max_requests_per_second=rate_limit)
    # Process remaining PMIDs in main batches
    for i in tqdm(range(0, len(pmids), batch_size), desc="Processing citation batches"):
        end_idx = min(i + batch_size, len(pmids))
        main_batch_pmids = pmids[i:end_idx]
        
        print(f"Processing main batch {i//batch_size}: PMIDs {i} to {end_idx-1}")
        
        # Split main batch into mini-batches for threading
        mini_batches = []
        for j in range(0, len(main_batch_pmids), mini_batch_size):
            mini_end = min(j + mini_batch_size, len(main_batch_pmids))
            mini_batch = main_batch_pmids[j:mini_end]
            mini_batches.append(mini_batch)
        
        print(f"  Split into {len(mini_batches)} mini-batches for threaded processing")
        
        try:
            start_time = time.time()
            batch_results = []
            
            # Process mini-batches using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all mini-batches to the thread pool
                future_to_batch = {
                    executor.submit(_get_cites_relations_batch_worker, mini_batch, rate_limiter, idx): idx
                    for idx, mini_batch in enumerate(mini_batches)
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_batch):
                    batch_idx = future_to_batch[future]
                    try:
                        result = future.result()
                        if result['success']:
                            batch_results.extend(result['results'])
                            print(f"    Mini-batch {batch_idx} completed: {len(result['results'])} relations")
                        else:
                            print(f"    Mini-batch {batch_idx} failed: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        print(f"    Mini-batch {batch_idx} generated exception: {e}")
            
            print(f"Found {len(batch_results)} cites relations for main batch {i//batch_size} in {time.time() - start_time:.2f} seconds")
            
            # Group results by source PMID for individual checkpointing
            pmid_grouped_results = {}
            for relation in batch_results:
                source_pmid = relation['source_pmid']
                if source_pmid not in pmid_grouped_results:
                    pmid_grouped_results[source_pmid] = []
                pmid_grouped_results[source_pmid].append(relation)
            
            # Save individual PMID checkpoints and add to all results
            for pmid in main_batch_pmids:
                pmid_results = pmid_grouped_results.get(pmid, [])
                
                # Add PMID results to all results
                all_results.extend(pmid_results)
            
        except Exception as e:
            print(f"Error processing main batch: {str(e)}")
            # Continue with next batch rather than failing completely
            continue
    
    return all_results

