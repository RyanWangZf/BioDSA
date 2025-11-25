import os
import json
import pdb
from typing import List, Dict, Optional, Literal, Union, TypedDict
from typing_extensions import Set
import requests
import time
import pandas as pd
from tqdm import tqdm
from collections import defaultdict

from .ratelimiter import RateLimiter
from xml.etree import ElementTree

PUBTATOR3_BASE_URL = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api"
PUBTATOR3_SEARCH_URL = f"{PUBTATOR3_BASE_URL}/search/"
PUBTATOR3_FULLTEXT_URL = f"{PUBTATOR3_BASE_URL}/publications/export/biocjson"
PUBTATOR3_AUTOCOMPLETE_URL = f"{PUBTATOR3_BASE_URL}/entity/autocomplete/"
PUBTATOR3_RELATIONS_URL = f"{PUBTATOR3_BASE_URL}/relations"
PUBMED_EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Type definitions
EntityType = Literal["GENE", "DISEASE", "CHEMICAL", "VARIANT", "SPECIES", "CELLLINE"]
RelationType = Literal[
    "ASSOCIATE", "CAUSE", "COMPARE", "COTREAT", "DRUG_INTERACT", 
    "INHIBIT", "INTERACT", "NEGATIVE_CORRELATE", "POSITIVE_CORRELATE", 
    "PREVENT", "STIMULATE", "TREAT", "ANY"
]

# Typed dictionary for relation parameter
class RelationQuery(TypedDict):
    """Type definition for relation-based search."""
    relation_type: RelationType
    entity1: Union[str, EntityType]  # Entity ID (starting with @) or EntityType
    entity2: Union[str, EntityType]  # Entity ID (starting with @) or EntityType

# Valid entity types for PubTator3
VALID_ENTITY_TYPES = {
    "GENE", "DISEASE", "CHEMICAL", "VARIANT", "SPECIES", "CELLLINE"
}

# Valid relation types for PubTator3
VALID_RELATION_TYPES = {
    "ASSOCIATE", "CAUSE", "COMPARE", "COTREAT", "DRUG_INTERACT", 
    "INHIBIT", "INTERACT", "NEGATIVE_CORRELATE", "POSITIVE_CORRELATE", 
    "PREVENT", "STIMULATE", "TREAT", "ANY"
}


# ===============================
# Helper functions
# ===============================
def _clean_query_for_pubmed(boolean_query_text: str) -> str:
    """
    Clean PubTator-specific syntax from query to make it compatible with PubMed.
    
    Removes:
    - Entity IDs like @CHEMICAL_remdesivir, @DISEASE_COVID_19
    - Extracts readable terms from entity IDs
    
    Args:
        boolean_query_text: Original query with PubTator syntax
        
    Returns:
        Cleaned query suitable for PubMed E-utilities
    """
    import re
    
    # Extract entity names from @TYPE_name format
    # e.g., @CHEMICAL_remdesivir -> remdesivir
    # e.g., @DISEASE_COVID_19 -> COVID-19
    cleaned = re.sub(r'@[A-Z_]+_([A-Za-z0-9_\-]+)', r'\1', boolean_query_text)
    
    # Replace underscores with spaces in extracted entity names
    cleaned = re.sub(r'([A-Za-z])_([A-Za-z])', r'\1 \2', cleaned)
    
    # Keep AND/OR operators but make them compatible
    cleaned = cleaned.replace(' AND ', ' AND ')
    cleaned = cleaned.replace(' OR ', ' OR ')
    
    # Remove extra spaces
    cleaned = ' '.join(cleaned.split())
    
    return cleaned


