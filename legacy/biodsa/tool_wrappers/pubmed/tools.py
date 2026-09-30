from typing import Literal, List, Dict, Any, Type, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import pandas as pd
import json
import re
import os
import math

from biodsa.tools.pubmed.pubmed_api import (
    pubmed_api_get_paper_references,
    fetch_paper_content_by_pmid
)
from biodsa.tools.pubmed.pubtator_api import (
    pubtator_api_fetch_paper_annotations,
    pubtator_api_find_entities,
    pubtator_api_search_papers,
    pubtator_api_find_related_entities,
)
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper
from biodsa.tool_wrappers.utils import clean_task_name_for_filename, run_python_repl

__all__ = [
    "GetPaperReferencesTool",
    "FetchPaperAnnotationsTool",
    "FetchPaperContentTool",
    "FindEntitiesTool",
    "SearchPapersTool",
    "FindRelatedEntitiesTool",
    "GetPaperReferencesToolInput",
    "FetchPaperAnnotationsToolInput",
    "FetchPaperContentToolInput",
    "FindEntitiesToolInput",
    "SearchPapersToolInput",
    "FindRelatedEntitiesToolInput",
]

def _clean_query_for_pubmed(boolean_query_text: str) -> str:
    """
    Clean the query for pubmed search by removing entity type prefixes and replacing underscores with spaces.
    
    Converts patterns like:
    - @CHEMICAL_remdesivir to remdesivir
    - @DISEASE_Polycystic_Ovary_Syndrome to Polycystic Ovary Syndrome
    - @GENE_BRCA1 to BRCA1
    
    Args:
        boolean_query_text: Query string with entity identifiers
        
    Returns:
        Cleaned query string with @TYPE_ prefixes removed and underscores replaced with spaces
    """
    if not boolean_query_text:
        return boolean_query_text
    
    # Step 1: Remove @ENTITYTYPE_ prefix
    # Pattern: @[UPPERCASE_LETTERS]_ where entity types are all caps
    # This matches @DISEASE_, @CHEMICAL_, @GENE_, etc.
    cleaned_query = re.sub(r'@[A-Z]+_', '', boolean_query_text)
    
    # Step 2: Replace underscores with spaces
    cleaned_query = cleaned_query.replace('_', ' ')
    
    return cleaned_query

# =====================================================
# Tool 1: Get Paper References
# =====================================================
class GetPaperReferencesToolInput(BaseModel):
    """Input schema for GetPaperReferencesTool."""
    task_name: str = Field(
        ...,
        description="A less than three word description of what is the search for. It will be used to save the search results to the sandbox.",
    )
    pmids: List[str] = Field(
        ...,
        description="List of PubMed IDs (PMIDs) to get references for."
    )
    batch_size: int = Field(
        default=100,
        description="Number of PMIDs to process in each main batch."
    )
    mini_batch_size: int = Field(
        default=20,
        description="Size of each sub-batch for threading."
    )
    max_workers: int = Field(
        default=4,
        description="Number of threads for concurrent processing."
    )
    rate_limit: float = Field(
        default=3.0,
        description="Maximum requests per second."
    )


class GetPaperReferencesTool(BaseTool):
    """
    Tool to get paper references (citation relations) for a list of PMIDs.

    This tool retrieves articles that the input papers cite, returning citation
    relations with source and target PMIDs. Uses multi-threaded processing for efficiency.
    """
    name: str = "get_paper_references"
    description: str = (
        "Get paper references (citations) for a list of PubMed IDs. "
        "Returns citation relations showing which papers the input papers cite. "
        "Useful for finding related work and building citation networks."
    )
    args_schema: Type[BaseModel] = GetPaperReferencesToolInput
    sandbox: ExecutionSandboxWrapper = None
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox

    def _run(
        self,
        task_name: str,
        pmids: List[str],
        batch_size: int = 100,
        mini_batch_size: int = 20,
        max_workers: int = 4,
        rate_limit: float = 3.0
    ) -> str:
        """Execute the tool to get paper references."""
        # clean up  the task name for the filename
        cleaned_task_name = clean_task_name_for_filename(task_name)
        if self.sandbox is not None:
            workdir = self.sandbox.get_workdir()
        else:
            # local, get the current exefcution directory
            workdir = os.path.join(os.getcwd(), "workdir")
            # create the directory if it doesn't exist
            os.makedirs(workdir, exist_ok=True)
        tgt_filepath = os.path.join(workdir, f"{cleaned_task_name}.csv")
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.pubmed.pubmed_api import pubmed_api_get_paper_references
import pandas as pd

