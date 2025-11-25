"""Unified tool wrappers for biological target search and information fetching.

This module provides LangChain-compatible tools that aggregate target information
from multiple sources (Open Targets, KEGG, Gene Ontology, Human Protein Atlas) with a simple interface.
"""

import os
import pandas as pd
from typing import Optional, Type, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper
from biodsa.tools.targets import search_targets_unified, fetch_target_details_unified
from biodsa.tool_wrappers.utils import clean_task_name_for_filename


# =====================================================
# Unified Target Search Tool
# =====================================================

class UnifiedTargetSearchToolInput(BaseModel):
    """Input schema for UnifiedTargetSearchTool."""
    
    task_name: str = Field(
        description=(
            "A less than three word description of what the search is for. "
            "It will be used to save the search results to the sandbox. "
            "Examples: 'BRCA1 target', 'apoptosis pathway', 'kinase activity'"
        )
    )
    search_term: str = Field(
        description=(
            "Search term for biological targets (target name, gene name, pathway name, GO term, etc.). "
            "Examples: 'BRCA1', 'p53', 'apoptosis', 'protein kinase activity', 'MAPK pathway'"
        )
    )
    search_type: Optional[str] = Field(
        default=None,
        description=(
            "Type of search to perform. Options: 'target', 'pathway', 'go_term', 'gene', or None for all types. "
            "If not specified, searches all types."
        )
    )
    limit_per_source: int = Field(
        default=10,
        description="Maximum number of results to return from each source (1-50)"
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of sources to search. Options: 'opentargets', 'kegg_pathways', 'kegg_genes', 'gene_ontology', 'proteinatlas'. "
            "If not specified, searches all relevant sources based on search_type."
        )
    )


class UnifiedTargetSearchTool(BaseTool):
    """
    Unified biological target search tool that queries multiple databases simultaneously.
    
    This tool searches across Open Targets Platform (therapeutic targets), KEGG 
    (pathways and genes), Gene Ontology (functional annotations), and Human Protein Atlas 
    (protein expression, cancer markers) to provide comprehensive biological target 
    information from a single simple search term.
    
    Returns aggregated results including:
    - Therapeutic target information
    - Pathway associations
    - Gene annotations
    - Functional classifications
    - Protein expression profiles
    - Cancer markers and prognostic information
    - Cross-database references
    
    Use this tool when you need to:
    - Find therapeutic targets by gene name
    - Search for biological pathways
    - Look up functional annotations
    - Explore gene-disease-drug relationships
    - Find cancer markers and prognostic proteins
    - Get protein expression data
    - Get comprehensive target information from multiple authoritative sources
    """
    
    name: str = "unified_target_search"
    description: str = (
        "Search for biological targets (genes, proteins, pathways, GO terms) across multiple authoritative databases "
        "(Open Targets, KEGG, Gene Ontology, Human Protein Atlas) with a single search term. "
        "Returns comprehensive information including therapeutic targets, pathways, functional annotations, protein expression, "
        "cancer markers, prognostic information, and cross-database references. "
        "Use this for: finding therapeutic targets, searching pathways, looking up GO terms, exploring gene functions, "
        "finding cancer markers, getting protein expression data, or getting comprehensive target information from multiple sources. "
        "CRITICAL: This is the PRIMARY tool to use when researching biological targets, pathways, gene functions, or cancer markers."
    )
    args_schema: Type[BaseModel] = UnifiedTargetSearchToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        task_name: str,
        search_term: str,
        search_type: Optional[str] = None,
        limit_per_source: int = 10,
        sources: Optional[List[str]] = None,
    ) -> str:
        """Execute the unified target search."""
        
        # Clean up the task name for the filename
        cleaned_task_name = clean_task_name_for_filename(task_name)
        
        # Determine workdir and create save path
        if self.sandbox is not None:
            workdir = self.sandbox.get_workdir()
        else:
            workdir = os.path.join(os.getcwd(), "workdir")
            os.makedirs(workdir, exist_ok=True)
        
        save_path = os.path.join(workdir, f"{cleaned_task_name}.json")
        
        # Use code execution pattern for consistency with other tools
        code_template = f"""
import json
from biodsa.tools.targets import search_targets_unified

# Perform unified target search
results_dict, formatted_output = search_targets_unified(
    search_term="{search_term}",
    search_type={repr(search_type)},
    limit_per_source={limit_per_source},
    sources={repr(sources)},
    save_path="{save_path}"
)

# Print the formatted output
print(formatted_output)
"""
        
        if self.sandbox is not None:
            result = self.sandbox.execute_code(code_template, timeout=60)
            return result['output'] if 'output' in result else str(result)
        else:
            # Direct execution if no sandbox
            results_dict, formatted_output = search_targets_unified(
                search_term=search_term,
                search_type=search_type,
                limit_per_source=limit_per_source,
                sources=sources,
                save_path=save_path
            )
            return formatted_output


