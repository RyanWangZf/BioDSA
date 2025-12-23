"""Unified tool wrappers for drug search and information fetching.

This module provides LangChain-compatible tools that aggregate drug information
from multiple sources (BioThings, OpenFDA, KEGG, Open Targets) with a simple interface.
"""

import os
import pandas as pd
from typing import Optional, Type, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper
from biodsa.tools.drugs import search_drugs_unified, fetch_drug_details_unified
from biodsa.tool_wrappers.utils import clean_task_name_for_filename


# =====================================================
# Unified Drug Search Tool
# =====================================================

class UnifiedDrugSearchToolInput(BaseModel):
    """Input schema for UnifiedDrugSearchTool."""
    
    task_name: str = Field(
        description=(
            "A less than three word description of what the search is for. "
            "It will be used to save the search results to the sandbox. "
            "Examples: 'aspirin search', 'PDE4 inhibitors', 'diabetes drugs'"
        )
    )
    search_term: str = Field(
        description=(
            "Drug name, compound name, condition, or any search term. "
            "Examples: 'aspirin', 'imatinib', 'diabetes', 'PDE4 inhibitor'"
        )
    )
    limit_per_source: int = Field(
        default=10,
        description="Maximum number of results to return from each source (1-50)"
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of sources to search. Options: 'biothings', 'openfda_approval', 'openfda_label', 'kegg', 'opentargets'. "
            "If not specified, searches all sources."
        )
    )


class UnifiedDrugSearchTool(BaseTool):
    """
    Unified drug search tool that queries multiple databases simultaneously.
    
    This tool searches across BioThings (MyChem.info), OpenFDA approval data,
    OpenFDA drug labels, KEGG Drug Database, and Open Targets Platform to provide 
    comprehensive drug information from a single simple search term.
    
    Returns aggregated results including:
    - Drug names and identifiers
    - FDA approval status
    - Product labeling information
    - Chemical properties
    - Clinical trial information
    - Cross-database references
    
    Use this tool when you need to:
    - Find drugs by name or search term
    - Get comprehensive drug information from multiple authoritative sources
    - Research drug properties, approvals, or labeling
    - Find drugs for a specific condition or mechanism
    - Check clinical trial phases and drug development status
    """
    
    name: str = "unified_drug_search"
    description: str = (
        "Search for drugs across multiple authoritative databases (BioThings, OpenFDA, KEGG, Open Targets) with a single search term. "
        "Returns comprehensive drug information including names, identifiers, FDA approval status, labeling data, and clinical trial information. "
        "Use this for: finding drugs by name, researching drug properties, checking approval status, "
        "finding drugs for conditions, checking clinical trial phases, or getting comprehensive drug information from multiple sources. "
        "CRITICAL: This is the FIRST tool to use when starting any drug research or when you need broad drug information."
    )
    args_schema: Type[BaseModel] = UnifiedDrugSearchToolInput
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
        """Execute the unified drug search."""
        
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
from biodsa.tools.drugs import search_drugs_unified

# Perform unified drug search across multiple sources
results, output = search_drugs_unified(
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
            results, output = search_drugs_unified(
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
# Unified Drug Details Fetch Tool
# =====================================================

class UnifiedDrugDetailsFetchToolInput(BaseModel):
    """Input schema for UnifiedDrugDetailsFetchTool."""
    
    task_name: str = Field(
        description=(
            "A less than three word description of what the fetch is for. "
            "It will be used to save the results to the sandbox. "
            "Examples: 'aspirin details', 'imatinib info', 'DB00001 fetch'"
        )
    )
    drug_id: str = Field(
        description=(
            "Drug identifier of any type: DrugBank ID (DB#####), ChEBI ID (CHEBI:#####), "
            "ChEMBL ID (CHEMBL#####), PubChem CID (numeric), OpenFDA application (NDA/ANDA/BLA######), "
            "KEGG Drug ID (D#####), or drug name"
        )
    )
    id_type: Optional[str] = Field(
        default=None,
        description=(
            "Type of identifier if known. Options: 'drugbank', 'chebi', 'chembl', 'pubchem', "
            "'kegg', 'openfda_app', 'name'. If not specified, will auto-detect."
        )
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of sources to fetch from. Options: 'biothings', 'openfda_approval', 'openfda_label', 'kegg', 'opentargets'. "
            "If not specified, fetches from all relevant sources."
        )
    )


class UnifiedDrugDetailsFetchTool(BaseTool):
    """
    Fetch comprehensive drug details using any drug identifier.
    
    This tool accepts any type of drug identifier and automatically queries
    the appropriate databases to fetch detailed information including:
    - Chemical properties and structure
    - FDA approval information
    - Product labeling (indications, warnings, interactions)
    - Pharmacological data
    - Clinical trial information and drug development status
    - Cross-database identifiers
    
    Use this tool when you:
    - Have a specific drug ID and need detailed information
    - Need to look up drug details by any identifier type
    - Want comprehensive drug information from multiple sources
    - Need to cross-reference drug information across databases
    - Want to check clinical trial phases and development status
    """
    
    name: str = "fetch_drug_details"
    description: str = (
        "Fetch comprehensive drug details using any identifier (DrugBank, ChEBI, ChEMBL, PubChem, OpenFDA, KEGG, or name). "
        "Automatically queries multiple databases (BioThings, OpenFDA, KEGG, Open Targets) and returns detailed information including chemical properties, "
        "FDA approval data, product labeling, indications, warnings, clinical trial information, and cross-database references. "
        "Use this when you have a specific drug ID or name and need detailed comprehensive information."
    )
    args_schema: Type[BaseModel] = UnifiedDrugDetailsFetchToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        task_name: str,
        drug_id: str,
        id_type: Optional[str] = None,
        sources: Optional[List[str]] = None,
    ) -> str:
        """Execute the unified drug details fetch."""
        
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
from biodsa.tools.drugs import fetch_drug_details_unified

# Fetch drug details from multiple sources
details, output = fetch_drug_details_unified(
    drug_id={repr(drug_id)},
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
            details, output = fetch_drug_details_unified(
                drug_id=drug_id,
                id_type=id_type,
                sources=sources,
                save_path=save_path,
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n{output}\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result
