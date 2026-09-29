"""Unified tool wrappers for disease search and information fetching.

This module provides LangChain-compatible tools that aggregate disease information
from multiple sources (BioThings, KEGG, Open Targets) with a simple interface.
"""

import os
import pandas as pd
from typing import Optional, Type, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper
from biodsa.tools.diseases import search_diseases_unified, fetch_disease_details_unified
from biodsa.tool_wrappers.utils import clean_task_name_for_filename


# =====================================================
# Unified Disease Search Tool
# =====================================================

class UnifiedDiseaseSearchToolInput(BaseModel):
    """Input schema for UnifiedDiseaseSearchTool."""
    
    task_name: str = Field(
        description=(
            "A less than three word description of what the search is for. "
            "It will be used to save the search results to the sandbox. "
            "Examples: 'diabetes search', 'cancer types', 'heart diseases'"
        )
    )
    search_term: str = Field(
        description=(
            "Disease name, condition, symptoms, or any search term. "
            "Examples: 'diabetes', 'alzheimer', 'breast cancer', 'heart failure'"
        )
    )
    limit_per_source: int = Field(
        default=10,
        description="Maximum number of results to return from each source (1-50)"
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of sources to search. Options: 'biothings', 'kegg', 'opentargets'. "
            "If not specified, searches all sources."
        )
    )


class UnifiedDiseaseSearchTool(BaseTool):
    """
    Unified disease search tool that queries multiple databases simultaneously.
    
    This tool searches across BioThings (MyDisease.info), KEGG Disease Database,
    and Open Targets Platform to provide comprehensive disease information from a
    single simple search term.
    
    Returns aggregated results including:
    - Disease names and identifiers
    - Disease definitions and descriptions
    - Associated genes and pathways
    - Therapeutic areas and ontology information
    - Cross-database references
    
    Use this tool when you need to:
    - Find diseases by name or search term
    - Get comprehensive disease information from multiple authoritative sources
    - Research disease properties, associated genes, or pathways
    - Explore disease ontology and therapeutic areas
    - Find diseases related to specific conditions or symptoms
    """
    
    name: str = "unified_disease_search"
    description: str = (
        "Search for diseases across multiple authoritative databases (BioThings, KEGG, Open Targets) with a single search term. "
        "Returns comprehensive disease information including names, identifiers, definitions, associated genes, pathways, and therapeutic areas. "
        "Use this for: finding diseases by name, researching disease properties, checking associated genes/pathways, "
        "exploring disease ontology, finding diseases for conditions, or getting comprehensive disease information from multiple sources. "
        "CRITICAL: This is the FIRST tool to use when starting any disease research or when you need broad disease information."
    )
    args_schema: Type[BaseModel] = UnifiedDiseaseSearchToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        task_name: str,
        search_term: str,
        limit_per_source: int = 10,
        sources: Optional[List[str]] = None,
    ) -> str:
        """Execute the unified disease search."""
        
        # Clean up the task name for the filename
        cleaned_task_name = clean_task_name_for_filename(task_name)
        
        # Determine workdir and create save path
        if self.sandbox is not None:
            workdir = self.sandbox.get_workdir()
        else:
            # Local execution, use current directory
            workdir = os.path.join(os.getcwd(), "workdir")
            # Create the directory if it doesn't exist
            os.makedirs(workdir, exist_ok=True)
        
        save_path = os.path.join(workdir, f"{cleaned_task_name}.json")
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.diseases import search_diseases_unified

# Perform unified disease search across multiple sources
results, output = search_diseases_unified(
    search_term={repr(search_term)},
    limit_per_source={limit_per_source},
    sources={repr(sources)},
    save_path={repr(save_path)},
)

