"""
Tools for Virtual Lab multi-agent meetings.

This module contains tools that can be used during Virtual Lab meetings,
primarily the PubMed search tool for retrieving biomedical literature.

Based on the Virtual Lab framework:
@article{swanson2025virtual,
  title={The Virtual Lab of AI agents designs new SARS-CoV-2 nanobodies},
  author={Swanson, Kyle and Wu, Wesley and Bulaong, Nash L. and Pak, John E. and Zou, James},
  journal={Nature},
  volume={646},
  pages={716--723},
  year={2025}
}

Reference: https://github.com/zou-group/virtual-lab
"""
import json
import urllib.parse
from typing import Optional, Tuple, List, Type

import requests
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from biodsa.agents.virtuallab.prompt import format_references


class PubMedSearchInput(BaseModel):
    """Input schema for PubMed search."""
    query: str = Field(description="The search query to use for PubMed Central")
    num_articles: int = Field(
        default=3,
        description="The number of articles to return (default: 3)"
    )
    abstract_only: bool = Field(
        default=False,
        description="Whether to return only abstracts instead of full text"
    )


def get_pubmed_central_article(
    pmcid: str,
    abstract_only: bool = False
) -> Tuple[Optional[str], Optional[List[str]]]:
    """
    Get the title and content of a PubMed Central article given a PMC ID.
    
    Note: This only returns main text, ignoring tables, figures, and references.
    
    Args:
        pmcid: The PMC ID of the article
        abstract_only: Whether to return only the abstract
        
    Returns:
        Tuple of (title, content as list of paragraphs) or (None, None) if not found
    """
    # Get article from PMC ID in JSON form
    text_url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_JSON/PMC{pmcid}/unicode"
    
    try:
        response = requests.get(text_url, timeout=30)
        response.raise_for_status()
    except requests.RequestException:
        return None, None
    
    # Try to parse JSON
    try:
        article = response.json()
    except json.JSONDecodeError:
        return None, None
    
    if not article or not article[0].get("documents"):
        return None, None
    
    # Get document
    document = article[0]["documents"][0]
    
    # Get title
    title = None
    for passage in document.get("passages", []):
        if passage.get("infons", {}).get("section_type") == "TITLE":
            title = passage.get("text")
            break
    
    if title is None:
        return None, None
    
    # Get relevant passages
    passages = [
        passage for passage in document.get("passages", [])
        if passage.get("infons", {}).get("type") in {"abstract", "paragraph"}
    ]
    
    # Get abstract or full text of article (excluding references)
    if abstract_only:
        passages = [
            passage for passage in passages
            if passage.get("infons", {}).get("section_type") in ["ABSTRACT"]
        ]
    else:
        passages = [
            passage for passage in passages
            if passage.get("infons", {}).get("section_type") in [
                "ABSTRACT", "INTRO", "RESULTS", "DISCUSS", "CONCL", "METHODS"
            ]
        ]
    
    # Get content
    content = [passage.get("text", "") for passage in passages]
    
    return title, content


def run_pubmed_search(
    query: str,
    num_articles: int = 3,
    abstract_only: bool = False
) -> str:
    """
    Run a PubMed search, returning the full text or abstracts of matching articles.
    
    Args:
        query: The query to search PubMed with
        num_articles: The number of articles to search for
        abstract_only: Whether to return only abstracts
        
    Returns:
        Formatted text with article contents
    """
    print(
        f'Searching PubMed Central for {num_articles} articles '
        f'({"abstracts" if abstract_only else "full text"}) with query: "{query}"'
    )
    
    # Perform PubMed Central search for query to get PMC ID
    search_url = (
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
        f"db=pmc&term={urllib.parse.quote_plus(query)}&retmax={2 * num_articles}"
        f"&retmode=json&sort=relevance"
    )
    
    try:
        response = requests.get(search_url, timeout=30)
        response.raise_for_status()
        pmcids_found = response.json().get("esearchresult", {}).get("idlist", [])
    except (requests.RequestException, json.JSONDecodeError):
        return f'Error searching PubMed Central for query "{query}".'
    
    # Loop through top articles
    texts = []
    titles = []
    pmcids = []
    
    for pmcid in pmcids_found:
        # Break if reached desired number of articles
        if len(pmcids) >= num_articles:
            break
        
        title, content = get_pubmed_central_article(
            pmcid=pmcid,
            abstract_only=abstract_only,
        )
        
        if title is None:
            continue
        
        texts.append(
            f"PMCID = {pmcid}\n\nTitle = {title}\n\n{chr(10).join(content or [])}"
        )
        titles.append(title)
        pmcids.append(pmcid)
    
    # Print articles found
    article_count = len(texts)
    print(f"Found {article_count:,} articles on PubMed Central")
    
    # Combine texts
    if article_count == 0:
        combined_text = f'No articles found on PubMed Central for the query "{query}".'
    else:
        combined_text = format_references(
            references=texts,
            reference_type="paper",
            intro=f'Here are the top {article_count} articles on PubMed Central for the query "{query}":',
        )
    
    return combined_text


class PubMedSearchTool(BaseTool):
    """
    Tool to search PubMed Central for biomedical and life sciences articles.
    
    This tool allows agents to retrieve scientific literature during discussions,
    enabling evidence-based decision making.
    
    Example:
        ```python
        tool = PubMedSearchTool()
        result = tool._run(
            query="SARS-CoV-2 nanobody design",
            num_articles=3,
            abstract_only=False
        )
        print(result)
        ```
    """
    
    name: str = "pubmed_search"
    description: str = (
        "Search PubMed Central for biomedical and life sciences articles. "
        "Returns abstracts or full text of matching articles. "
        "Use this to find scientific evidence and references for your research discussions."
    )
    args_schema: Type[BaseModel] = PubMedSearchInput
    
    def _run(
        self,
        query: str,
        num_articles: int = 3,
        abstract_only: bool = False
    ) -> str:
        """
        Execute the PubMed search.
        
        Args:
            query: The search query
            num_articles: Number of articles to retrieve
            abstract_only: Whether to return only abstracts
            
        Returns:
            Formatted text with article contents
        """
        return run_pubmed_search(
            query=query,
            num_articles=num_articles,
            abstract_only=abstract_only
        )
    
    async def _arun(
        self,
        query: str,
        num_articles: int = 3,
        abstract_only: bool = False
    ) -> str:
        """Async version of the tool (currently just calls sync version)."""
        return self._run(query, num_articles, abstract_only)


def get_virtuallab_tools(use_pubmed: bool = True) -> List[BaseTool]:
    """
    Get all available tools for Virtual Lab meetings.
    
    Args:
        use_pubmed: Whether to include the PubMed search tool
        
    Returns:
        List of available tools
    """
    tools = []
    
    if use_pubmed:
        tools.append(PubMedSearchTool())
    
    return tools