# Get paper references
search_results = pubmed_api_get_paper_references(
    pmids={repr(pmids)},
    batch_size={batch_size},
    mini_batch_size={mini_batch_size},
    max_workers={max_workers},
    rate_limit={rate_limit}
)

# Output results
search_results_df = pd.DataFrame(search_results)
search_results_df.to_csv('{tgt_filepath}', index=False)
print("The search results are saved at '{tgt_filepath}'")
print(search_results_df.head().to_markdown())
"""
        
        # Execute in sandbox if available
        if self.sandbox is not None:
            exit_code, output, artifacts, running_time, peak_memory = self.sandbox.execute(
                language="python",
                code=code_template
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += f"*Execution time: {running_time:.2f}s, Peak memory: {peak_memory:.2f}MB*"
            
            if exit_code != 0:
                result += f"\n\n⚠️ **Warning:** Code exited with non-zero status ({exit_code})"
            
            return result
        else:
            # Fallback: execute locally
            output = run_python_repl(code_template)
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            
            return result


# =====================================================
# Helper Function: Extract Relevant Sections with Context
# =====================================================
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


# =====================================================
# Tool 2: Fetch Paper Content
# =====================================================
class FetchPaperContentToolInput(BaseModel):
    """Input schema for FetchPaperContentTool."""
    pmid: str = Field(
        ...,
        description="A single PubMed ID (PMID) to fetch content for. Example: '36608654'"
    )
    filter_keywords: str = Field(
        ...,
        description=(
            "Keywords or regex pattern to search for and extract from the paper content. "
            "This FILTERS the paper to return ONLY matching sections with surrounding context (~1000 chars per match). "
            "Use this to focus on specific information you need from long papers. "
            "Supports both simple keywords and regex patterns (case-insensitive). "
            "Examples: "
            "- Simple keywords: 'survival rate', 'adverse events', 'clinical outcomes' "
            "- Multiple terms (OR logic): 'efficacy|effectiveness|response rate' "
            "- Statistical data: 'hazard ratio.*\\d+\\.\\d+', 'p[- ]?value.*0\\.0\\d+' "
            "- Drug dosages: 'dosage|dose.*mg.*kg', 'IC50|EC50' "
            "- Methods: 'randomized.*controlled.*trial', 'inclusion criteria' "
        )
    )


class FetchPaperContentTool(BaseTool):
    """
    Tool to fetch complete paper content for a single PMID from multiple sources.

    This tool:
    1. Fetches title and abstract from PubMed API
    2. Checks PubTator3 for full text availability
    3. Attempts to fetch full open access text from PMC BioC JSON API
    4. Returns the most complete content available

    Critical for extracting specific data, numbers, or detailed information from papers.
    """
    name: str = "fetch_paper_content"
    description: str = (
        "Fetch and extract specific content from a PubMed paper by PMID using keyword/regex filtering. "
        "REQUIRED: You MUST provide 'filter_keywords' to specify what content to extract from the paper. "
        "This tool returns ONLY the sections matching your keywords with surrounding context (~1000 chars per match), "
        "making it efficient for extracting specific information from long papers. "
        "Sources tried: (1) PubMed for title/abstract, (2) PubTator3 for full text, (3) PMC BioC for open access full text. "
        "CRITICAL USE CASES: "
        "- Extract specific statistics: filter_keywords='hazard ratio|odds ratio|p-value' "
        "- Find methodology details: filter_keywords='study design|inclusion criteria|randomization' "
        "- Get clinical outcomes: filter_keywords='survival|mortality|response rate|adverse events' "
        "- Extract drug information: filter_keywords='dosage|administration|pharmacokinetics' "
        "The filter_keywords supports both simple text matching and regex patterns (case-insensitive)."
    )
    args_schema: Type[BaseModel] = FetchPaperContentToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox

    def _run(self, pmid: str, filter_keywords: str) -> str:
        """
        Execute the tool to fetch and filter paper content.

        Args:
            pmid: PubMed ID to fetch
            filter_keywords: Keywords or regex pattern to filter the content

        Returns:
            Formatted string with title, abstract, and filtered content sections
        """
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.pubmed.pubmed_api import fetch_paper_content_by_pmid, format_paper_content_output

# Fetch and format paper content
result = fetch_paper_content_by_pmid({repr(pmid)})
output = format_paper_content_output(result, filter_keywords={repr(filter_keywords)})
print(output)
"""

        # Execute in sandbox if available
        if self.sandbox is not None:
            exit_code, output, artifacts, running_time, peak_memory = self.sandbox.execute(
                language="python",
                code=code_template
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += f"*Execution time: {running_time:.2f}s, Peak memory: {peak_memory:.2f}MB*"
            
            if exit_code != 0:
                result += f"\n\n⚠️ **Warning:** Code exited with non-zero status ({exit_code})"
            
            return result
        else:
            # Fallback: execute locally
            output = run_python_repl(code_template)
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            
            return result


# =====================================================
# Tool 3: Fetch Paper Annotations
# =====================================================
class FetchPaperAnnotationsToolInput(BaseModel):
    """Input schema for FetchPaperAnnotationsTool."""
    pmids: List[str] = Field(
        ...,
        description="List of PubMed IDs (PMIDs) to fetch annotations for."
    )
    batch_size: int = Field(
        default=50,
        description="Maximum number of PMIDs per API request."
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed requests."
    )
    max_requests_per_second: float = Field(
        default=3.0,
        description="Maximum number of requests per second."
    )


class FetchPaperAnnotationsTool(BaseTool):
    """
    Tool to fetch biomedical entity annotations from PubTator3 for a list of papers.

    This tool retrieves annotated entities (genes, diseases, chemicals, variants, etc.)
    and their relations from PubMed papers using the PubTator3 API.
    """
    name: str = "fetch_paper_annotations"
    description: str = (
        "Fetch biomedical entity annotations from PubTator3 for a list of PubMed IDs. "
        "Returns annotated entities (genes, diseases, chemicals, variants, species, cell lines) "
        "and their relations from the papers. Useful for extracting structured biomedical knowledge."
    )
    args_schema: Type[BaseModel] = FetchPaperAnnotationsToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox

    def _run(
        self,
        pmids: List[str],
        batch_size: int = 50,
        max_retries: int = 3,
        max_requests_per_second: float = 3.0
    ) -> str:
        """Execute the tool to fetch paper annotations."""
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.pubmed.pubtator_api import pubtator_api_fetch_paper_annotations
import json

# Fetch paper annotations
search_results = pubtator_api_fetch_paper_annotations(
    pmids={repr(pmids)},
    batch_size={batch_size},
    max_retries={max_retries},
    max_requests_per_second={max_requests_per_second}
)

# Output results
print(json.dumps(search_results, indent=4))
"""
        
        # Execute in sandbox if available
        if self.sandbox is not None:
            exit_code, output, artifacts, running_time, peak_memory = self.sandbox.execute(
                language="python",
                code=code_template
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += f"*Execution time: {running_time:.2f}s, Peak memory: {peak_memory:.2f}MB*"
            
            if exit_code != 0:
                result += f"\n\n⚠️ **Warning:** Code exited with non-zero status ({exit_code})"
            
            return result
        else:
            # Fallback: execute locally
            output = run_python_repl(code_template)
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            
            return result

# =====================================================
# Tool 4: Find Entities
# =====================================================
class FindEntitiesToolInput(BaseModel):
    """Input schema for FindEntitiesTool."""
    query_text: str = Field(
        ...,
        description="A single search term (partial entity name) to find entities in PubTator3. Example: 'remdesivir', 'COVID', 'BRCA1'."
    )
    concept_type: Optional[Literal["GENE", "DISEASE", "CHEMICAL", "VARIANT", "SPECIES", "CELLLINE"]] = Field(
        default=None,
        description="Restrict results to a specific entity type. If None, searches across all types."
    )
    limit: int = Field(
        default=10,
        description="Maximum number of results to return."
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed requests."
    )
    max_requests_per_second: float = Field(
        default=3.0,
        description="Maximum number of requests per second."
    )


class FindEntitiesTool(BaseTool):
    """
    Tool to find and autocomplete biomedical entity names in PubTator3.

    This tool provides entity name suggestions based on partial text input,
    useful for finding entity IDs and normalized names.
    """
    name: str = "find_entities"
    description: str = (
        "Find and autocomplete biomedical entity names in the PubTator3 database. "
        "Returns entity suggestions with IDs, normalized names, and types. "
        "Useful for entity disambiguation and finding correct entity identifiers for search."
    )
    args_schema: Type[BaseModel] = FindEntitiesToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox

    def _run(
        self,
        query_text: str,
        concept_type: Optional[Literal["GENE", "DISEASE", "CHEMICAL", "VARIANT", "SPECIES", "CELLLINE"]] = None,
        limit: int = 10,
        max_retries: int = 3,
        max_requests_per_second: float = 3.0
    ) -> str:
        """Execute the tool to find entities."""
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.pubmed.pubtator_api import pubtator_api_find_entities
import pandas as pd

# Find entities
results = pubtator_api_find_entities(
    query_text={repr(query_text)},
    concept_type={repr(concept_type)},
    limit={limit},
    max_retries={max_retries},
    max_requests_per_second={max_requests_per_second}
)

# Output results
if len(results) == 0:
    print("No entities found. Please try again with different query.")
else:
    if isinstance(results, pd.DataFrame):
        print(results.to_markdown())
    else:
        print("No entities found. Please try again with different query.")
"""
        
        # Execute in sandbox if available
        if self.sandbox is not None:
            exit_code, output, artifacts, running_time, peak_memory = self.sandbox.execute(
                language="python",
                code=code_template
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += f"*Execution time: {running_time:.2f}s, Peak memory: {peak_memory:.2f}MB*"
            
            if exit_code != 0:
                result += f"\n\n⚠️ **Warning:** Code exited with non-zero status ({exit_code})"
            
            return result
        else:
            # Fallback: execute locally
            output = run_python_repl(code_template)
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            
            return result

# =====================================================
# Tool 5: Search Papers
# =====================================================
class SearchPapersToolInput(BaseModel):
    """Input schema for SearchPapersTool."""
    task_name: str = Field(
        ...,
        description="A less than three word description of what is the search for",
    )
    boolean_query_text: Optional[str] = Field(
        default=None,
        description=(
            "Boolean query with entity IDs/types, keywords, AND/OR operators, and parentheses. "
            "Examples: '@CHEMICAL_remdesivir', '@CHEMICAL_Doxorubicin AND @DISEASE_Neoplasms', "
            "'(@DISEASE_COVID_19 AND complications) OR @DISEASE_Post_Acute_COVID_19_Syndrome'"
        )
    )
    relation_query: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Relation-based search dictionary with keys: 'relation_type' (TREAT, CAUSE, INTERACT, etc.), "
            "'entity1' (entity ID or type), 'entity2' (entity ID or type). "
            "Example: {'relation_type': 'TREAT', 'entity1': '@CHEMICAL_Doxorubicin', 'entity2': '@DISEASE_Neoplasms'}"
        )
    )
    top_k: int = Field(
        default=100,
        description="Number of top results to return."
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed requests."
    )
    max_requests_per_second: float = Field(
        default=3.0,
        description="Maximum number of requests per second."
    )


