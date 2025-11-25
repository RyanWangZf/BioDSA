from typing import Literal, Type, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import json

from biodsa.tools.gene_set.get_pathway_for_gene_set import get_pathway_for_gene_set
from biodsa.tools.gene_set.get_enrichment_for_gene_set import get_enrichment_for_gene_set
from biodsa.tools.gene_set.get_interactions_for_gene_set import get_interactions_for_gene_set
from biodsa.tools.gene_set.get_complex_for_gene_set import get_complex_for_gene_set
from biodsa.tools.gene_set.get_gene_summary_for_single_gene import get_gene_summary_for_single_gene
from biodsa.tools.gene_set.get_disease_for_single_gene import get_disease_for_single_gene
from biodsa.tools.gene_set.get_domain_for_single_gene import get_domain_for_single_gene
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper
from biodsa.tool_wrappers.utils import run_python_repl

__all__ = [
    "GetPathwayForGeneSetTool",
    "GetEnrichmentForGeneSetTool",
    "GetInteractionsForGeneSetTool",
    "GetComplexForGeneSetTool",
    "GetGeneSummaryForSingleGeneTool",
    "GetDiseaseForSingleGeneTool",
    "GetDomainForSingleGeneTool",
    "GetPathwayForGeneSetToolInput",
    "GetEnrichmentForGeneSetToolInput",
    "GetInteractionsForGeneSetToolInput",
    "GetComplexForGeneSetToolInput",
    "GetGeneSummaryForSingleGeneToolInput",
    "GetDiseaseForSingleGeneToolInput",
    "GetDomainForSingleGeneToolInput",
]

# =====================================================
# Tool 1: Get Pathway for Gene Set
# =====================================================
class GetPathwayForGeneSetToolInput(BaseModel):
    """Input schema for GetPathwayForGeneSetTool."""
    gene_set: str = Field(
        ...,
        description="A gene set separated only by comma ',' (no whitespace). For example: 'BRCA1,TP53,EGFR'."
    )


class GetPathwayForGeneSetTool(BaseTool):
    """
    Tool to get biological pathway annotations for a gene set.
    
    This tool queries multiple pathway databases (KEGG, Reactome, BioPlanet, MSigDB Hallmark)
    via Enrichr API and returns the top-5 enriched pathways with overlapping genes.
    """
    name: str = "get_pathway_for_gene_set"
    description: str = (
        "Get top-5 biological pathway names for a given gene set. "
        "Queries KEGG, Reactome, BioPlanet, and MSigDB Hallmark databases. "
        "Returns pathway terms, overlapping genes, and source database. "
        "Useful for understanding biological pathways associated with a set of genes."
    )
    args_schema: Type[BaseModel] = GetPathwayForGeneSetToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(self, gene_set: str) -> str:
        """Execute the tool to get pathway annotations."""
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.gene_set.get_pathway_for_gene_set import get_pathway_for_gene_set

# Get pathway annotations for gene set
results = get_pathway_for_gene_set({repr(gene_set)})

# Output results
print(results)
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
# Tool 2: Get Enrichment for Gene Set
# =====================================================
class GetEnrichmentForGeneSetToolInput(BaseModel):
    """Input schema for GetEnrichmentForGeneSetTool."""
    gene_set: str = Field(
        ...,
        description="A gene set separated only by comma ',' (no whitespace). For example: 'BRCA1,TP53,EGFR'."
    )


class GetEnrichmentForGeneSetTool(BaseTool):
    """
    Tool to perform functional enrichment analysis for a gene set.
    
    This tool uses g:Profiler API to perform enrichment analysis across multiple
    functional databases including GO, KEGG, Reactome, and more.
    """
    name: str = "get_enrichment_for_gene_set"
    description: str = (
        "Get top-5 enrichment function names for a gene set, including biological regulation, "
        "signaling, and metabolism. Uses g:Profiler for comprehensive enrichment analysis. "
        "Returns enriched terms with statistics and gene overlaps."
    )
    args_schema: Type[BaseModel] = GetEnrichmentForGeneSetToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(self, gene_set: str) -> str:
        """Execute the tool to get enrichment analysis."""
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.gene_set.get_enrichment_for_gene_set import get_enrichment_for_gene_set

# Get enrichment analysis for gene set
results = get_enrichment_for_gene_set({repr(gene_set)})

# Output results
print(results)
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
# Tool 3: Get Interactions for Gene Set
# =====================================================
class GetInteractionsForGeneSetToolInput(BaseModel):
    """Input schema for GetInteractionsForGeneSetTool."""
    gene_set: str = Field(
        ...,
        description="A gene set delimited with comma. For example: 'BRCA1,TP53,EGFR'."
    )


class GetInteractionsForGeneSetTool(BaseTool):
    """
    Tool to get protein-protein interaction information for a gene set.
    
    This tool queries the PubTator3 API to retrieve protein-protein interactions
    for the given genes, returning up to 50 interactions.
    """
    name: str = "get_interactions_for_gene_set"
    description: str = (
        "Get information on interacting genes for a given gene set. "
        "Returns protein-protein interactions from literature mining via PubTator3. "
        "Useful for understanding gene networks and interaction partners."
    )
    args_schema: Type[BaseModel] = GetInteractionsForGeneSetToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(self, gene_set: str) -> str:
        """Execute the tool to get gene interactions."""
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.gene_set.get_interactions_for_gene_set import get_interactions_for_gene_set