def _fallback_to_pubmed_search(boolean_query_text: str, max_results: int = 10) -> Optional[pd.DataFrame]:
    """
    Fallback to PubMed E-utilities when PubTator returns no results.
    
    Args:
        boolean_query_text: Original query (will be cleaned for PubMed)
        max_results: Maximum number of results to return
        
    Returns:
        DataFrame with search results or None if search fails
    """
    try:
        # Clean the query for PubMed
        pubmed_query = _clean_query_for_pubmed(boolean_query_text)
        print(f"Cleaned query for PubMed: {pubmed_query}")
        
        # Step 1: Search for PMIDs
        search_url = f"{PUBMED_EUTILS_BASE_URL}/esearch.fcgi"
        search_params = {
            "db": "pubmed",
            "term": pubmed_query,
            "retmode": "xml",
            "retmax": str(max_results),
            "sort": "relevance"
        }
        
        search_response = requests.get(search_url, params=search_params, timeout=30)
        search_response.raise_for_status()
        
        search_results = ElementTree.fromstring(search_response.content)
        pmids = [id_tag.text for id_tag in search_results.findall('.//Id')]
        
        if not pmids:
            print("No results from PubMed E-utilities either")
            return None
        
        print(f"Found {len(pmids)} results from PubMed E-utilities")
        
        # Step 2: Fetch article details
        fetch_url = f"{PUBMED_EUTILS_BASE_URL}/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml"
        }
        
        fetch_response = requests.get(fetch_url, params=fetch_params, timeout=30)
        fetch_response.raise_for_status()
        
        articles_tree = ElementTree.fromstring(fetch_response.content)
        
        # Step 3: Parse articles
        results = []
        for article in articles_tree.findall('.//PubmedArticle'):
            pmid_elem = article.find('.//PMID')
            pmid = pmid_elem.text if pmid_elem is not None else None
            
            title_elem = article.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else "No title available"
            
            # Try to find journal
            journal_elem = article.find('.//Journal/Title')
            if journal_elem is None:
                journal_elem = article.find('.//Journal/ISOAbbreviation')
            journal = journal_elem.text if journal_elem is not None else "Unknown"
            
            # Try to find publication date
            pub_date = article.find('.//PubDate')
            date = "Unknown"
            if pub_date is not None:
                year = pub_date.find('Year')
                month = pub_date.find('Month')
                if year is not None:
                    date = year.text
                    if month is not None:
                        date = f"{year.text}-{month.text}"
            
            # Get abstract (concatenate multiple abstract text elements)
            abstract_texts = []
            for abstract_elem in article.findall('.//Abstract/AbstractText'):
                label = abstract_elem.get('Label', '')
                text = abstract_elem.text if abstract_elem is not None else ""
                if text:
                    if label:
                        abstract_texts.append(f"{label}: {text}")
                    else:
                        abstract_texts.append(text)
            
            highlighted_text = "\n".join(abstract_texts) if abstract_texts else title
            
            results.append({
                'PMID': pmid,
                'PMCID': None,  # Not available from efetch
                'Title': title,
                'Journal': journal,
                'Date': date,
                'Highlighted_Text': highlighted_text
            })
        
        return pd.DataFrame(results)
        
    except Exception as e:
        print(f"PubMed fallback search failed: {e}")
        return None


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
                    if infons.get("type") is not None and infons.get("name") is not None:
                        main_annotations[infons.get("type")].add(infons['name'])

            if passage_type in ["abstract"]:
                for annotation in annotations:
                    infons = annotation.get("infons", {})
                    if infons.get("type") is not None and infons.get("name") is not None:
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
                    import traceback
                    traceback.print_exc()
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


# ===============================
# Main functions
# ===============================

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


