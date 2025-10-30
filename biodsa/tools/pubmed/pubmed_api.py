from typing import List, Dict, Any
import os
import requests
import time
import xml.etree.ElementTree as ET
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from xml.etree import ElementTree

from .ratelimiter import RateLimiter

PUBMED_BASE_URL = "https://pubmed.ncbi.nlm.nih.gov/"
PUBMED_EU_UTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_API_KEY = os.environ.get("PUBMED_API_KEY")

__all__ = [
    "pubmed_api_get_paper_references",
    "get_pubmed_articles",
    "fetch_paper_content_by_pmid",
]

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

def get_pubmed_articles(term):
    base_url_pubmed = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    search_url = f"{base_url_pubmed}/esearch.fcgi"
    fetch_url = f"{base_url_pubmed}/efetch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": term,
        "retmode": "xml",
        "retmax": "5",
        "sort": "relevance"
    }
    search_response = requests.get(search_url, params=search_params)
    try:
        search_results = ElementTree.fromstring(search_response.content)
        id_list = [id_tag.text for id_tag in search_results.findall('.//Id')]
    except ElementTree.ParseError as e:
        return f"Error parsing search results: {e}"
    
    if not id_list:
        return "No articles found for the query."
    
    fetch_params = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "retmode": "xml"
    }
    fetch_response = requests.get(fetch_url, params=fetch_params)
    
    try:
        articles = ElementTree.fromstring(fetch_response.content)
    except ElementTree.ParseError as e:
        return f"Error parsing fetch results: {e}"

    results = [] 
    for article in articles.findall('.//PubmedArticle'):
        pmid_elem = article.find('.//PMID')
        pmid = pmid_elem.text if pmid_elem is not None else "No PMID available"
        title_elem = article.find('.//ArticleTitle')
        title = title_elem.text if title_elem is not None else "No title available"
        abstract_elem = article.find('.//Abstract/AbstractText')
        abstract_text = abstract_elem.text if abstract_elem is not None else "No abstract available"
        results.append(f"PMID: {pmid}\nTitle: {title}\nAbstract: {abstract_text}\n")
    return "".join(results)


get_pubmed_articles_doc = {
    "name": "get_pubmed_articles",
    "description": "Given a PubMed ID, return related PubMed articles containing titles and abstractions.",
    "parameters": {
        "type": "object",
        "properties": {
            "term": {
                "type": "string",
                "description": "a pubmed ID to search.",
            },
        },
        "required": ["term"],
    },
}


