import os
import json
import pdb
from typing_extensions import Set
import requests
import time
import pandas as pd
from tqdm import tqdm
from collections import defaultdict

from .ratelimiter import RateLimiter

PUBTATOR3_BASE_URL = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api"
PUBTATOR3_SEARCH_URL = f"{PUBTATOR3_BASE_URL}/search/"
PUBTATOR3_FULLTEXT_URL = f"{PUBTATOR3_BASE_URL}/publications/export/biocjson"
PUBTATOR3_AUTOCOMPLETE_URL = f"{PUBTATOR3_BASE_URL}/entity/autocomplete/"


# ===============================
# Helper functions
# ===============================
def _parse_pubtator_response_to_get_content_and_attributes_and_relations(pubtator_json):
    """
    Parse PubTator3 JSON response to extract conditions and interventions from the content, attributes, and relations.
    """
    main_annotations = defaultdict(set)
    relevant_annotations = defaultdict(set)
    relations = []
    
    # Process passages
    if "passages" in pubtator_json:
        for passage in pubtator_json["passages"]:
            passage_type = passage.get("infons", {}).get("type", "")
            annotations = passage.get("annotations", [])
            
            if passage_type in ["title"]:
                for annotation in annotations:
                    infons = annotation.get("infons", {})
                    main_annotations[infons.get("type")].add(infons['name'])

            if passage_type in ["abstract"]:
                for annotation in annotations:
                    infons = annotation.get("infons", {})
                    relevant_annotations[infons.get("type")].add(infons['name'])

    # Process relations for additional chemicals and diseases
    if "relations" in pubtator_json:
        for relation in pubtator_json["relations"]:
            infons = relation.get("infons", {})

            relation_type = infons.get("type")
            if relation_type in [
                "Negative_Correlation",
                "Association",
                "Positive_Correlation"
            ]:
                # only extract when chemicals or diseases are involved
                # Check role1 and role2
                role1 = infons.get("role1", {})
                role2 = infons.get("role2", {})

                name1 = role1.get("name")
                name2 = role2.get("name")

                rel_type = infons.get("type")
                if rel_type.lower() not in ["association"]: # association is too common to be included in the relations
                    relations.append({
                        "type": rel_type.lower(),
                        "name1": name1,
                        "name2": name2
                    })

    # standardize the data
    main_annotations = {k: sorted(list(v)) for k, v in main_annotations.items()}
    relevant_annotations = {f"Relevant_{k}": sorted(list(v)) for k, v in relevant_annotations.items()}
    # each item is a string of the form "name1:type:name2"
    relation_mentions = []
    for relation in relations:
        relation_mentions.append(f"{relation['name1']}:{relation['type']}:{relation['name2']}")
    relation_mentions = sorted(list(set(relation_mentions)))
    main_annotations.update(relevant_annotations)
    main_annotations.update({"Relation_Mentions": relation_mentions})
    return main_annotations

def _fetch_pubtator_chunk(pmids_chunk, max_retries=3, rate_limiter: RateLimiter = None):
    """
    Fetch PubTator3 data for a single chunk of PMIDs.
    
    Args:
        pmids_chunk (list): List of PMID strings (should be <= batch_size)
        max_retries (int): Maximum number of retry attempts for failed requests
        rate_limiter: Rate limiter to control request frequency
        
    Returns:
        list: List of dicts with keys 'pmid', 'conditions', 'interventions'
    """
    if not pmids_chunk:
        return []
    
    if rate_limiter is not None:
        rate_limiter.wait_if_needed()
    
    # Join PMIDs with commas for batch request
    pmids_str = ",".join(str(pmid) for pmid in pmids_chunk)
    url = f"{PUBTATOR3_FULLTEXT_URL}?pmids={pmids_str}"
        
    for attempt in range(max_retries):
        try:
            # Add delay to avoid rate limiting (except for first attempt)
            if attempt > 0:
                print(f"Retry attempt {attempt + 1} after {rate_limiter.min_interval * attempt} seconds...")
                time.sleep(rate_limiter.min_interval * attempt)
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # Raises an exception for bad status codes
            
            # Parse JSON response
            data = response.json()
            data = data['PubTator3']
            
            results = []
            
            # Process each publication in the response
            for pub_data in data:
                pmid = pub_data.get("pmid") or str(pub_data.get("id", "unknown"))
                
                try:
                    data = _parse_pubtator_response_to_get_content_and_attributes_and_relations(pub_data)
                    data["PMID"] = pmid
                    results.append(data)
                                    
                except Exception as e:
                    print(f"  Error parsing PMID {pmid}: {e}")
                    # Still add empty result to maintain order
                    results.append({
                        "PMID": pmid,
                        "error": str(e)
                    })
            
            print(f"Successfully processed {len(results)} publications from chunk")
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                print(f"Failed to fetch data for chunk after {max_retries} attempts")
                # Return empty results for all PMIDs in this chunk
                return [{
                    "PMID": pmid,
                    "error": f"API request failed: {e}"
                } for pmid in pmids_chunk]
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return [{
                    "PMID": pmid,
                    "error": f"JSON decode error: {e}"
                } for pmid in pmids_chunk]
        except Exception as e:
            print(f"Unexpected error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return [{
                    "PMID": pmid,
                    "error": f"Unexpected error: {e}"
                } for pmid in pmids_chunk]