# =====================================================
# Unified Target Details Fetch Tool
# =====================================================

class UnifiedTargetDetailsFetchToolInput(BaseModel):
    """Input schema for UnifiedTargetDetailsFetchTool."""
    
    task_name: str = Field(
        description=(
            "A less than three word description of what the fetch is for. "
            "It will be used to save the results to the sandbox. "
            "Examples: 'BRCA1 details', 'pathway info', 'GO term fetch'"
        )
    )
    target_id: str = Field(
        description=(
            "Target identifier of any type: Ensembl ID (ENSG00000000000), gene symbol (BRCA1), "
            "pathway ID (hsa00010), GO term (GO:0000000), or target name"
        )
    )
    id_type: Optional[str] = Field(
        default=None,
        description=(
            "Type of identifier if known. Options: 'ensembl', 'gene_symbol', 'pathway', 'go_term'. "
            "If not specified, will auto-detect."
        )
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of sources to fetch from. Options: 'opentargets', 'kegg', 'gene_ontology', 'proteinatlas'. "
            "If not specified, fetches from all relevant sources."
        )
    )
    include_associations: bool = Field(
        default=True,
        description="Whether to include target-disease associations (default: True)"
    )


class UnifiedTargetDetailsFetchTool(BaseTool):
    """
    Fetch comprehensive biological target details using any identifier.
    
    This tool accepts any type of target identifier and automatically queries
    the appropriate databases to fetch detailed information including:
    - Target properties and functions
    - Associated diseases and drugs
    - Pathway information
    - Functional annotations
    - Gene ontology classifications
    - Protein expression profiles
    - Cancer pathology and prognostic information
    - Subcellular localization
    - Cross-database identifiers
    
    Use this tool when you:
    - Have a specific target ID and need detailed information
    - Need to look up target details by any identifier type
    - Want comprehensive target information from multiple sources
    - Need to explore target-disease-drug relationships
    - Want to understand biological pathways and functions
    - Need protein expression or cancer pathology data
    """
    
    name: str = "fetch_target_details"
    description: str = (
        "Fetch comprehensive biological target details using any identifier (Ensembl ID, gene symbol, pathway ID, GO term). "
        "Automatically queries multiple databases (Open Targets, KEGG, Gene Ontology, Human Protein Atlas) and returns detailed information including "
        "target functions, associated diseases/drugs, pathways, functional annotations, protein expression, cancer pathology, "
        "subcellular localization, and cross-database references. "
        "Use this when you have a specific target ID or name and need detailed comprehensive information."
    )
    args_schema: Type[BaseModel] = UnifiedTargetDetailsFetchToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        task_name: str,
        target_id: str,
        id_type: Optional[str] = None,
        sources: Optional[List[str]] = None,
        include_associations: bool = True,
    ) -> str:
        """Execute the unified target details fetch."""
        
        # Clean up the task name for the filename
        cleaned_task_name = clean_task_name_for_filename(task_name)
        
        # Determine workdir and create save path
        if self.sandbox is not None:
            workdir = self.sandbox.get_workdir()
        else:
            workdir = os.path.join(os.getcwd(), "workdir")
            os.makedirs(workdir, exist_ok=True)
        
        save_path = os.path.join(workdir, f"{cleaned_task_name}.json")
        
        # Use code execution pattern for consistency with other tools
        code_template = f"""
import json
from biodsa.tools.targets import fetch_target_details_unified

# Fetch unified target details
details_dict, formatted_output = fetch_target_details_unified(
    target_id="{target_id}",
    id_type={repr(id_type)},
    sources={repr(sources)},
    include_associations={include_associations},
    save_path="{save_path}"
)

# Print the formatted output
print(formatted_output)
"""
        
        if self.sandbox is not None:
            result = self.sandbox.execute_code(code_template, timeout=60)
            return result['output'] if 'output' in result else str(result)
        else:
            # Direct execution if no sandbox
            details_dict, formatted_output = fetch_target_details_unified(
                target_id=target_id,
                id_type=id_type,
                sources=sources,
                include_associations=include_associations,
                save_path=save_path
            )
            return formatted_output

