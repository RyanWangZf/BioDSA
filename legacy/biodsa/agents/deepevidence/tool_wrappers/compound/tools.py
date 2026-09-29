"""Unified tool wrappers for compound search and information fetching.

This module provides LangChain-compatible tools that aggregate compound information
from multiple sources (KEGG Compound, PubChem) with a simple interface.
"""

import os
from typing import Optional, Type, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper
from biodsa.tools.compound import search_compounds_unified, fetch_compound_details_unified
from biodsa.tool_wrappers.utils import clean_task_name_for_filename


# =====================================================
# Unified Compound Search Tool
# =====================================================

class UnifiedCompoundSearchToolInput(BaseModel):
    """Input schema for UnifiedCompoundSearchTool."""
    
    task_name: str = Field(
        description=(
            "A less than three word description of what the search is for. "
            "It will be used to save the search results to the sandbox. "
            "Examples: 'aspirin search', 'glucose compounds', 'ATP search'"
        )
    )
    search_term: str = Field(
        description=(
            "Search term for chemical compounds (compound name, CAS number, formula, SMILES, etc.). "
            "Examples: 'aspirin', 'C9H8O4', '50-78-2', 'glucose', 'ATP'"
        )
    )
    search_type: Optional[str] = Field(
        default="name",
        description=(
            "Type of search to perform. Options: 'name', 'formula', 'smiles', 'inchi', 'cas'. Default: 'name'"
        )
    )
    limit_per_source: int = Field(
        default=10,
        description="Maximum number of results to return from each source (1-100, default: 10)"
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of sources to search. Options: 'kegg', 'pubchem'. "
            "If not specified, searches all sources."
        )
    )


class UnifiedCompoundSearchTool(BaseTool):
    """
    Unified chemical compound search tool that queries KEGG and PubChem simultaneously.
    
    This tool searches across:
    - KEGG Compound Database (metabolites, drugs, natural products)
    - PubChem (comprehensive chemical database with >100M structures)
    
    Returns aggregated results including:
    - Compound names and identifiers
    - Chemical formulas and structures
    - Molecular weights and properties
    - Synonyms and cross-references
    
    Use this tool when you need to:
    - Find compounds by name or identifier
    - Search by chemical formula or structure
    - Look up metabolites or drugs
    - Get comprehensive compound information from multiple authoritative sources
    """
    
    name: str = "unified_compound_search"
    description: str = (
        "Search for chemical compounds across KEGG Compound and PubChem databases. "
        "Returns comprehensive information including compound names, identifiers, chemical formulas, "
        "molecular properties, and synonyms. "
        "Use this for: finding compounds by name, searching by chemical structure, looking up metabolites, "
        "or getting comprehensive compound information from multiple sources. "
        "CRITICAL: This is the PRIMARY tool to use when researching chemical compounds or metabolites."
    )
    args_schema: Type[BaseModel] = UnifiedCompoundSearchToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        task_name: str,
        search_term: str,
        search_type: Optional[str] = "name",
        limit_per_source: int = 10,
        sources: Optional[List[str]] = None,
    ) -> str:
        """Execute the unified compound search."""
        
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
from biodsa.tools.compound import search_compounds_unified

# Perform unified compound search across multiple sources
results, output = search_compounds_unified(
    search_term={repr(search_term)},
    search_type={repr(search_type)},
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
            results, output = search_compounds_unified(
                search_term=search_term,
                search_type=search_type,
                limit_per_source=limit_per_source,
                sources=sources,
                save_path=save_path,
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n{output}\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result


# =====================================================
# Compound Details Fetch Tool
# =====================================================

class UnifiedCompoundDetailsFetchToolInput(BaseModel):
    """Input schema for CompoundDetailsFetchTool."""
    
    task_name: str = Field(
        description=(
            "A less than three word description of what the fetch is for. "
            "It will be used to save the results to the sandbox. "
            "Examples: 'aspirin details', 'glucose info', 'ATP properties'"
        )
    )
    compound_id: str = Field(
        description=(
            "Compound identifier. Can be: "
            "- KEGG compound ID (e.g., 'C00002', 'cpd:C00002')"
            "- PubChem CID (e.g., '2244', 'CID:2244')"
            "- Compound name for search"
        )
    )
    id_type: Optional[str] = Field(
        default=None,
        description=(
            "Type of identifier if known. Options: 'kegg', 'pubchem', 'name'. "
            "If not specified, will auto-detect."
        )
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of sources to fetch from. Options: 'kegg', 'pubchem'. "
            "If not specified, fetches from relevant sources."
        )
    )


class UnifiedCompoundDetailsFetchTool(BaseTool):
    """
    Fetch comprehensive chemical compound details using compound identifiers.
    
    This tool accepts KEGG compound IDs or PubChem CIDs and automatically queries
    the appropriate databases to fetch detailed information including:
    - Compound name and synonyms
    - Chemical structure (SMILES, InChI)
    - Molecular formula and weight
    - Chemical properties (LogP, TPSA, etc.)
    - Related reactions and pathways (KEGG)
    - Cross-database references
    
    Use this tool when you:
    - Have a specific compound ID and need detailed information
    - Need to explore compound properties and structure
    - Want comprehensive compound information from KEGG or PubChem
    """
    
    name: str = "unified_compound_details_fetch"
    description: str = (
        "Fetch comprehensive chemical compound details using KEGG compound ID or PubChem CID. "
        "Automatically detects identifier type and queries the appropriate database. "
        "Returns detailed information including compound name, structure, properties, reactions, and pathways. "
        "Use this when you have a specific compound ID (e.g., C00002, 2244) and need detailed information."
    )
    args_schema: Type[BaseModel] = UnifiedCompoundDetailsFetchToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        task_name: str,
        compound_id: str,
        id_type: Optional[str] = None,
        sources: Optional[List[str]] = None,
    ) -> str:
        """Execute the compound details fetch."""
        
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
from biodsa.tools.compound import fetch_compound_details_unified

# Fetch compound details from multiple sources
details, output = fetch_compound_details_unified(
    compound_id={repr(compound_id)},
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
            details, output = fetch_compound_details_unified(
                compound_id=compound_id,
                id_type=id_type,
                sources=sources,
                save_path=save_path,
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n{output}\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result