def pubtator_api_fetch_paper_annotations(pmids, batch_size=50, max_retries=3, max_requests_per_second=3.0):
    """
    Fetch PubTator3 data for a batch of PMIDs and return parsed results.
    
    Args:
        pmids (list): List of PMID strings
        batch_size (int): Maximum number of PMIDs per API request (default: 50)
        max_retries (int): Maximum number of retry attempts for failed requests
        max_requests_per_second (float): Maximum number of requests per second

    Returns:
        list: List of dicts with keys 'PMID', 'Disease', 'Drug', 'Relation_Mentions', etc.
    """
    if not pmids:
        return []
    
    rate_limiter = RateLimiter(max_requests_per_second)
    all_results = []

    if not pmids:
        print("All PMIDs already processed!")
        return all_results
    
    # Split remaining PMIDs into chunks to avoid URL length limits
    for i in tqdm(range(0, len(pmids), batch_size)):
        chunk = pmids[i:i + batch_size]
        chunk_results = _fetch_pubtator_chunk(chunk, max_retries, rate_limiter)
        all_results.extend(chunk_results)
    
    print(f"Total results: {len(all_results)}")
    return all_results


def pubtator_api_search_papers(text, page=1, max_retries=3, max_requests_per_second=3.0):
    """
    Search for relevant PubMed articles using entity IDs or relation queries.
    
    Args:
        text (str): Query text in the format: "relations:{relation}|{entityID_1}|{entityID_2}"
                   Example: "relations:treat|@CHEMICAL_Doxorubicin|@DISEASE_Neoplasms"
        page (int): Page number for pagination (default: 1)
        max_retries (int): Maximum number of retry attempts for failed requests (default: 3)
        max_requests_per_second (float): Maximum number of requests per second (default: 3.0)
    
    Returns:
        dict: Response containing search results with the following structure:
            {
                "results": [
                    {
                        "entityId": str,
                        "entityName": str,
                        "relationType": str,
                        "relatedEntityId": str,
                        "relatedEntityName": str
                    },
                    ...
                ]
            }
        Returns None if the request fails after all retries.
    
    Example:
        >>> results = pubtator_api_search_papers(
        ...     text="relations:treat|@CHEMICAL_Doxorubicin|@DISEASE_Neoplasms",
        ...     page=1
        ... )
    """
    rate_limiter = RateLimiter(max_requests_per_second)
    
    # Prepare query parameters
    params = {
        "text": text,
        "page": page
    }
    
    for attempt in range(max_retries):
        try:
            # Apply rate limiting
            rate_limiter.wait_if_needed()
            
            # Add delay for retry attempts
            if attempt > 0:
                delay = rate_limiter.min_interval * attempt
                print(f"Retry attempt {attempt + 1} after {delay} seconds...")
                time.sleep(delay)
            
            # Make the GET request
            response = requests.get(PUBTATOR3_SEARCH_URL, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse and return the JSON response
            data = response.json()
            print(f"Successfully retrieved {len(data.get('results', []))} results")
            results = data.get('results', [])
            results_df = pd.DataFrame(results)
            results_df = results_df[['pmid','pmcid','title','journal','date','text_hl']]
            results_df.rename(columns={'pmid': 'PMID', 'pmcid': 'PMCID', 'title': 'Title', 'journal': 'Journal', 'date': 'Date', 'text_hl': 'Highlighted_Text'}, inplace=True)            
            return results_df
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error (attempt {attempt + 1}/{max_retries}): {e}")
            if e.response.status_code == 400:
                print(f"Bad request - invalid input parameters: {params}")
                return None
            if attempt == max_retries - 1:
                print(f"Failed to fetch data after {max_retries} attempts")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                print(f"Failed to fetch data after {max_retries} attempts")
                return None
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                print(f"Failed to parse response after {max_retries} attempts")
                return None
                
        except Exception as e:
            print(f"Unexpected error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                print(f"Unexpected error after {max_retries} attempts")
                return None
    
    return None

