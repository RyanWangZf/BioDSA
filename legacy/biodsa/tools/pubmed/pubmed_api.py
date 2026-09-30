from typing import List, Dict, Any
import os
import requests
import time
import xml.etree.ElementTree as ET
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from xml.etree import ElementTree
import pandas as pd
from typing import Optional
import re

from .ratelimiter import RateLimiter

PUBMED_BASE_URL = "https://pubmed.ncbi.nlm.nih.gov/"
PUBMED_EU_UTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_API_KEY = os.environ.get("PUBMED_API_KEY")
PMID_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term="
PUBMED_EFETCH_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id="
BATCH_REQUEST_SIZE = 100

__all__ = [
    "pubmed_api_get_paper_references",
    "get_pubmed_articles",
    "fetch_paper_content_by_pmid",
    "pubmed_api_search_papers", # search papers by boolean query or relation query
    "extract_relevant_sections", # extract relevant sections from text based on grep pattern
    "format_paper_content_output", # format paper content for display
]

# ===============================
# Helper functions
# ===============================
def extract_relevant_sections(text: str, grep_pattern: str, context_chars: int = 1000) -> List[Dict[str, Any]]:
    """
    Extract sections from text that match the grep pattern with surrounding context.

    Args:
        text: The full text to search in
        grep_pattern: Regex pattern or keywords to search for
        context_chars: Number of characters to include before and after each match

    Returns:
        List of dictionaries containing match info and surrounding context
    """
    if not text or not grep_pattern:
        return []

    matches = []

    # Try as regex first, fall back to literal search
    try:
        # Case-insensitive search
        pattern = re.compile(grep_pattern, re.IGNORECASE | re.DOTALL)
        for match in pattern.finditer(text):
            start, end = match.span()

            # Calculate context boundaries
            context_start = max(0, start - context_chars)
            context_end = min(len(text), end + context_chars)

            # Find natural boundaries (sentence/paragraph breaks) for cleaner context
            # Look for sentence breaks before the match
            pre_context = text[context_start:start]
            sentence_breaks = [m.end() for m in re.finditer(r'[.!?]\s+', pre_context)]
            if sentence_breaks:
                context_start = context_start + sentence_breaks[-1]

            # Look for sentence breaks after the match
            post_context = text[end:context_end]
            sentence_breaks = [m.start() for m in re.finditer(r'[.!?]\s+', post_context)]
            if sentence_breaks:
                context_end = end + sentence_breaks[0] + 2  # Include the punctuation and space

            context = text[context_start:context_end].strip()
            matched_text = match.group(0)

            matches.append({
                'matched_text': matched_text,
                'context': context,
                'start_pos': start,
                'end_pos': end
            })
    except re.error:
        # If regex fails, do case-insensitive literal search
        search_term = grep_pattern.lower()
        text_lower = text.lower()
        start = 0

        while True:
            pos = text_lower.find(search_term, start)
            if pos == -1:
                break

            end = pos + len(search_term)
            context_start = max(0, pos - context_chars)
            context_end = min(len(text), end + context_chars)

            # Find natural boundaries
            pre_context = text[context_start:pos]
            sentence_breaks = [m.end() for m in re.finditer(r'[.!?]\s+', pre_context)]
            if sentence_breaks:
                context_start = context_start + sentence_breaks[-1]

            post_context = text[end:context_end]
            sentence_breaks = [m.start() for m in re.finditer(r'[.!?]\s+', post_context)]
            if sentence_breaks:
                context_end = end + sentence_breaks[0] + 2

            context = text[context_start:context_end].strip()
            matched_text = text[pos:end]

            matches.append({
                'matched_text': matched_text,
                'context': context,
                'start_pos': pos,
                'end_pos': end
            })

            start = end

    # Remove duplicate matches that overlap significantly
    unique_matches = []
    for match in matches:
        is_duplicate = False
        for existing in unique_matches:
            # If contexts overlap by more than 80%, consider it a duplicate
            overlap_start = max(match['start_pos'], existing['start_pos'])
            overlap_end = min(match['end_pos'], existing['end_pos'])
            overlap_len = max(0, overlap_end - overlap_start)
            match_len = match['end_pos'] - match['start_pos']

            if overlap_len > 0.8 * match_len:
                is_duplicate = True
                break

        if not is_duplicate:
            unique_matches.append(match)

    return unique_matches