# Get interactions for gene set
results = get_interactions_for_gene_set({repr(gene_set)})

# Output results
print(results)
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
# Tool 4: Get Complex for Gene Set
# =====================================================
class GetComplexForGeneSetToolInput(BaseModel):
    """Input schema for GetComplexForGeneSetTool."""
    gene_set: str = Field(
        ...,
        description="A gene set delimited only with comma ',' (no whitespace). For example: 'BRCA1,TP53,EGFR'."
    )


class GetComplexForGeneSetTool(BaseTool):
    """
    Tool to get protein complex information for a gene set.
    
    This tool queries the PubTator3 API to retrieve protein complex information,
    including complex protocol IDs and corresponding complex names.
    """
    name: str = "get_complex_for_gene_set"
    description: str = (
        "Get information on all possible protein complex protocol IDs and corresponding "
        "complex names for a given gene set. Returns complex annotations from PubTator3. "
        "Useful for identifying protein complexes that genes may participate in."
    )
    args_schema: Type[BaseModel] = GetComplexForGeneSetToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(self, gene_set: str) -> str:
        """Execute the tool to get protein complex information."""
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.gene_set.get_complex_for_gene_set import get_complex_for_gene_set

# Get complex information for gene set
results = get_complex_for_gene_set({repr(gene_set)})

# Output results
print(results)
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
# Tool 5: Get Gene Summary for Single Gene
# =====================================================
class GetGeneSummaryForSingleGeneToolInput(BaseModel):
    """Input schema for GetGeneSummaryForSingleGeneTool."""
    gene_name: str = Field(
        ...,
        description="A single gene name to search. For example: 'BRCA1'."
    )
    specie: Literal["Homo", "Mus"] = Field(
        ...,
        description="Species name. Either 'Homo' (human) or 'Mus' (mouse)."
    )


class GetGeneSummaryForSingleGeneTool(BaseTool):
    """
    Tool to get comprehensive summary information for a single gene.
    
    This tool queries NCBI Gene database via E-utilities to retrieve gene summary
    information including function, location, aliases, and other metadata.
    """
    name: str = "get_gene_summary_for_single_gene"
    description: str = (
        "Get summary information on a single gene including function, location, aliases, "
        "and other metadata. Queries NCBI Gene database for comprehensive gene information. "
        "Supports human (Homo) and mouse (Mus) species."
    )
    args_schema: Type[BaseModel] = GetGeneSummaryForSingleGeneToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(self, gene_name: str, specie: Literal["Homo", "Mus"]) -> str:
        """Execute the tool to get gene summary."""
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.gene_set.get_gene_summary_for_single_gene import get_gene_summary_for_single_gene
import json

# Get gene summary
results = get_gene_summary_for_single_gene({repr(gene_name)}, {repr(specie)})

# Output results
if results is None:
    print(f"No summary found for gene '{{gene_name}}' in species '{{specie}}'.")
else:
    print(json.dumps(results, indent=2))
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
# Tool 6: Get Disease for Single Gene
# =====================================================
class GetDiseaseForSingleGeneToolInput(BaseModel):
    """Input schema for GetDiseaseForSingleGeneTool."""
    gene_name: str = Field(
        ...,
        description="A single gene name to search. For example: 'BRCA1'."
    )


class GetDiseaseForSingleGeneTool(BaseTool):
    """
    Tool to get disease associations for a single gene.
    
    This tool queries the PubTator API to retrieve disease associations for a gene,
    including disease IDs and corresponding disease names from literature.
    """
    name: str = "get_disease_for_single_gene"
    description: str = (
        "Get information on related diseases for a given gene, including disease IDs "
        "and corresponding disease names. Queries PubTator API for gene-disease associations "
        "from literature mining. Returns up to 100 disease associations."
    )
    args_schema: Type[BaseModel] = GetDiseaseForSingleGeneToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(self, gene_name: str) -> str:
        """Execute the tool to get disease associations."""
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.gene_set.get_disease_for_single_gene import get_disease_for_single_gene

# Get disease associations for gene
results = get_disease_for_single_gene({repr(gene_name)})

# Output results
print(results)
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
# Tool 7: Get Domain for Single Gene
# =====================================================
class GetDomainForSingleGeneToolInput(BaseModel):
    """Input schema for GetDomainForSingleGeneTool."""
    gene_name: str = Field(
        ...,
        description="A single gene name to search. For example: 'BRCA1'."
    )


class GetDomainForSingleGeneTool(BaseTool):
    """
    Tool to get protein domain information for a single gene.
    
    This tool queries the PubTator API's conserved domain database (CDD) to retrieve
    information about protein domains, including domain IDs and names.
    """
    name: str = "get_domain_for_single_gene"
    description: str = (
        "Get information on related biological protein domains for a given gene, "
        "including domain IDs and corresponding domain names. Queries PubTator CDD API "
        "for conserved domain information. Returns up to 10 domain annotations."
    )
    args_schema: Type[BaseModel] = GetDomainForSingleGeneToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(self, gene_name: str) -> str:
        """Execute the tool to get protein domain information."""
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.gene_set.get_domain_for_single_gene import get_domain_for_single_gene

# Get domain information for gene
results = get_domain_for_single_gene({repr(gene_name)})

# Output results
print(results)
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

