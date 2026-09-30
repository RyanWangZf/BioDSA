"""Unified tool wrappers for biological pathway search and information fetching.

This module provides LangChain-compatible tools that aggregate pathway information
from multiple sources (KEGG pathways, Gene Ontology biological processes) with a simple interface.
"""

import os
from typing import Optional, Type, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper
from biodsa.tools.pathway import search_pathways_unified, fetch_pathway_details_unified
from biodsa.tool_wrappers.utils import clean_task_name_for_filename


# =====================================================
# Unified Pathway Search Tool
# =====================================================

class UnifiedPathwaySearchToolInput(BaseModel):
    """Input schema for UnifiedPathwaySearchTool."""
    
    task_name: str = Field(
        description=(
            "A less than three word description of what the search is for. "
            "It will be used to save the search results to the sandbox. "
            "Examples: 'apoptosis pathways', 'MAPK signaling', 'glycolysis search'"
        )
    )
    search_term: str = Field(
        description=(
            "Search term for biological pathways (pathway name, biological process, metabolic pathway, etc.). "
            "Examples: 'apoptosis', 'MAPK signaling pathway', 'glycolysis', 'cell cycle', 'immune response'"
        )
    )
    limit_per_source: int = Field(
        default=20,
        description="Maximum number of results to return from each source (1-100, default: 20)"
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of sources to search. Options: 'kegg', 'go'. "
            "If not specified, searches all sources."
        )
    )


class UnifiedPathwaySearchTool(BaseTool):
    """
    Unified biological pathway search tool that queries KEGG and Gene Ontology simultaneously.
    
    This tool searches across:
    - KEGG Pathways (metabolic pathways, signaling pathways, disease pathways)
    - Gene Ontology Biological Processes (functional annotations, biological processes)
    
    Returns aggregated results including:
    - Pathway names and identifiers
    - Pathway descriptions
    - Associated genes and proteins
    - Pathway categories and hierarchies
    
    Use this tool when you need to:
    - Find pathways by name or keyword
    - Search for biological processes
    - Explore metabolic or signaling pathways
    - Get comprehensive pathway information from multiple authoritative sources
    """
    
    name: str = "unified_pathway_search"
    description: str = (
        "Search for biological pathways and processes across KEGG and Gene Ontology databases. "
        "Returns comprehensive information including pathway names, descriptions, and associated genes. "
        "Use this for: finding pathways by name, searching biological processes, exploring metabolic pathways, "
        "or getting comprehensive pathway information from multiple sources. "
        "CRITICAL: This is the PRIMARY tool to use when researching biological pathways or processes."
    )
    args_schema: Type[BaseModel] = UnifiedPathwaySearchToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        task_name: str,
        search_term: str,
        limit_per_source: int = 20,
        sources: Optional[List[str]] = None,
    ) -> str:
        """Execute the unified pathway search."""
        
        # Clean up the task name for the filename
        cleaned_task_name = clean_task_name_for_filename(task_name)
        
        # Determine workdir and create save path
        if self.sandbox is not None:
            workdir = self.sandbox.get_workdir()
        else:
            workdir = os.path.join(os.getcwd(), "workdir")
            os.makedirs(workdir, exist_ok=True)
        
        save_path = os.path.join(workdir, f"{cleaned_task_name}.json")
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.pathway import search_pathways_unified

# Perform unified pathway search across multiple sources
results, output = search_pathways_unified(
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
            results, output = search_pathways_unified(
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
# Pathway Details Fetch Tool
# =====================================================

class UnifiedPathwayDetailsFetchToolInput(BaseModel):
    """Input schema for UnifiedPathwayDetailsFetchTool."""
    
    task_name: str = Field(
        description=(
            "A less than three word description of what the fetch is for. "
            "It will be used to save the results to the sandbox. "
            "Examples: 'apoptosis details', 'MAPK info', 'pathway genes'"
        )
    )
    pathway_id: str = Field(
        description=(
            "Pathway identifier. Can be: "
            "- KEGG pathway ID (e.g., 'hsa04210', 'map00010')"
            "- GO term ID (e.g., 'GO:0006915')"
        )
    )
    id_type: Optional[str] = Field(
        default=None,
        description=(
            "Type of identifier if known. Options: 'kegg', 'go'. "
            "If not specified, will auto-detect."
        )
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of sources to fetch from. Options: 'kegg', 'go'. "
            "If not specified, fetches from relevant sources."
        )
    )
    include_genes: bool = Field(
        default=True,
        description="Whether to include genes/proteins associated with the pathway (default: True)"
    )
    include_compounds: bool = Field(
        default=True,
        description="Whether to include compounds in the pathway (default: True, KEGG only)"
    )


class UnifiedPathwayDetailsFetchTool(BaseTool):
    """
    Fetch comprehensive biological pathway details using pathway identifiers.
    
    This tool accepts KEGG pathway IDs or GO term IDs and automatically queries
    the appropriate databases to fetch detailed information including:
    - Pathway/process name and description
    - Associated genes and proteins
    - Pathway hierarchy and relationships
    - Compounds and metabolites (KEGG)
    - GO annotations and evidence codes
    - Pathway diagrams and visualization URLs
    
    Use this tool when you:
    - Have a specific pathway ID and need detailed information
    - Need to explore pathway components (genes, compounds)
    - Want to understand pathway relationships and hierarchies
    """
    
    name: str = "unified_pathway_details_fetch"
    description: str = (
        "Fetch comprehensive biological pathway details using KEGG pathway ID or GO term ID. "
        "Automatically detects identifier type and queries the appropriate database. "
        "Returns detailed information including pathway name, description, associated genes/proteins, and compounds. "
        "Use this when you have a specific pathway ID (e.g., hsa04210, GO:0006915) and need detailed information."
    )
    args_schema: Type[BaseModel] = UnifiedPathwayDetailsFetchToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        task_name: str,
        pathway_id: str,
        id_type: Optional[str] = None,
        sources: Optional[List[str]] = None,
        include_genes: bool = True,
        include_compounds: bool = True,
    ) -> str:
        """Execute the pathway details fetch."""
        
        # Clean up the task name for the filename
        cleaned_task_name = clean_task_name_for_filename(task_name)
        
        # Determine workdir and create save path
        if self.sandbox is not None:
            workdir = self.sandbox.get_workdir()
        else:
            workdir = os.path.join(os.getcwd(), "workdir")
            os.makedirs(workdir, exist_ok=True)
        
        save_path = os.path.join(workdir, f"{cleaned_task_name}.json")
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.pathway import fetch_pathway_details_unified

# Fetch pathway details from multiple sources
details, output = fetch_pathway_details_unified(
    pathway_id={repr(pathway_id)},
    id_type={repr(id_type)},
    sources={repr(sources)},
    include_genes={include_genes},
    include_compounds={include_compounds},
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
            details, output = fetch_pathway_details_unified(
                pathway_id=pathway_id,
                id_type=id_type,
                sources=sources,
                include_genes=include_genes,
                include_compounds=include_compounds,
                save_path=save_path,
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n{output}\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result