def format_paper_content_output(result: Dict[str, Any], filter_keywords: str = "") -> str:
    """
    Format paper content result into a readable string output.
    
    Args:
        result: Dictionary containing paper content from fetch_paper_content_by_pmid
        filter_keywords: Optional keywords to filter/highlight in the full text
        
    Returns:
        Formatted string with paper metadata, abstract, and filtered content
    """
    output_parts = []
    output_parts.append(f"PMID: {result['pmid']}")
    output_parts.append("=" * 80)
    
    if result.get('error'):
        output_parts.append(f"ERROR: {result['error']}")
    
    if result.get('title'):
        output_parts.append(f"\nTITLE:\n{result['title']}")
    
    if result.get('abstract'):
        output_parts.append(f"\nABSTRACT:\n{result['abstract']}")
    
    has_full = result.get('has_full_text', False)
    source = result.get('source', 'none')
    
    if has_full:
        source_name = {'pmc': 'PMC Open Access', 'pubtator': 'PubTator3', 'none': 'None'}.get(source, source)
        output_parts.append(f"\nFULL TEXT AVAILABLE: Yes (Source: {source_name})")
    else:
        output_parts.append(f"\nFULL TEXT AVAILABLE: No (Only abstract available)")
    
    if result.get('passages'):
        output_parts.append(f"AVAILABLE SECTIONS: {', '.join(result['passages'])}")
    
    # Apply filter if full content is available
    if result.get('full_content') and filter_keywords:
        full_content = result['full_content']
        relevant_sections = extract_relevant_sections(full_content, filter_keywords, context_chars=1000)
        
        if relevant_sections:
            output_parts.append(f"\n{'='*80}")
            output_parts.append(f"FILTER APPLIED: Found {len(relevant_sections)} matching section(s) for: '{filter_keywords}'")
            output_parts.append(f"{'='*80}")
            
            for i, section in enumerate(relevant_sections, 1):
                output_parts.append(f"\n--- MATCH {i}/{len(relevant_sections)} ---")
                matched_preview = section['matched_text'][:100] + ('...' if len(section['matched_text']) > 100 else '')
                output_parts.append(f'Matched text: "{matched_preview}"')
                output_parts.append(f"\nContext (±1000 chars):")
                output_parts.append(section['context'])
                output_parts.append("")
        else:
            output_parts.append(f"\n{'='*80}")
            output_parts.append(f"FILTER WARNING: No matches found for keywords: '{filter_keywords}'")
            output_parts.append(f"{'='*80}")
            output_parts.append("\nTip: Try broader keywords or alternative terms.")
            output_parts.append("No content to display as filter produced no matches.")
    elif has_full and not result.get('full_content'):
        output_parts.append(f"\nWARNING: Full text was retrieved but content is empty.")
    elif filter_keywords and not has_full:
        output_parts.append(f"\nNOTE: Only abstract available (no full text), filter cannot be applied to full content.")
    
    return "\n".join(output_parts)

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

def _parse_xml_recursively(element):
    child_dict = {}
    if element.text and element.text.strip():
        child_dict['text'] = element.text.strip()

    for child in element:
        if child.tag not in child_dict:
            child_dict[child.tag] = []
        child_dict[child.tag].append(_parse_xml_recursively(child))

    # Simplify structure when there's only one child or text
    for key in child_dict:
        if len(child_dict[key]) == 1:
            child_dict[key] = child_dict[key][0]
        elif not child_dict[key]:
            del child_dict[key]

    return child_dict

