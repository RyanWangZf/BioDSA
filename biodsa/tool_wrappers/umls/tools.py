from typing import Literal, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import json
import os

from biodsa.tools.umls.umls_python_client.umls_client import UMLSClient
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper

__all__ = [
    "SearchUMLSEntitiesTool",
    "SearchUMLSEntitiesToolInput",
]

# =====================================================
# Tool 1: Search UMLS Entities
# =====================================================
class SearchUMLSEntitiesToolInput(BaseModel):
    """Input schema for SearchUMLSEntitiesTool."""
    search_string: str = Field(
        ...,
        description="The search term or phrase to search in UMLS. Example: 'diabetes', 'heart attack', 'BRCA1'"
    )
    target_vocabulary: Optional[str] = Field(
        default=None,
        description=(
            "Target source vocabulary to search in (comma-separated if multiple). "
            "Common vocabularies: 'SNOMEDCT_US' (SNOMED CT), 'ICD10CM' (ICD-10-CM), "
            "'RXNORM' (RxNorm for drugs), 'LOINC' (lab tests), 'MSH' (MeSH), "
            "'NCI' (NCI Thesaurus), 'HPO' (Human Phenotype Ontology). "
            "If None, searches across all vocabularies."
        )
    )
    search_type: Literal[
        "exact", "words", "leftTruncation", "rightTruncation", 
        "normalizedString", "normalizedWords"
    ] = Field(
        default="words",
        description=(
            "Type of search to perform. Options: "
            "'exact' (exact match), "
            "'words' (matches on individual words in any order), "
            "'leftTruncation' (matches terms ending with the search string), "
            "'rightTruncation' (matches terms beginning with the search string), "
            "'normalizedString' (exact match on normalized string), "
            "'normalizedWords' (word match on normalized string)."
        )
    )
    return_id_type: Literal[
        "concept", "code", "aui", "sourceConcept", "sourceDescriptor", "sourceUi"
    ] = Field(
        default="concept",
        description=(
            "Type of identifier to retrieve. Options: "
            "'concept' (UMLS CUI), "
            "'code' (source-asserted identifier), "
            "'aui' (atom unique identifier), "
            "'sourceConcept', 'sourceDescriptor', 'sourceUi'."
        )
    )


class SearchUMLSEntitiesTool(BaseTool):
    """
    Tool to search for biomedical entities in the UMLS Metathesaurus.
    
    The Unified Medical Language System (UMLS) integrates and distributes key terminology,
    classification, and coding standards from various biomedical vocabularies. This tool
    allows you to search across multiple vocabularies to find standardized medical concepts.
    
    Use cases:
    - Find UMLS CUIs (Concept Unique Identifiers) for medical terms
    - Search for terms in specific vocabularies (SNOMED CT, ICD-10, RxNorm, etc.)
    - Disambiguate medical terminology
    - Map terms across different coding systems
    """
    name: str = "search_umls_entities"
    description: str = (
        "Search for biomedical entities in the UMLS Metathesaurus. "
        "Returns standardized medical concepts (CUIs) and their mappings across different vocabularies. "
        "Can search in specific vocabularies like SNOMED CT, ICD-10, RxNorm, LOINC, MeSH, etc. "
        "Supports different search types: exact match, word match, truncation searches. "
        "Returns top 10 most relevant results by default. "
        "Useful for finding standardized medical terminology, concept disambiguation, and cross-vocabulary mapping."
    )
    args_schema: Type[BaseModel] = SearchUMLSEntitiesToolInput
    umls_api_key: Optional[str] = None
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, umls_api_key: Optional[str] = None, sandbox: ExecutionSandboxWrapper = None):
        """Initialize the tool with UMLS API key and optional sandbox."""
        super().__init__()
        # Try to get API key from environment if not provided
        self.umls_api_key = umls_api_key or os.getenv("UMLS_API_KEY")
        if not self.umls_api_key:
            raise ValueError(
                "UMLS API key is required. Either pass it as 'umls_api_key' parameter "
                "or set it as 'UMLS_API_KEY' environment variable."
            )
        self.sandbox = sandbox
    
    def _run(
        self,
        search_string: str,
        target_vocabulary: Optional[str] = None,
        search_type: Literal[
            "exact", "words", "leftTruncation", "rightTruncation",
            "normalizedString", "normalizedWords"
        ] = "words",
        return_id_type: Literal[
            "concept", "code", "aui", "sourceConcept", "sourceDescriptor", "sourceUi"
        ] = "concept",
    ) -> str:
        """Execute the tool to search UMLS entities."""
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.umls.umls_python_client.umls_client import UMLSClient
import json
import os