class SearchPapersTool(BaseTool):
    """
    Tool to search for PubMed articles using boolean or relation-based queries.

    Supports two search modes:
    1. Boolean queries with entity IDs, entity types, and free-text keywords
    2. Relation-based queries to find papers discussing specific entity relationships
    """
    name: str = "search_papers"
    description: str = (
        "Search for PubMed articles using boolean queries or relation-based queries. "
        "Boolean mode: Use entity IDs (@CHEMICAL_remdesivir), entity types, keywords, and AND/OR operators. "
        "Relation mode: Search by entity relationships (TREAT, CAUSE, INTERACT, etc.). "
        "Returns paper metadata including PMID, title, journal, date, and highlighted text snippets."
    )
    args_schema: Type[BaseModel] = SearchPapersToolInput
    sandbox: ExecutionSandboxWrapper = None

    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox

    def _run(
        self,
        task_name: str,
        boolean_query_text: Optional[str] = None,
        relation_query: Optional[Dict[str, Any]] = None,
        top_k: int = 100,
        max_retries: int = 3,
        max_requests_per_second: float = 3.0
    ) -> str:
        """Execute the tool to search papers."""

        # clean up the task name for the filename
        cleaned_task_name = clean_task_name_for_filename(task_name)
        if self.sandbox is not None:
            workdir = self.sandbox.get_workdir()
        else:
            # local, get the current exefcution directory
            workdir = os.path.join(os.getcwd(), "workdir")
            # create the directory if it doesn't exist
            os.makedirs(workdir, exist_ok=True)
        tgt_filepath = os.path.join(workdir, f"{cleaned_task_name}.csv")

        # calculate the number of pages to search
        n_pages = math.ceil(top_k / 10) # 10 results per page
        n_pages = max(n_pages, 1) # min 1 page
        n_pages = min(n_pages, 100) # max 100 pages

        # clean the boolean query to get the one for pubmed search
        boolean_query_text_for_pubmed = _clean_query_for_pubmed(boolean_query_text)

        # Generate Python code template
        code_template = f"""
from biodsa.tools.pubmed.pubtator_api import pubtator_api_search_papers
from biodsa.tools.pubmed.pubmed_api import pubmed_api_search_papers
import pandas as pd

# Search papers
all_search_results = []
for page in range(1, {n_pages} + 1):
    search_results = pubtator_api_search_papers(
        boolean_query_text={repr(boolean_query_text)},
        relation_query={repr(relation_query)},
        page=page,
        max_retries={max_retries},
        max_requests_per_second={max_requests_per_second}
    )
    if search_results is not None:
        all_search_results.append(search_results)
    else:
        # no more results, break the loop
        break

if len(all_search_results) > 0:
    all_search_results = pd.concat(all_search_results)
    all_search_results = all_search_results[["PMID", "Title", "Journal", "Year", "Highlighted_Text"]]
    all_search_results.columns = ["PMID", "Title", "Journal", "Year", "Abstract"]
else:
    all_search_results = None

# search papers using pubmed api
pmid_df = pubmed_api_search_papers(
    boolean_query_text={repr(boolean_query_text_for_pubmed)},
    top_k={top_k},
)
if pmid_df is not None:
    pmid_df = pmid_df[["PMID", "Title", "Journal", "Year", "Abstract"]]
    if all_search_results is not None:
        all_search_results = pd.concat([all_search_results, pmid_df]).reset_index(drop=True)
    else:
        all_search_results = pmid_df

if len(all_search_results) > 0:
    all_search_results.to_csv('{tgt_filepath}', index=False)
    print("The search results are saved at '{tgt_filepath}'")
    print(" Number of search results: ", len(all_search_results))
    print(all_search_results.head().to_markdown())
else:
    print("No search results found. Please try again with different query.")
"""
        # Execute in sandbox if available
        if self.sandbox is not None:
            exit_code, output, artifacts, running_time, peak_memory = self.sandbox.execute(
                language="python",
                code=code_template
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"            
            if exit_code != 0:
                result += f"\n\n⚠️ **Warning:** Code exited with non-zero status ({exit_code})"
            return result
        else:
            # Fallback: execute locally
            output = run_python_repl(code_template)
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            return result

# =====================================================
# Tool 6: Find Related Entities
# =====================================================
class FindRelatedEntitiesToolInput(BaseModel):
    """Input schema for FindRelatedEntitiesTool."""
    target_entity: str = Field(
        ...,
        description=(
            "The target entity to find relations for. "
            "Must be a PubTator3 entity ID (e.g., '@GENE_JAK1', '@DISEASE_COVID_19') "
            "or an entity type (e.g., 'GENE', 'DISEASE', 'CHEMICAL')."
        )
    )
    relation_type: Literal[
        "ASSOCIATE", "CAUSE", "COMPARE", "COTREAT", "DRUG_INTERACT",
        "INHIBIT", "INTERACT", "NEGATIVE_CORRELATE", "POSITIVE_CORRELATE",
        "PREVENT", "STIMULATE", "TREAT", "ANY"
    ] = Field(
        ...,
        description=(
            "Type of relation to search for. Options: "
            "ASSOCIATE (general association), "
            "CAUSE (entity1 causes entity2), "
            "COMPARE (effect comparison), "
            "COTREAT (entities administered together), "
            "DRUG_INTERACT (pharmacodynamic interaction), "
            "INHIBIT (negative correlation/inhibition), "
            "INTERACT (physical interaction like protein binding), "
            "NEGATIVE_CORRELATE (negative correlation in expression), "
            "POSITIVE_CORRELATE (positive correlation in expression), "
            "PREVENT (prevention relationship), "
            "STIMULATE (stimulation relationship), "
            "TREAT (treatment relationship), "
            "ANY (any relation type)."
        )
    )
    related_entity_type: str = Field(
        ...,
        description=(
            "Type or ID of related entities to find. Can be: "
            "- Entity type: GENE, DISEASE, CHEMICAL, VARIANT, SPECIES, CELLLINE "
            "- Specific entity ID: '@CHEMICAL_D000068698', '@GENE_1956'"
        )
    )
    limit: int = Field(
        default=100,
        description="Maximum number of results to return."
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed requests."
    )
    max_requests_per_second: float = Field(
        default=3.0,
        description="Maximum number of requests per second."
    )


class FindRelatedEntitiesTool(BaseTool):
    """
    Tool to find entities that have a specific relationship with a target entity.

    This tool queries the PubTator3 relations API to discover entities related to
    a target entity through a specific relationship type. Useful for finding:
    - Chemicals that treat specific diseases
    - Genes associated with diseases
    - Drug-drug interactions
    - Gene-chemical interactions
    - Co-occurring entities in literature
    """
    name: str = "find_related_entities"
    description: str = (
        "Find entities that have a specific relationship with a target entity using PubTator3 relations API. "
        "Discovers related entities through specific relationship types (TREAT, CAUSE, INTERACT, etc.). "
        "Returns related entities with relationship information and PubMed article counts supporting each relation. "
        "Example uses: Find chemicals that treat a disease, genes associated with a disease, "
        "drugs that interact with each other, genes that interact with chemicals."
    )
    args_schema: Type[BaseModel] = FindRelatedEntitiesToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox

    def _run(
        self,
        target_entity: str,
        relation_type: Literal[
            "ASSOCIATE", "CAUSE", "COMPARE", "COTREAT", "DRUG_INTERACT",
            "INHIBIT", "INTERACT", "NEGATIVE_CORRELATE", "POSITIVE_CORRELATE",
            "PREVENT", "STIMULATE", "TREAT", "ANY"
        ],
        related_entity_type: str,
        limit: int = 100,
        max_retries: int = 3,
        max_requests_per_second: float = 3.0
    ) -> str:
        """Execute the tool to find related entities."""
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.pubmed.pubtator_api import pubtator_api_find_related_entities
import pandas as pd

# Find related entities
results = pubtator_api_find_related_entities(
    target_entity={repr(target_entity)},
    relation_type={repr(relation_type)},
    related_entity_type={repr(related_entity_type)},
    limit={limit},
    max_retries={max_retries},
    max_requests_per_second={max_requests_per_second}
)

# Output results
if results is None:
    print("Failed to fetch related entities. Please try again.")
elif len(results) == 0:
    print(f"No related entities found for target '{target_entity}' with relation '{relation_type}' "
          f"and entity type '{related_entity_type}'. Please try different parameters.")
else:
    if isinstance(results, pd.DataFrame):
        results_str = results.to_markdown(index=False)
        summary = (
            f"Found {{len(results)}} related entities for target '{target_entity}' "
            f"with relation '{relation_type}':\\n\\n{{results_str}}"
        )
        print(summary)
    else:
        print("Unexpected result format. Please try again.")
"""
        
        # Execute in sandbox if available
        if self.sandbox is not None:
            exit_code, output, artifacts, running_time, peak_memory = self.sandbox.execute(
                language="python",
                code=code_template
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += f"*Execution time: {running_time:.2f}s, Peak memory: {peak_memory:.2f}MB*"
            
            if exit_code != 0:
                result += f"\n\n⚠️ **Warning:** Code exited with non-zero status ({exit_code})"
            
            return result
        else:
            # Fallback: execute locally
            output = run_python_repl(code_template)
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            
            return result