def _parse_article_xml_to_dict(article):
    results = {}
    dict_obj  = _parse_xml_recursively(article)

    # get article information
    article = dict_obj.get("MedlineCitation", {}).get("Article", {})

    # get the fields correspondingly
    results['PMID'] = dict_obj.get('MedlineCitation', {}).get('PMID', {}).get('text', '')

    # get the journal title
    journal = article.get('Journal', {}).get('Title', {}).get('text', '')
    results["Journal"] = journal

    # get pub date
    date = article.get('Journal', {}).get('JournalIssue', {})
    publication_year = date.get('PubDate', {}).get('Year', {}).get('text', '')
    publication_month = date.get('PubDate', {}).get('Month', {}).get('text', '')
    publication_day = date.get('PubDate', {}).get('Day', {}).get('text', '')
    results['Year'] = publication_year
    results['Month'] = publication_month
    results['Day'] = publication_day

    # get the title
    article_title = article.get('ArticleTitle', {}).get('text', '')
    results['Title'] = article_title

    # publication type
    publication_type = article.get('PublicationTypeList', {}).get('PublicationType', [])
    if len(publication_type) > 0:
        pubtype_list = []
        if isinstance(publication_type, dict):
            publication_type = [publication_type]
        for pt in publication_type:
            if isinstance(pt, dict):
                pubtype_list.append(pt.get('text', ''))
            else:
                pubtype_list.append(pt)
        publication_type = ", ".join(pubtype_list)
    else:
        publication_type = ""
    results['Publication Type'] = publication_type

    # authors
    author_names = article.get('AuthorList', {}).get('Author', [])
    authors = []
    if len(author_names) > 0:
        if isinstance(author_names, dict):
            author_names = [author_names]
        for author in author_names:
            last_name = author.get('LastName', {}).get('text', '')
            first_name = author.get('ForeName', {}).get('text', '')
            authors.append(f"{first_name} {last_name}")
        authors = ", ".join(authors)
    else:
        authors = ""
    results['Authors'] = authors

    # get the abstract
    abstracts = article.get('Abstract', {}).get('AbstractText', [])
    abstract_texts = []
    if len(abstracts) > 0:
        if isinstance(abstracts, dict):
            abstracts = [abstracts]
        for abstract in abstracts:
            if isinstance(abstract, dict):
                abstract_text = abstract.get('text', "")
            else:
                abstract_text = abstract
            abstract_texts.append(abstract_text)
        abstract_texts = "\n".join(abstract_texts)
    else:
        abstract_texts = ""
    results['Abstract'] = abstract_texts
    return results

def _parse_book_xml_to_dict(book):
    results = {}
    dict_obj  = _parse_xml_recursively(book)
    book = dict_obj.get("BookDocument")

    # get book information
    pmid = book.get("PMID", {}).get("text", "")
    results['PMID'] = pmid

    # get the book title
    book_title = book.get("Book", {}).get("BookTitle", {}).get("text", "")
    results['Title'] = book_title

    # pub date
    date = book.get("Book", {}).get('PubDate', {})
    publication_year = date.get('Year', {}).get('text', '')
    publication_month = date.get('Month', {}).get('text', '')
    publication_day = date.get('Day', {}).get('text', '')
    results['Year'] = publication_year
    results['Month'] = publication_month
    results['Day'] = publication_day

    # authors
    author_names = book.get('AuthorList', {}).get('Author', [])
    authors = []
    if len(author_names) > 0:
        if isinstance(author_names, dict):
            author_names = [author_names]
        for author in author_names:
            last_name = author.get('LastName', {}).get('text', '')
            first_name = author.get('ForeName', {}).get('text', '')
            authors.append(f"{first_name} {last_name}")
        authors = ", ".join(authors)
    else:
        authors = ""
    results['Authors'] = authors

    # get the abstract
    abstracts = book.get('Abstract', {}).get('AbstractText', [])
    abstract_texts = []
    if len(abstracts) > 0:
        if isinstance(abstracts, dict):
            abstracts = [abstracts]
        for abstract in abstracts:
            if isinstance(abstract, dict):
                abstract_text = abstract.get('text', "")
            else:
                abstract_text = abstract
            abstract_texts.append(abstract_text)
        abstract_texts = "\n".join(abstract_texts)
    else:
        abstract_texts = ""

    # get pub type
    publication_type = book.get('PublicationType', {}).get('text', '')
    results['Publication Type'] = publication_type

