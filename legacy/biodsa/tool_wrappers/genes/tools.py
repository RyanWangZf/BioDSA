"""Unified tool wrappers for gene search and information fetching.

This module provides LangChain-compatible tools that aggregate gene information
from multiple sources (BioThings MyGene.info, BioThings MyVariant.info, KEGG) with a simple interface.
"""

import os
import pandas as pd
from typing import Optional, Type, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper
from biodsa.tools.genes import search_genes_unified, fetch_gene_details_unified
from biodsa.tool_wrappers.utils import clean_task_name_for_filename


# =====================================================
# Unified Gene Search Tool
# =====================================================

class UnifiedGeneSearchToolInput(BaseModel):
    """Input schema for UnifiedGeneSearchTool."""
    
    task_name: str = Field(
        description=(
            "A less than three word description of what the search is for. "
            "It will be used to save the search results to the sandbox. "
            "Examples: 'BRCA1 search', 'cancer genes', 'kinase search'"
        )
    )
    search_term: str = Field(
        description=(
            "Gene symbol, name, or any search term. "
            "Examples: 'BRCA1', 'TP53', 'kinase', 'tumor suppressor'"
        )
    )
    limit_per_source: int = Field(
        default=10,
        description="Maximum number of results to return from each source (1-50)"
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of sources to search. Options: 'biothings', 'kegg', 'opentargets', 'variants'. "
            "If not specified, searches biothings, kegg, and opentargets (use include_variants for variants)."
        )
    )
    include_variants: bool = Field(
        default=False,
        description="Whether to include variant search (searches for variants in genes matching the search term)"
    )


class UnifiedGeneSearchTool(BaseTool):
    """
    Unified gene search tool that queries multiple databases simultaneously.
    
    This tool searches across BioThings (MyGene.info), KEGG Gene Database, 
    Open Targets Platform, and optionally MyVariant.info to provide comprehensive 
    gene information from a single simple search term.
    
    Returns aggregated results including:
    - Gene names, symbols, and identifiers
    - Gene summaries and descriptions
    - Therapeutic target information
    - Associated variants (if include_variants=True)
    - Cross-database references
    
    Use this tool when you need to:
    - Find genes by symbol or name
    - Get comprehensive gene information from multiple authoritative sources
    - Research gene properties, functions, or pathways
    - Find therapeutic target information
    - Find genes related to specific biological processes
    - Optionally search for variants in specific genes
    """
    
    name: str = "unified_gene_search"
    description: str = (
        "Search for genes across multiple authoritative databases (BioThings MyGene.info, KEGG, Open Targets) with a single search term. "
        "Returns comprehensive gene information including symbols, names, summaries, therapeutic target data, and cross-database identifiers. "
        "Can optionally include variant information from MyVariant.info. "
        "Use this for: finding genes by symbol/name, researching gene properties, checking gene functions/pathways, "
        "finding therapeutic targets, finding genes for biological processes, or getting comprehensive gene information from multiple sources. "
        "CRITICAL: This is the FIRST tool to use when starting any gene research or when you need broad gene information."
    )
    args_schema: Type[BaseModel] = UnifiedGeneSearchToolInput
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
        include_variants: bool = False,
    ) -> str:
        """Execute the unified gene search."""
        
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
from biodsa.tools.genes import search_genes_unified

# Perform unified gene search across multiple sources
results, output = search_genes_unified(
    search_term={repr(search_term)},
    limit_per_source={limit_per_source},
    sources={repr(sources)},
    include_variants={include_variants},
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
            results, output = search_genes_unified(
                search_term=search_term,
                limit_per_source=limit_per_source,
                sources=sources,
                include_variants=include_variants,
                save_path=save_path,
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n{output}\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result


# =====================================================
# Unified Gene Details Fetch Tool
# =====================================================

class UnifiedGeneDetailsFetchToolInput(BaseModel):
    """Input schema for UnifiedGeneDetailsFetchTool."""
    
    task_name: str = Field(
        description=(
            "A less than three word description of what the fetch is for. "
            "It will be used to save the results to the sandbox. "
            "Examples: 'BRCA1 details', 'TP53 info', 'gene fetch'"
        )
    )
    gene_id: str = Field(
        description=(
            "Gene identifier of any type: Gene symbol (BRCA1, TP53), Entrez ID (672, 7157), "
            "Ensembl ID (ENSG00000012048), KEGG ID (hsa:672), or gene name"
        )
    )
    id_type: Optional[str] = Field(
        default=None,
        description=(
            "Type of identifier if known. Options: 'symbol', 'entrez', 'ensembl', "
            "'kegg', 'name'. If not specified, will auto-detect."
        )
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of sources to fetch from. Options: 'biothings', 'kegg', 'opentargets', 'variants'. "
            "If not specified, fetches from biothings, kegg, and opentargets (use include_variants for variants)."
        )
    )
    include_variants: bool = Field(
        default=False,
        description="Whether to fetch variants associated with the gene"
    )


class UnifiedGeneDetailsFetchTool(BaseTool):
    """
    Fetch comprehensive gene details using any gene identifier.
    
    This tool accepts any type of gene identifier and automatically queries
    the appropriate databases to fetch detailed information including:
    - Gene symbols, names, and descriptions
    - Gene functions and pathways
    - Associated diseases
    - Therapeutic target information from Open Targets
    - Cross-database identifiers
    - Optionally: associated variants from MyVariant.info
    
    Use this tool when you:
    - Have a specific gene ID and need detailed information
    - Need to look up gene details by any identifier type
    - Want comprehensive gene information from multiple sources
    - Need to cross-reference gene information across databases
    - Want therapeutic target and tractability information
    - Want to find variants associated with a specific gene
    """
    
    name: str = "fetch_gene_details"
    description: str = (
        "Fetch comprehensive gene details using any identifier (Gene symbol, Entrez, Ensembl, KEGG, or name). "
        "Automatically queries multiple databases (BioThings, KEGG, Open Targets) and returns detailed information including functions, "
        "pathways, associated diseases, therapeutic target data, and cross-database references. Can optionally include variant information. "
        "Use this when you have a specific gene ID or name and need detailed comprehensive information."
    )
    args_schema: Type[BaseModel] = UnifiedGeneDetailsFetchToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        task_name: str,
        gene_id: str,
        id_type: Optional[str] = None,
        sources: Optional[List[str]] = None,
        include_variants: bool = False,
    ) -> str:
        """Execute the unified gene details fetch."""
        
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
from biodsa.tools.genes import fetch_gene_details_unified

# Fetch gene details from multiple sources
details, output = fetch_gene_details_unified(
    gene_id={repr(gene_id)},
    id_type={repr(id_type)},
    sources={repr(sources)},
    include_variants={include_variants},
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
            details, output = fetch_gene_details_unified(
                gene_id=gene_id,
                id_type=id_type,
                sources=sources,
                include_variants=include_variants,
                save_path=save_path,
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n{output}\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result