def fetch_paper_content_by_pmid(pmid: str) -> Dict[str, Any]:
    """
    Fetch paper content for a single PMID from PubMed, PubTator3, and PMC BioC APIs.
    
    This function:
    1. Fetches title and abstract from PubMed API
    2. Fetches full content availability from PubTator3 API
    3. Attempts to fetch full open access text from PMC BioC JSON API
    4. Returns combined information with full text availability indicator
    
    Args:
        pmid: A single PubMed ID (PMID) as string
    
    Returns:
        Dictionary containing:
        - pmid: The PMID
        - title: Paper title from PubMed
        - abstract: Paper abstract from PubMed
        - has_full_text: Boolean indicating if full text is available
        - passages: List of passage types available (from PubTator or PMC)
        - full_content: Full text content if available
        - pmc_full_text: Full text from PMC BioC if available (open access papers)
        - source: Source of full text ('pubtator', 'pmc', or 'none')
        - error: Error message if any
    """
    result = {
        "pmid": pmid,
        "title": None,
        "abstract": None,
        "has_full_text": False,
        "passages": [],
        "full_content": None,
        "pmc_full_text": None,
        "source": "none",
        "error": None
    }
    
    # Step 1: Fetch from PubMed API
    base_url_pubmed = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    fetch_url = f"{base_url_pubmed}/efetch.fcgi"
    
    try:
        fetch_params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml"
        }
        if PUBMED_API_KEY:
            fetch_params["api_key"] = PUBMED_API_KEY
            
        fetch_response = requests.get(fetch_url, params=fetch_params, timeout=30)
        fetch_response.raise_for_status()
        
        articles = ElementTree.fromstring(fetch_response.content)
        article = articles.find('.//PubmedArticle')
        
        if article is not None:
            title_elem = article.find('.//ArticleTitle')
            result["title"] = title_elem.text if title_elem is not None else "No title available"
            
            # Get abstract text (may have multiple AbstractText elements)
            abstract_texts = []
            for abstract_elem in article.findall('.//Abstract/AbstractText'):
                label = abstract_elem.get('Label', '')
                text = abstract_elem.text if abstract_elem is not None else ""
                if label:
                    abstract_texts.append(f"{label}: {text}")
                else:
                    abstract_texts.append(text)
            
            result["abstract"] = "\n".join(abstract_texts) if abstract_texts else "No abstract available"
        else:
            result["error"] = "Paper not found in PubMed"
            
    except requests.RequestException as e:
        result["error"] = f"PubMed API error: {e}"
    except ElementTree.ParseError as e:
        result["error"] = f"PubMed XML parse error: {e}"
    except Exception as e:
        result["error"] = f"PubMed fetch error: {e}"
    
    # Step 2: Fetch from PubTator3 API to check full text availability
    try:
        pubtator_url = f"https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocjson?pmids={pmid}"
        pubtator_response = requests.get(pubtator_url, timeout=30)
        pubtator_response.raise_for_status()
        
        pubtator_data = pubtator_response.json()
        
        if 'PubTator3' in pubtator_data and len(pubtator_data['PubTator3']) > 0:
            pub_data = pubtator_data['PubTator3'][0]
            passages = pub_data.get('passages', [])
            
            # Collect passage types and full content
            passage_types = []
            full_content_parts = []
            
            for passage in passages:
                passage_type = passage.get('infons', {}).get('type', 'unknown')
                passage_types.append(passage_type)
                
                # Collect text from all passages
                text = passage.get('text', '')
                if text:
                    full_content_parts.append(f"[{passage_type.upper()}]\n{text}")
            
            result["passages"] = list(set(passage_types))
            result["has_full_text"] = any(
                ptype not in ['title', 'abstract', 'front'] 
                for ptype in passage_types
            )
            
            if full_content_parts:
                result["full_content"] = "\n\n".join(full_content_parts)
                if result["has_full_text"]:
                    result["source"] = "pubtator"
                
    except requests.RequestException as e:
        # Don't overwrite existing errors, just note PubTator issue
        if not result["error"]:
            result["error"] = f"PubTator API error: {e}"
    except (json.JSONDecodeError, KeyError) as e:
        if not result["error"]:
            result["error"] = f"PubTator parse error: {e}"
    except Exception as e:
        if not result["error"]:
            result["error"] = f"PubTator fetch error: {e}"
    
    # Step 3: Try to fetch full text from PMC BioC JSON API (for open access papers)
    try:
        pmc_bioc_url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pmid}/unicode"
        pmc_response = requests.get(pmc_bioc_url, timeout=30)
        pmc_response.raise_for_status()
        
        pmc_data = pmc_response.json()
        
        # Check if we got valid BioC data
        if isinstance(pmc_data, list) and len(pmc_data) > 0:
            bioc_collection = pmc_data[0]
            
            if bioc_collection.get('bioctype') == 'BioCCollection':
                documents = bioc_collection.get('documents', [])
                
                if documents and len(documents) > 0:
                    document = documents[0]
                    passages = document.get('passages', [])
                    
                    if passages:
                        # Collect all passages and their types
                        pmc_passage_types = []
                        pmc_content_parts = []
                        
                        for passage in passages:
                            infons = passage.get('infons', {})
                            section_type = infons.get('section_type', infons.get('type', 'unknown'))
                            text = passage.get('text', '')
                            
                            if text:
                                pmc_passage_types.append(section_type)
                                pmc_content_parts.append(f"[{section_type.upper()}]\n{text}")
                        
                        # Check if we have substantial content beyond title/abstract
                        has_pmc_full_text = any(
                            ptype not in ['TITLE', 'ABSTRACT', 'front', 'abstract_title_1', 'abstract']
                            for ptype in pmc_passage_types
                        )
                        
                        if pmc_content_parts:
                            pmc_full_content = "\n\n".join(pmc_content_parts)
                            result["pmc_full_text"] = pmc_full_content
                            
                            # If PMC has more complete content, use it as primary source
                            if has_pmc_full_text and len(pmc_full_content) > len(result.get("full_content") or ""):
                                result["has_full_text"] = True
                                result["full_content"] = pmc_full_content
                                result["passages"] = list(set(pmc_passage_types))
                                result["source"] = "pmc"
                            elif not result["has_full_text"] and has_pmc_full_text:
                                # If PubTator didn't have full text but PMC does
                                result["has_full_text"] = True
                                result["full_content"] = pmc_full_content
                                result["passages"] = list(set(pmc_passage_types))
                                result["source"] = "pmc"
                                
    except requests.RequestException:
        # PMC full text not available (not an error, just not open access)
        pass
    except (json.JSONDecodeError, KeyError, IndexError):
        # Invalid or unexpected response format from PMC
        pass
    except Exception:
        # Any other exception - silently continue as PMC is optional
        pass
    
    return result