def _retrieve_abstract_from_efetch(pmids, api_key) -> pd.DataFrame:
    """Retrieve the abstract from the efetch API."""
    all_abstracts = []
    for i in range(0, len(pmids), BATCH_REQUEST_SIZE):
        pmid_subset = pmids[i:i+BATCH_REQUEST_SIZE]
        pmid_str = ','.join(pmid_subset)
        query = PUBMED_EFETCH_BASE_URL + pmid_str + "&retmode=xml"
        if api_key is not None:
            query += f"&api_key={api_key}"
        response = requests.get(query, timeout=30)
        if response.status_code != 200:
            continue
        else:
            response = response.text
            tree = ET.fromstring(response)
            articles = tree.findall(".//PubmedArticle")
            for article in articles:
                try:
                    article_dict = _parse_article_xml_to_dict(article)
                    all_abstracts.append(article_dict)
                except:
                    continue

            # for books
            books = tree.findall(".//PubmedBookArticle")
            if len(books) > 0:
                for book in books:
                    try:
                        book_dict = _parse_book_xml_to_dict(book)
                        all_abstracts.append(book_dict)
                    except:
                        pass

    all_abstracts = [x for x in all_abstracts if x is not None]
    if len(all_abstracts) > 0:
        output_abstracts = pd.DataFrame.from_records(all_abstracts)
    else:
        output_abstracts = None
    return output_abstracts

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
    

    # get all the target_pmid and retrieve their title
    if len(all_results) > 0:
        all_results = pd.DataFrame(all_results)
        target_pmids = all_results['target_pmid'].unique().tolist()
        # get the content of the target_pmids
        target_pmids_content = _retrieve_abstract_from_efetch(target_pmids, PUBMED_API_KEY)
        # add the content to the all_results
        target_pmids_content = target_pmids_content[['PMID', 'Title', "Year"]]
        target_pmids_content.columns = ['target_pmid', 'target_title', "target_year"]
        all_results = pd.merge(all_results, target_pmids_content, on='target_pmid', how='left')
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

def pubmed_api_search_papers(
    boolean_query_text: str,
    top_k: int = 10,
) -> Optional[pd.DataFrame]:
    """
    Search for papers using PubMed API.
    
    Args:
        boolean_query_text: Boolean query text for PubMed search.
        top_k: Maximum number of results to return.
    
    Returns:
        Optional[pd.DataFrame]: DataFrame containing search results.
    """    
    query_url = f"{PMID_BASE_URL}{boolean_query_text}&retmax={top_k}&retmode=json"
    if PUBMED_API_KEY:
        query_url += f"&api_key={PUBMED_API_KEY}"
    try:
        response = requests.get(query_url, timeout=30)
        response.raise_for_status()
        response_dict = response.json()
        pmid_list = response_dict['esearchresult']['idlist']
        total_count = response_dict['esearchresult']['count']
    except requests.RequestException as e:
        print(f"Error searching papers: {e}")
        return None
    

    if pmid_list is None or len(pmid_list) == 0:
        return None
    
    # get the paper details for pmids
    paper_details = _retrieve_abstract_from_efetch(pmid_list, PUBMED_API_KEY)
    if paper_details is None or len(paper_details) == 0:
        return None

    # PMID, Title,
    return paper_details # it is a dataframe