try:
    # Get API key from environment
    umls_api_key = {repr(self.umls_api_key)} or os.getenv("UMLS_API_KEY")
    
    # Initialize UMLS client
    client = UMLSClient(api_key=umls_api_key)
    
    # Perform search with top 10 results
    results = client.searchAPI.search(
        search_string={repr(search_string)},
        sabs={repr(target_vocabulary)},
        search_type={repr(search_type)},
        return_id_type={repr(return_id_type)},
        page_size=10,
        page_number=1
    )
    
    # Check if there's an error
    if isinstance(results, dict) and "error" in results:
        print(f"Error searching UMLS: {{results['error']}}")
    else:
        # Parse results
        if isinstance(results, str):
            results = json.loads(results)
        
        # Extract result items
        result_list = results.get("result", {{}}).get("results", [])
        
        if not result_list or len(result_list) == 0:
            msg = f"No results found for search term '{search_string}'"
            if {repr(target_vocabulary)}:
                msg += f" in vocabulary '{target_vocabulary}'"
            msg += f" using '{search_type}' search type."
            print(msg)
        else:
            # Format results
            output_parts = []
            output_parts.append(f"UMLS Search Results for: '{search_string}'")
            output_parts.append("=" * 80)
            
            if {repr(target_vocabulary)}:
                output_parts.append(f"Target Vocabulary: {target_vocabulary}")
            output_parts.append(f"Search Type: {search_type}")
            output_parts.append(f"Return ID Type: {return_id_type}")
            output_parts.append(f"Found {{len(result_list)}} results (showing top 10):")
            output_parts.append("=" * 80)
            
            for idx, result in enumerate(result_list, 1):
                ui = result.get("ui", "N/A")
                name = result.get("name", "N/A")
                uri = result.get("uri", "N/A")
                root_source = result.get("rootSource", "N/A")
                
                output_parts.append(f"\\n{{idx}}. {{name}}")
                output_parts.append(f"   ID: {{ui}}")
                output_parts.append(f"   Root Source: {{root_source}}")
                output_parts.append(f"   URI: {{uri}}")
            
            print("\\n".join(output_parts))
            
except Exception as e:
    print(f"Error executing UMLS search: {{str(e)}}")
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
            try:
                # Initialize UMLS client
                client = UMLSClient(api_key=self.umls_api_key)
                
                # Perform search with top 10 results
                results = client.searchAPI.search(
                    search_string=search_string,
                    sabs=target_vocabulary,
                    search_type=search_type,
                    return_id_type=return_id_type,
                    page_size=10,
                    page_number=1
                )
                
                # Check if there's an error
                if isinstance(results, dict) and "error" in results:
                    output = f"Error searching UMLS: {results['error']}"
                else:
                    # Parse results
                    if isinstance(results, str):
                        results = json.loads(results)
                    
                    # Extract result items
                    result_list = results.get("result", {}).get("results", [])
                    
                    if not result_list or len(result_list) == 0:
                        output = (
                            f"No results found for search term '{search_string}'"
                            + (f" in vocabulary '{target_vocabulary}'" if target_vocabulary else "")
                            + f" using '{search_type}' search type."
                        )
                    else:
                        # Format results in a readable way
                        output_parts = []
                        output_parts.append(f"UMLS Search Results for: '{search_string}'")
                        output_parts.append("=" * 80)
                        
                        if target_vocabulary:
                            output_parts.append(f"Target Vocabulary: {target_vocabulary}")
                        output_parts.append(f"Search Type: {search_type}")
                        output_parts.append(f"Return ID Type: {return_id_type}")
                        output_parts.append(f"Found {len(result_list)} results (showing top 10):")
                        output_parts.append("=" * 80)
                        
                        for idx, result in enumerate(result_list, 1):
                            ui = result.get("ui", "N/A")
                            name = result.get("name", "N/A")
                            uri = result.get("uri", "N/A")
                            root_source = result.get("rootSource", "N/A")
                            
                            output_parts.append(f"\n{idx}. {name}")
                            output_parts.append(f"   ID: {ui}")
                            output_parts.append(f"   Root Source: {root_source}")
                            output_parts.append(f"   URI: {uri}")
                        
                        output = "\n".join(output_parts)
                        
            except Exception as e:
                output = f"Error executing UMLS search: {str(e)}"
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result
