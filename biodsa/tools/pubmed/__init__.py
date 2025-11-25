"""PubMed and PubTator API functions for literature search and annotation.

This module provides pure API functions without LangChain dependencies.
"""

__all__ = [
    # PubMed API functions
    "pubmed_api_get_paper_references",
    "fetch_paper_content_by_pmid",
    # PubTator API functions
    "pubtator_api_fetch_paper_annotations",
    "pubtator_api_find_entities",
    "pubtator_api_search_papers",
    "pubtator_api_find_related_entities",
]

from .pubmed_api import (
    pubmed_api_get_paper_references,
    fetch_paper_content_by_pmid,
    pubmed_api_search_papers,
)
from .pubtator_api import (
    pubtator_api_fetch_paper_annotations,
    pubtator_api_find_entities,
    pubtator_api_search_papers,
    pubtator_api_find_related_entities,
)