# Display formatted output
print(output)
"""
        
        # Execute in sandbox if available
        if self.sandbox is not None:
            exit_code, output, artifacts, running_time, peak_memory = self.sandbox.execute(
                language="python",
                code=code_template
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n{output}\n\n"
            result += f"*Execution time: {running_time:.2f}s, Peak memory: {peak_memory:.2f}MB*"
            
            if exit_code != 0:
                result += f"\n\n⚠️ **Warning:** Code exited with non-zero status ({exit_code})"
            
            return result
        else:
            # Fallback: execute locally
            results, output = search_diseases_unified(
                search_term=search_term,
                limit_per_source=limit_per_source,
                sources=sources,
                save_path=save_path,
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n{output}\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result


# =====================================================
# Unified Disease Details Fetch Tool
# =====================================================

class UnifiedDiseaseDetailsFetchToolInput(BaseModel):
    """Input schema for UnifiedDiseaseDetailsFetchTool."""
    
    task_name: str = Field(
        description=(
            "A less than three word description of what the fetch is for. "
            "It will be used to save the results to the sandbox. "
            "Examples: 'diabetes details', 'cancer info', 'MONDO0004992 fetch'"
        )
    )
    disease_id: str = Field(
        description=(
            "Disease identifier of any type: MONDO ID (MONDO:0000000), DOID (DOID:0000000), "
            "OMIM ID (6 digits), MeSH ID (D000000), KEGG Disease ID (H00000), EFO ID (EFO:0000000), or disease name"
        )
    )
    id_type: Optional[str] = Field(
        default=None,
        description=(
            "Type of identifier if known. Options: 'mondo', 'doid', 'omim', 'mesh', "
            "'kegg', 'efo', 'name'. If not specified, will auto-detect."
        )
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of sources to fetch from. Options: 'biothings', 'kegg', 'opentargets'. "
            "If not specified, fetches from all relevant sources."
        )
    )


class UnifiedDiseaseDetailsFetchTool(BaseTool):
    """
    Fetch comprehensive disease details using any disease identifier.
    
    This tool accepts any type of disease identifier and automatically queries
    the appropriate databases to fetch detailed information including:
    - Disease definitions and descriptions
    - Associated genes and pathways
    - Phenotypic information
    - Therapeutic areas and ontology information
    - Cross-database identifiers
    - Related drugs and treatments
    
    Use this tool when you:
    - Have a specific disease ID and need detailed information
    - Need to look up disease details by any identifier type
    - Want comprehensive disease information from multiple sources
    - Need to cross-reference disease information across databases
    - Want to explore disease ontology and therapeutic classification
    """
    
    name: str = "fetch_disease_details"
    description: str = (
        "Fetch comprehensive disease details using any identifier (MONDO, DOID, OMIM, MeSH, KEGG, EFO, or name). "
        "Automatically queries multiple databases (BioThings, KEGG, Open Targets) and returns detailed information including definitions, "
        "associated genes/pathways, phenotypes, therapeutic areas, and cross-database references. "
        "Use this when you have a specific disease ID or name and need detailed comprehensive information."
    )
    args_schema: Type[BaseModel] = UnifiedDiseaseDetailsFetchToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        task_name: str,
        disease_id: str,
        id_type: Optional[str] = None,
        sources: Optional[List[str]] = None,
    ) -> str:
        """Execute the unified disease details fetch."""
        
        # Clean up the task name for the filename
        cleaned_task_name = clean_task_name_for_filename(task_name)
        
        # Determine workdir and create save path
        if self.sandbox is not None:
            workdir = self.sandbox.get_workdir()
        else:
            # Local execution, use current directory
            workdir = os.path.join(os.getcwd(), "workdir")
            # Create the directory if it doesn't exist
            os.makedirs(workdir, exist_ok=True)
        
        save_path = os.path.join(workdir, f"{cleaned_task_name}.json")
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.diseases import fetch_disease_details_unified

# Fetch disease details from multiple sources
details, output = fetch_disease_details_unified(
    disease_id={repr(disease_id)},
    id_type={repr(id_type)},
    sources={repr(sources)},
    save_path={repr(save_path)},
)

# Display formatted output
print(output)
"""
        
        # Execute in sandbox if available
        if self.sandbox is not None:
            exit_code, output, artifacts, running_time, peak_memory = self.sandbox.execute(
                language="python",
                code=code_template
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n{output}\n\n"
            result += f"*Execution time: {running_time:.2f}s, Peak memory: {peak_memory:.2f}MB*"
            
            if exit_code != 0:
                result += f"\n\n⚠️ **Warning:** Code exited with non-zero status ({exit_code})"
            
            return result
        else:
            # Fallback: execute locally
            details, output = fetch_disease_details_unified(
                disease_id=disease_id,
                id_type=id_type,
                sources=sources,
                save_path=save_path,
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n{output}\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result