def pubtator_api_search_papers(
    boolean_query_text: Optional[str] = None,
    relation_query: Optional[RelationQuery] = None,
    page: int = 1,
    max_retries: int = 3,
    max_requests_per_second: float = 3.0
) -> Optional[pd.DataFrame]:
    """
    Search for relevant PubMed articles using boolean queries or relation queries.
    
    Args:
        boolean_query_text (Optional[str]): Boolean query with entity IDs / entity types /raw entity text, keywords, AND/OR operators,
            and parentheses for grouping. This is the raw text format supported by PubTator3.
            
            Supported syntax:
            - Entity IDs: @CHEMICAL_remdesivir, @DISEASE_Neoplasms
            - Boolean operators: AND, OR
            - Grouping: Use parentheses for complex queries
            - Free-text keywords: Can be mixed with entity IDs
            
            Examples:
            - Single entity: "@CHEMICAL_remdesivir"
            - Multiple entities: "@CHEMICAL_Doxorubicin AND @DISEASE_Neoplasms"
            - Complex boolean: "(@DISEASE_COVID_19 AND complications) OR @DISEASE_Post_Acute_COVID_19_Syndrome"
            - Mixed: "@CHEMICAL_remdesivir AND (efficacy OR effectiveness)"
            - Multiple drugs: "(@CHEMICAL_Doxorubicin OR @CHEMICAL_Cisplatin) AND @DISEASE_Neoplasms"
        
        relation_query  (Optional[RelationQuery]): Relation-based search dictionary with required keys:
            - 'relation_type' (RelationType): One of the valid relation types:
                ASSOCIATE, CAUSE, COMPARE, COTREAT, DRUG_INTERACT, INHIBIT, INTERACT,
                NEGATIVE_CORRELATE, POSITIVE_CORRELATE, PREVENT, STIMULATE, TREAT, ANY
            - 'entity1' (str): First entity, either:
                * Entity ID (e.g., "@CHEMICAL_Doxorubicin")
                * Entity type (EntityType): GENE, DISEASE, CHEMICAL, VARIANT, SPECIES, CELLLINE
            - 'entity2' (str): Second entity, either:
                * Entity ID (e.g., "@DISEASE_Neoplasms")
                * Entity type (EntityType): GENE, DISEASE, CHEMICAL, VARIANT, SPECIES, CELLLINE
        
        page (int): Page number for pagination (default: 1)
        max_retries (int): Maximum number of retry attempts for failed requests (default: 3)
        max_requests_per_second (float): Maximum number of requests per second (default: 3.0)
    
    Returns:
        Optional[pd.DataFrame]: DataFrame containing search results with columns:
            - PMID: PubMed ID
            - PMCID: PubMed Central ID
            - Title: Article title
            - Journal: Journal name
            - Date: Publication date
            - Highlighted_Text: Highlighted text snippets
        Returns None if the request fails after all retries.
    
    Relation Types:
        - ASSOCIATE: General association between entities
        - CAUSE: Entity1 causes entity2 (e.g., chemical-induced diseases)
        - COMPARE: Effect comparison of two chemicals/drugs
        - COTREAT: Two or more chemicals/drugs administered together
        - DRUG_INTERACT: Pharmacodynamic interaction between two chemicals
        - INHIBIT: Negative correlation (e.g., disease-gene, chemical-variant)
        - INTERACT: Physical interaction (e.g., protein-binding, gene-gene)
        - NEGATIVE_CORRELATE: Negative correlation (e.g., chemical-gene co-expression)
        - POSITIVE_CORRELATE: Positive correlation (e.g., chemical-gene co-expression)
        - PREVENT: Prevention relationship (e.g., variant-disease)
        - STIMULATE: Stimulation relationship (e.g., disease-gene, disease-variant)
        - TREAT: Chemical/drug treats a disease
        - ANY: Any relation type
    
    Examples:
        # Simple boolean query - single entity
        >>> results = pubtator_api_search_papers(
        ...     boolean_query_text="@CHEMICAL_remdesivir"
        ... )
        
        # Boolean query - multiple entities with AND
        >>> results = pubtator_api_search_papers(
        ...     boolean_query_text="@CHEMICAL_Doxorubicin AND @DISEASE_Neoplasms"
        ... )
        
        # Complex boolean query with OR and parentheses
        >>> results = pubtator_api_search_papers(
        ...     boolean_query_text="(@DISEASE_COVID_19 AND complications) OR @DISEASE_Post_Acute_COVID_19_Syndrome"
        ... )
        
        # Boolean query with mixed entities and keywords
        >>> results = pubtator_api_search_papers(
        ...     boolean_query_text="@CHEMICAL_remdesivir AND (efficacy OR effectiveness)"
        ... )
        
        # Relation search with two entity IDs
        >>> results = pubtator_api_search_papers(
        ...     relation_query={
        ...         'relation_type': 'TREAT',
        ...         'entity1': '@CHEMICAL_Doxorubicin',
        ...         'entity2': '@DISEASE_Neoplasms'
        ...     }
        ... )
        
        # Relation search with entity ID and entity type
        >>> results = pubtator_api_search_papers(
        ...     relation_query={
        ...         'relation_type': 'ANY',
        ...         'entity1': '@CHEMICAL_Doxorubicin',
        ...         'entity2': 'DISEASE'
        ...     }
        ... )
        
        # Relation search with two entity types
        >>> results = pubtator_api_search_papers(
        ...     relation_query={
        ...         'relation_type': 'INTERACT',
        ...         'entity1': 'GENE',
        ...         'entity2': 'CHEMICAL'
        ...     }
        ... )
    """
    # Build query text based on parameters
    query_text = None
    
    if boolean_query_text is not None and relation_query is not None:
        raise ValueError("Cannot specify both boolean_query_text and relation. Choose one search mode.")
    
    if boolean_query_text is not None:
        # Boolean query mode - use as-is
        if not isinstance(boolean_query_text, str):
            raise ValueError("boolean_query_text must be a string")
        if not boolean_query_text.strip():
            raise ValueError("boolean_query_text cannot be empty")
        query_text = boolean_query_text
        
    elif relation_query is not None:
        # Relation-based search - strict validation
        if not isinstance(relation_query, dict):
            raise ValueError("relation must be a dictionary")
        
        required_keys = {'relation_type', 'entity1', 'entity2'}
        if not required_keys.issubset(relation_query.keys()):
            raise ValueError(f"relation dict must contain keys: {required_keys}")
        
        # Validate relation type
        relation_type = relation_query['relation_type']
        if relation_type not in VALID_RELATION_TYPES:
            raise ValueError(
                f"Invalid relation_type '{relation_type}'. "
                f"Must be one of: {', '.join(sorted(VALID_RELATION_TYPES))}"
            )
        
        # Validate entities (can be entity ID or entity type)
        entity1 = relation_query['entity1']
        entity2 = relation_query['entity2']
        
        # Check if entity is a type (not an ID), validate it
        if not entity1.startswith('@') and entity1 not in VALID_ENTITY_TYPES:
            raise ValueError(
                f"Invalid entity1 '{entity1}'. "
                f"Must be an entity ID (starting with @) or one of: {', '.join(sorted(VALID_ENTITY_TYPES))}"
            )
        
        if not entity2.startswith('@') and entity2 not in VALID_ENTITY_TYPES:
            raise ValueError(
                f"Invalid entity2 '{entity2}'. "
                f"Must be an entity ID (starting with @) or one of: {', '.join(sorted(VALID_ENTITY_TYPES))}"
            )
        
        query_text = f"relations:{relation_type}|{entity1}|{entity2}"
    else:
        raise ValueError("Must provide either boolean_query_text or relation")
    
    rate_limiter = RateLimiter(max_requests_per_second)
    
    # Prepare query parameters
    params = {
        "text": query_text,
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
            results = data.get('results', [])
            results_df = pd.DataFrame(results)
            if len(results_df) > 0:
                results_df = results_df[['pmid','pmcid','title','journal','date','text_hl']]
                results_df.rename(columns={'pmid': 'PMID', 'pmcid': 'PMCID', 'title': 'Title', 'journal': 'Journal', 'date': 'Date', 'text_hl': 'Highlighted_Text'}, inplace=True)
                # try to parse the date to extract the year from it
                # Convert Date column to datetime and extract year
                results_df['Year'] = pd.to_datetime(results_df['Date'], errors='coerce').dt.year
                return results_df
            else:
                return None
            
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


def pubtator_api_find_entities(
    query_text: str,
    concept_type: Optional[EntityType] = None,
    limit: int = 10,
    max_retries: int = 3,
    max_requests_per_second: float = 3.0
) -> Optional[pd.DataFrame]:
    """
    Find and autocomplete entity names in the PubTator3 database using a query text.
    
    This function provides entity name suggestions/autocomplete based on partial text input.
    Useful for finding entity IDs and normalized names for biomedical entities.
    
    Args:
        query_text (str): Search query text (partial entity name).
            Example: "remdesivir", "COVID", "BRCA1"
        
        concept_type (Optional[EntityType]): Restrict results to a specific entity type.
            One of: GENE, DISEASE, CHEMICAL, VARIANT, SPECIES, CELLLINE
            If None, searches across all entity types.
        
        limit (int): Maximum number of results to return (default: 10)
        
        max_retries (int): Maximum number of retry attempts for failed requests (default: 3)
        max_requests_per_second (float): Maximum number of requests per second (default: 3.0)
    
    Returns:
        Optional[pd.DataFrame]: DataFrame containing entity suggestions with columns:
            - EntityID: PubTator3 entity identifier (e.g., "@CHEMICAL_D000068698")
            - Name: Normalized entity name
            - Type: Entity type (GENE, DISEASE, CHEMICAL, etc.)
            - Score: Relevance score (if available)
        Returns None if the request fails after all retries.
    
    Examples:
        # Search for chemicals matching "remdesivir"
        >>> results = pubtator_api_find_entities(
        ...     query_text="remdesivir",
        ...     concept_type="CHEMICAL",
        ...     limit=5
        ... )
        
        # Search for diseases matching "COVID"
        >>> results = pubtator_api_find_entities(
        ...     query_text="COVID",
        ...     concept_type="DISEASE",
        ...     limit=10
        ... )
        
        # Search across all entity types
        >>> results = pubtator_api_find_entities(
        ...     query_text="BRCA1",
        ...     limit=10
        ... )
        
        # Search for genes
        >>> results = pubtator_api_find_entities(
        ...     query_text="insulin",
        ...     concept_type="GENE",
        ...     limit=5
        ... )
    """
    if not query_text or not query_text.strip():
        raise ValueError("query_text cannot be empty")
    
    if concept_type is not None and concept_type not in VALID_ENTITY_TYPES:
        raise ValueError(
            f"Invalid concept_type '{concept_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ENTITY_TYPES))}"
        )
    
    rate_limiter = RateLimiter(max_requests_per_second)
    
    # Prepare query parameters
    params = {
        "query": query_text.strip(),
        "limit": limit
    }
    
    # Add concept type if specified
    if concept_type is not None:
        params["concept"] = concept_type
    
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
            response = requests.get(PUBTATOR3_AUTOCOMPLETE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            
            if not data or len(data) == 0:
                print(f"No entities found for query: '{query_text}'")
                return pd.DataFrame(columns=['EntityID', 'Name', 'Type', 'Score'])
            
            print(f"Successfully retrieved {len(data)} entity suggestions")
            
            # Parse results into a structured format
            results = []
            for item in data:
                # Extract entity information
                entity_id = item.get('_id', '')
                name = item.get('name', '')
                entity_type = item.get('biotype', '')
                source_db = item.get('db', '')
                source_db_id = item.get('db_id', '')
                
                results.append({
                    'PubTator3_EntityID': entity_id,
                    'Name': name,
                    'Type': entity_type,
                    'SourceDB': source_db,
                    'ID_in_SourceDB': source_db_id,
                })
            
            results_df = pd.DataFrame(results)
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


def pubtator_api_find_related_entities(
    target_entity: str,
    relation_type: RelationType,
    related_entity_type: Union[str, EntityType],
    limit: int = 100,
    max_retries: int = 3,
    max_requests_per_second: float = 3.0
) -> Optional[pd.DataFrame]:
    """
    Find entities that have a specific relationship with a target entity using PubTator3 relations API.
    
    This function queries the PubTator3 relations endpoint to discover entities that are related
    to a target entity through a specific relationship type. Useful for finding co-occurring
    entities, drug-disease associations, gene-chemical interactions, etc.
    
    Args:
        target_entity (str): The target entity to find relations for.
            Must be a PubTator3 entity ID (e.g., "@GENE_JAK1", "@DISEASE_COVID_19")
            or an entity type (e.g., "GENE", "DISEASE", "CHEMICAL")
        
        relation_type (RelationType): Type of relation to search for.
            One of: ASSOCIATE, CAUSE, COMPARE, COTREAT, DRUG_INTERACT, INHIBIT, INTERACT,
            NEGATIVE_CORRELATE, POSITIVE_CORRELATE, PREVENT, STIMULATE, TREAT, ANY
        
        related_entity_type (Union[str, EntityType]): Type or ID of related entities to find.
            Can be:
            - Entity type: GENE, DISEASE, CHEMICAL, VARIANT, SPECIES, CELLLINE
            - Specific entity ID: "@CHEMICAL_D000068698", "@GENE_1956"
        
        limit (int): Maximum number of results to return (default: 100)
        
        max_retries (int): Maximum number of retry attempts for failed requests (default: 3)
        max_requests_per_second (float): Maximum number of requests per second (default: 3.0)
    
    Returns:
        Optional[pd.DataFrame]: DataFrame containing related entities with columns:
            - Entity1_ID: First entity ID in the relation
            - Entity1_Name: First entity name
            - Entity1_Type: First entity type
            - Relation_Type: Type of relation
            - Entity2_ID: Second entity ID in the relation
            - Entity2_Name: Second entity name
            - Entity2_Type: Second entity type
            - PubMed_Count: Number of PubMed articles supporting this relation
        Returns None if the request fails after all retries.
    
    Relation Types:
        - ASSOCIATE: General association between entities
        - CAUSE: Entity1 causes entity2
        - COMPARE: Effect comparison between entities
        - COTREAT: Entities administered together
        - DRUG_INTERACT: Pharmacodynamic interaction
        - INHIBIT: Negative correlation or inhibition
        - INTERACT: Physical interaction (e.g., protein binding)
        - NEGATIVE_CORRELATE: Negative correlation (e.g., gene expression)
        - POSITIVE_CORRELATE: Positive correlation (e.g., gene expression)
        - PREVENT: Prevention relationship
        - STIMULATE: Stimulation relationship
        - TREAT: Treatment relationship
        - ANY: Any relation type
    
    Examples:
        # Find chemicals that negatively correlate with JAK1 gene
        >>> results = pubtator_api_find_related_entities(
        ...     target_entity="@GENE_JAK1",
        ...     relation_type="NEGATIVE_CORRELATE",
        ...     related_entity_type="CHEMICAL",
        ...     limit=50
        ... )
        
        # Find diseases treated by Doxorubicin
        >>> results = pubtator_api_find_related_entities(
        ...     target_entity="@CHEMICAL_Doxorubicin",
        ...     relation_type="TREAT",
        ...     related_entity_type="DISEASE",
        ...     limit=100
        ... )
        
        # Find genes that interact with a specific disease
        >>> results = pubtator_api_find_related_entities(
        ...     target_entity="@DISEASE_Neoplasms",
        ...     relation_type="ASSOCIATE",
        ...     related_entity_type="GENE",
        ...     limit=200
        ... )
        
        # Find any entities that interact with BRCA1
        >>> results = pubtator_api_find_related_entities(
        ...     target_entity="@GENE_672",  # BRCA1
        ...     relation_type="ANY",
        ...     related_entity_type="CHEMICAL",
        ...     limit=100
        ... )
    """
    # Validate inputs
    if not target_entity or not target_entity.strip():
        raise ValueError("target_entity cannot be empty")
    
    # Validate relation type
    if relation_type not in VALID_RELATION_TYPES:
        raise ValueError(
            f"Invalid relation_type '{relation_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_RELATION_TYPES))}"
        )
    
    # Validate related entity type (can be entity type or entity ID)
    if not related_entity_type.startswith('@') and related_entity_type not in VALID_ENTITY_TYPES:
        raise ValueError(
            f"Invalid related_entity_type '{related_entity_type}'. "
            f"Must be an entity ID (starting with @) or one of: {', '.join(sorted(VALID_ENTITY_TYPES))}"
        )
    
    rate_limiter = RateLimiter(max_requests_per_second)
    
    # Prepare query parameters
    # Convert relation type to lowercase with underscore (API format)
    api_relation_type = relation_type.lower()
    
    params = {
        "e1": target_entity.strip(),
        "type": api_relation_type,
        "e2": related_entity_type,
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
            response = requests.get(PUBTATOR3_RELATIONS_URL, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            
            if not data or len(data) == 0:
                print(f"No related entities found for target '{target_entity}' with relation '{relation_type}'")
                return pd.DataFrame(columns=[
                    'Entity1_ID', 'Entity1_Name', 'Entity1_Type',
                    'Relation_Type',
                    'Entity2_ID', 'Entity2_Name', 'Entity2_Type',
                    'PubMed_Count'
                ])
            
            print(f"Successfully retrieved {len(data)} related entities")
            
            # Parse results into a structured format
            results = []
            for item in data:
                # Extract relation information
                relation = item.get('type', '')
                entity_1_id = item.get('source', '')
                entity_2_id = item.get('target', '')
                pubmed_count = item.get('publications', 0)
                
                results.append({
                    'Entity1_ID': entity_1_id,
                    'Relation_Type': relation,
                    'Entity2_ID': entity_2_id,
                    'PubMed_Count': pubmed_count,
                })
            
            results_df = pd.DataFrame(results)
            
            # Apply limit if needed
            if limit and len(results_df) > limit:
                results_df = results_df.head(limit)
            
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
