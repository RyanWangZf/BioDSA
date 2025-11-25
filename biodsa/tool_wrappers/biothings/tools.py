from typing import List, Optional, Dict, Any, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import pandas as pd

from biodsa.tools.biothings.diseases import (
    search_diseases,
    fetch_disease_details_by_ids,
)
from biodsa.tools.biothings.drugs import (
    search_drugs,
    fetch_drug_details_by_ids,
)
from biodsa.tools.biothings.genes import (
    search_genes,
    fetch_gene_details_by_ids,
)
from biodsa.tools.biothings.variants import (
    search_variants,
    fetch_variant_details_by_ids,
)
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper


def execute_in_sandbox_or_local(sandbox, code_template: str, local_func, local_args: dict) -> str:
    """
    Helper function to execute code in sandbox or locally with consistent output format.
    
    Args:
        sandbox: ExecutionSandboxWrapper instance or None
        code_template: Python code string to execute
        local_func: Function to call if no sandbox available
        local_args: Arguments to pass to local_func
        
    Returns:
        Formatted string with code and output
    """
    if sandbox is not None:
        # Execute in sandbox
        exit_code, output, artifacts, running_time, peak_memory = sandbox.execute(
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
        # Execute locally
        output = local_func(**local_args)
        
        result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
        result += f"### Output:\n```\n{output}\n```\n\n"
        result += "*Executed locally (no sandbox)*"
        
        return result

__all__ = [
    # Disease tools
    "SearchDiseasesTool",
    "FetchDiseaseDetailsTool",
    "SearchDiseasesToolInput",
    "FetchDiseaseDetailsToolInput",
    # Drug tools
    "SearchDrugsTool",
    "FetchDrugDetailsTool",
    "SearchDrugsToolInput",
    "FetchDrugDetailsToolInput",
    # Gene tools
    "SearchGenesTool",
    "FetchGeneDetailsTool",
    "SearchGenesToolInput",
    "FetchGeneDetailsToolInput",
    # Variant tools
    "SearchVariantsTool",
    "FetchVariantDetailsTool",
    "SearchVariantsToolInput",
    "FetchVariantDetailsToolInput",
]


# =====================================================
# Disease Tools
# =====================================================
class SearchDiseasesToolInput(BaseModel):
    """Input schema for SearchDiseasesTool."""
    
    search: Optional[str] = Field(
        default=None,
        description="General search term to query across all fields"
    )
    name: Optional[str] = Field(
        default=None,
        description="Disease name (e.g., 'breast cancer', 'diabetes mellitus')"
    )
    mondo_id: Optional[str] = Field(
        default=None,
        description="MONDO ID (e.g., 'MONDO:0004992' for cancer)"
    )
    doid: Optional[str] = Field(
        default=None,
        description="Disease Ontology ID (e.g., 'DOID:162' for cancer)"
    )
    omim_id: Optional[str] = Field(
        default=None,
        description="OMIM ID for genetic diseases"
    )
    mesh_id: Optional[str] = Field(
        default=None,
        description="MeSH ID for medical subject headings"
    )
    limit: int = Field(
        default=100,
        description="Maximum number of results to return (1-1000)"
    )
    skip: int = Field(
        default=0,
        description="Number of results to skip for pagination"
    )
    save_path: Optional[str] = Field(
        default=None,
        description="Path to save the search results"
    )


class SearchDiseasesTool(BaseTool):
    """
    Tool to search for diseases using MyDisease.info API.
    
    This comprehensive search tool allows searching by:
    - Disease names and general terms
    - Disease ontology identifiers (MONDO, DOID, OMIM, MeSH)
    - Synonyms and related terms
    
    Returns detailed disease information including names, definitions, synonyms,
    and cross-references to multiple disease databases.
    """
    
    name: str = "search_diseases"
    description: str = (
        "Search for diseases and medical conditions using MyDisease.info. "
        "Find diseases by name, general search terms, or specific identifiers (MONDO, DOID, OMIM, MeSH). "
        "Returns disease information including names, definitions, synonyms, and database cross-references. "
        "CRITICAL USE: When researching medical conditions, disease classification, "
        "finding disease identifiers, or exploring disease relationships and synonyms."
    )
    args_schema: Type[BaseModel] = SearchDiseasesToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        search: Optional[str] = None,
        name: Optional[str] = None,
        mondo_id: Optional[str] = None,
        doid: Optional[str] = None,
        omim_id: Optional[str] = None,
        mesh_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
        save_path: Optional[str] = None,
    ) -> str:
        """Execute the tool to search diseases."""
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.biothings.diseases import search_diseases
import pandas as pd

# Search for diseases
df, summary = search_diseases(
    search={repr(search)},
    name={repr(name)},
    mondo_id={repr(mondo_id)},
    doid={repr(doid)},
    omim_id={repr(omim_id)},
    mesh_id={repr(mesh_id)},
    limit={limit},
    skip={skip},
    save_path={repr(save_path)},
)

# Generate output
if df is None or len(df) == 0:
    print("No diseases found matching the search criteria.")
else:
    print(f"## Disease Search Results\\n\\n{{summary}}\\n")
    print("### Results:\\n")
    
    for idx, row in df.iterrows():
        print(f"**{{idx + 1}}. {{row.get('name', 'N/A')}}**")
        if pd.notna(row.get('disease_id')):
            print(f"- **ID:** {{row['disease_id']}}")
        if pd.notna(row.get('mondo_id')):
            print(f"- **MONDO ID:** {{row['mondo_id']}}")
        if pd.notna(row.get('doid')):
            print(f"- **DOID:** {{row['doid']}}")
        if pd.notna(row.get('definition')) and row.get('definition'):
            definition = str(row['definition'])[:200]
            print(f"- **Definition:** {{definition}}{{'...' if len(str(row['definition'])) > 200 else ''}}")
        if pd.notna(row.get('synonyms')) and row.get('synonyms'):
            synonyms = str(row['synonyms'])
            if len(synonyms) > 100:
                synonyms = synonyms[:100] + "..."
            print(f"- **Synonyms:** {{synonyms}}")
        print()
    
    if len(df) >= {limit}:
        print(f"\\n---\\n**Note:** Showing first {limit} results. Use `skip={{{skip + limit}}}` to see more.")
"""
        
        # Execute in sandbox if available
        if self.sandbox is not None:
            exit_code, output, artifacts, running_time, peak_memory = self.sandbox.execute(
                language="python",
                code=code_template
            )
            
            # Return both code and output
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += f"*Execution time: {running_time:.2f}s, Peak memory: {peak_memory:.2f}MB*"
            
            if exit_code != 0:
                result += f"\n\n⚠️ **Warning:** Code exited with non-zero status ({exit_code})"
            
            return result
        else:
            # Fallback: execute locally if no sandbox
            from biodsa.tools.biothings.diseases import search_diseases
            
            df, summary = search_diseases(
                search=search,
                name=name,
                mondo_id=mondo_id,
                doid=doid,
                omim_id=omim_id,
                mesh_id=mesh_id,
                limit=limit,
                skip=skip,
                save_path=save_path,
            )
            
            if df is None or len(df) == 0:
                output = "No diseases found matching the search criteria."
            else:
                output = f"## Disease Search Results\n\n{summary}\n\n"
                output += "### Results:\n\n"
                for idx, row in df.iterrows():
                    output += f"**{idx + 1}. {row.get('name', 'N/A')}**\n"
                    if pd.notna(row.get('disease_id')):
                        output += f"- **ID:** {row['disease_id']}\n"
                    if pd.notna(row.get('mondo_id')):
                        output += f"- **MONDO ID:** {row['mondo_id']}\n"
                    if pd.notna(row.get('doid')):
                        output += f"- **DOID:** {row['doid']}\n"
                    if pd.notna(row.get('definition')) and row.get('definition'):
                        definition = str(row['definition'])[:200]
                        output += f"- **Definition:** {definition}{'...' if len(str(row['definition'])) > 200 else ''}\n"
                    if pd.notna(row.get('synonyms')) and row.get('synonyms'):
                        synonyms = str(row['synonyms'])
                        if len(synonyms) > 100:
                            synonyms = synonyms[:100] + "..."
                        output += f"- **Synonyms:** {synonyms}\n"
                    output += "\n"
                
                if len(df) >= limit:
                    output += f"\n---\n**Note:** Showing first {limit} results. Use `skip={skip + limit}` to see more."
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result


class FetchDiseaseDetailsToolInput(BaseModel):
    """Input schema for FetchDiseaseDetailsTool."""
    
    disease_ids: List[str] = Field(
        ...,
        description="List of disease IDs to fetch detailed information for (e.g., ['MONDO:0004992', 'DOID:162'])"
    )
    save_path: Optional[str] = Field(
        default=None,
        description="Optional path to save the results as CSV"
    )


class FetchDiseaseDetailsTool(BaseTool):
    """
    Tool to fetch detailed information for specific diseases by their IDs.
    
    This tool retrieves comprehensive information about diseases including:
    - Complete definitions and descriptions
    - All known synonyms and alternative names
    - Cross-references to multiple databases
    - Associated phenotypes and characteristics
    
    Use this when you have specific disease IDs and need complete details.
    """
    
    name: str = "fetch_disease_details"
    description: str = (
        "Fetch detailed information for specific diseases using their IDs (MONDO, DOID, OMIM, etc.). "
        "Returns comprehensive disease data including full definitions, all synonyms, "
        "cross-references, and associated phenotypes. "
        "CRITICAL USE: When you have identified diseases by ID and need complete details "
        "for in-depth analysis, comparison, or extracting specific disease characteristics."
    )
    args_schema: Type[BaseModel] = FetchDiseaseDetailsToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        disease_ids: List[str],
        save_path: Optional[str] = None,
    ) -> str:
        """Execute the tool to fetch disease details."""
        
        if not disease_ids or len(disease_ids) == 0:
            return "Error: No disease IDs provided. Please provide at least one disease ID."
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.biothings.diseases import fetch_disease_details_by_ids
import pandas as pd

# Fetch disease details
df, summary = fetch_disease_details_by_ids(
    disease_ids={repr(disease_ids)},
    save_path={repr(save_path)},
)

# Generate output
if df is None or len(df) == 0:
    print(f"No details found for the provided disease IDs: {{', '.join({repr(disease_ids)})}}")
else:
    print(f"## Disease Details\\n\\n{{summary}}\\n")
    
    for idx, row in df.iterrows():
        print(f"### {{idx + 1}}. {{row.get('name', 'Unknown Disease')}}\\n")
        if pd.notna(row.get('disease_id')):
            print(f"**ID:** {{row['disease_id']}}\\n")
        if pd.notna(row.get('definition')) and row.get('definition'):
            print(f"**Definition:** {{row['definition']}}\\n")
        if pd.notna(row.get('synonyms')) and row.get('synonyms'):
            print(f"**Synonyms:** {{row['synonyms']}}\\n")
        if pd.notna(row.get('mondo')) and row.get('mondo'):
            print(f"**MONDO Info:** {{str(row['mondo'])[:300]}}...\\n")
        if pd.notna(row.get('xrefs')) and row.get('xrefs'):
            print(f"**Cross-references:** {{str(row['xrefs'])[:300]}}...\\n")
        if pd.notna(row.get('phenotypes')) and row.get('phenotypes'):
            print(f"**Phenotypes:** {{str(row['phenotypes'])[:300]}}...\\n")
        print("---\\n")
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
            df, summary = fetch_disease_details_by_ids(
                disease_ids=disease_ids,
                save_path=save_path,
            )
            
            if df is None or len(df) == 0:
                output = f"No details found for the provided disease IDs: {', '.join(disease_ids)}"
            else:
                output = f"## Disease Details\n\n{summary}\n\n"
                for idx, row in df.iterrows():
                    output += f"### {idx + 1}. {row.get('name', 'Unknown Disease')}\n\n"
                    if pd.notna(row.get('disease_id')):
                        output += f"**ID:** {row['disease_id']}\n\n"
                    if pd.notna(row.get('definition')) and row.get('definition'):
                        output += f"**Definition:** {row['definition']}\n\n"
                    if pd.notna(row.get('synonyms')) and row.get('synonyms'):
                        output += f"**Synonyms:** {row['synonyms']}\n\n"
                    if pd.notna(row.get('mondo')) and row.get('mondo'):
                        output += f"**MONDO Info:** {str(row['mondo'])[:300]}...\n\n"
                    if pd.notna(row.get('xrefs')) and row.get('xrefs'):
                        output += f"**Cross-references:** {str(row['xrefs'])[:300]}...\n\n"
                    if pd.notna(row.get('phenotypes')) and row.get('phenotypes'):
                        output += f"**Phenotypes:** {str(row['phenotypes'])[:300]}...\n\n"
                    output += "---\n\n"
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result


# =====================================================
# Drug Tools
# =====================================================
class SearchDrugsToolInput(BaseModel):
    """Input schema for SearchDrugsTool."""
    
    search: Optional[str] = Field(
        default=None,
        description="General search term to query across all fields"
    )
    name: Optional[str] = Field(
        default=None,
        description="Drug name (e.g., 'aspirin', 'imatinib', 'pembrolizumab')"
    )
    drugbank_id: Optional[str] = Field(
        default=None,
        description="DrugBank ID (e.g., 'DB00001')"
    )
    chebi_id: Optional[str] = Field(
        default=None,
        description="ChEBI ID (e.g., 'CHEBI:15365')"
    )
    chembl_id: Optional[str] = Field(
        default=None,
        description="ChEMBL ID (e.g., 'CHEMBL25')"
    )
    pubchem_cid: Optional[str] = Field(
        default=None,
        description="PubChem Compound ID"
    )
    inchikey: Optional[str] = Field(
        default=None,
        description="InChI Key for chemical structure"
    )
    limit: int = Field(
        default=100,
        description="Maximum number of results to return (1-1000)"
    )
    skip: int = Field(
        default=0,
        description="Number of results to skip for pagination"
    )
    save_path: Optional[str] = Field(
        default=None,
        description="Path to save the search results"
    )


class SearchDrugsTool(BaseTool):
    """
    Tool to search for drugs and chemical compounds using MyChem.info API.
    
    This comprehensive search tool allows searching by:
    - Drug names and trade names
    - Chemical identifiers (DrugBank, ChEBI, ChEMBL, PubChem)
    - Chemical structures (InChI Key)
    - General search terms
    
    Returns detailed drug information including names, identifiers, chemical formulas,
    and cross-references to multiple drug databases.
    """
    
    name: str = "search_drugs"
    description: str = (
        "Search for drugs and chemical compounds using MyChem.info. "
        "Find drugs by name, trade names, or specific identifiers (DrugBank, ChEBI, ChEMBL, PubChem, InChI). "
        "Returns drug information including names, trade names, chemical identifiers, formulas, and database cross-references. "
        "CRITICAL USE: When researching medications, drug properties, chemical compounds, "
        "finding drug identifiers, or exploring drug relationships and alternatives."
    )
    args_schema: Type[BaseModel] = SearchDrugsToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        search: Optional[str] = None,
        name: Optional[str] = None,
        drugbank_id: Optional[str] = None,
        chebi_id: Optional[str] = None,
        chembl_id: Optional[str] = None,
        pubchem_cid: Optional[str] = None,
        inchikey: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
        save_path: Optional[str] = None,
    ) -> str:
        """Execute the tool to search drugs."""
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.biothings.drugs import search_drugs
import pandas as pd

# Search for drugs
df, summary = search_drugs(
    search={repr(search)},
    name={repr(name)},
    drugbank_id={repr(drugbank_id)},
    chebi_id={repr(chebi_id)},
    chembl_id={repr(chembl_id)},
    pubchem_cid={repr(pubchem_cid)},
    inchikey={repr(inchikey)},
    limit={limit},
    skip={skip},
    save_path={repr(save_path)},
)

# Generate output
if df is None or len(df) == 0:
    print("No drugs found matching the search criteria.")
else:
    print(f"## Drug Search Results\\n\\n{{summary}}\\n")
    print("### Results:\\n")
    
    for idx, row in df.iterrows():
        print(f"**{{idx + 1}}. {{row.get('name', 'N/A')}}**")
        if pd.notna(row.get('drug_id')):
            print(f"- **ID:** {{row['drug_id']}}")
        if pd.notna(row.get('tradename')) and row.get('tradename'):
            tradename = str(row['tradename'])
            if len(tradename) > 100:
                tradename = tradename[:100] + "..."
            print(f"- **Trade Names:** {{tradename}}")
        if pd.notna(row.get('drugbank_id')):
            print(f"- **DrugBank ID:** {{row['drugbank_id']}}")
        if pd.notna(row.get('chebi_id')):
            print(f"- **ChEBI ID:** {{row['chebi_id']}}")
        if pd.notna(row.get('chembl_id')):
            print(f"- **ChEMBL ID:** {{row['chembl_id']}}")
        if pd.notna(row.get('pubchem_cid')):
            print(f"- **PubChem CID:** {{row['pubchem_cid']}}")
        if pd.notna(row.get('formula')):
            print(f"- **Formula:** {{row['formula']}}")
        if pd.notna(row.get('inchikey')):
            inchikey_str = str(row['inchikey'])[:50]
            print(f"- **InChI Key:** {{inchikey_str}}...")
        print()
    
    if len(df) >= {limit}:
        print(f"\\n---\\n**Note:** Showing first {limit} results. Use `skip={{{skip + limit}}}` to see more.")
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
            df, summary = search_drugs(
                search=search,
                name=name,
                drugbank_id=drugbank_id,
                chebi_id=chebi_id,
                chembl_id=chembl_id,
                pubchem_cid=pubchem_cid,
                inchikey=inchikey,
                limit=limit,
                skip=skip,
                save_path=save_path,
            )
            
            if df is None or len(df) == 0:
                output = "No drugs found matching the search criteria."
            else:
                output = f"## Drug Search Results\n\n{summary}\n\n"
                output += "### Results:\n\n"
                for idx, row in df.iterrows():
                    output += f"**{idx + 1}. {row.get('name', 'N/A')}**\n"
                    if pd.notna(row.get('drug_id')):
                        output += f"- **ID:** {row['drug_id']}\n"
                    if pd.notna(row.get('tradename')) and row.get('tradename'):
                        tradename = str(row['tradename'])
                        if len(tradename) > 100:
                            tradename = tradename[:100] + "..."
                        output += f"- **Trade Names:** {tradename}\n"
                    if pd.notna(row.get('drugbank_id')):
                        output += f"- **DrugBank ID:** {row['drugbank_id']}\n"
                    if pd.notna(row.get('chebi_id')):
                        output += f"- **ChEBI ID:** {row['chebi_id']}\n"
                    if pd.notna(row.get('chembl_id')):
                        output += f"- **ChEMBL ID:** {row['chembl_id']}\n"
                    if pd.notna(row.get('pubchem_cid')):
                        output += f"- **PubChem CID:** {row['pubchem_cid']}\n"
                    if pd.notna(row.get('formula')):
                        output += f"- **Formula:** {row['formula']}\n"
                    if pd.notna(row.get('inchikey')):
                        inchikey_str = str(row['inchikey'])[:50]
                        output += f"- **InChI Key:** {inchikey_str}...\n"
                    output += "\n"
                
                if len(df) >= limit:
                    output += f"\n---\n**Note:** Showing first {limit} results. Use `skip={skip + limit}` to see more."
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result


class FetchDrugDetailsToolInput(BaseModel):
    """Input schema for FetchDrugDetailsTool."""
    
    drug_ids: List[str] = Field(
        ...,
        description="List of drug IDs to fetch detailed information for (e.g., ['DB00001', 'CHEBI:15365'])"
    )
    save_path: Optional[str] = Field(
        default=None,
        description="Optional path to save the results as CSV"
    )


class FetchDrugDetailsTool(BaseTool):
    """
    Tool to fetch detailed information for specific drugs by their IDs.
    
    This tool retrieves comprehensive information about drugs including:
    - Complete descriptions and indications
    - Mechanism of action
    - Pharmacology information
    - All trade names
    - Cross-references to multiple databases
    
    Use this when you have specific drug IDs and need complete details.
    """
    
    name: str = "fetch_drug_details"
    description: str = (
        "Fetch detailed information for specific drugs using their IDs (DrugBank, ChEBI, ChEMBL, PubChem, etc.). "
        "Returns comprehensive drug data including descriptions, indications, mechanism of action, "
        "pharmacology, trade names, and cross-references. "
        "CRITICAL USE: When you have identified drugs by ID and need complete details "
        "for in-depth analysis, comparison, or extracting specific drug properties and mechanisms."
    )
    args_schema: Type[BaseModel] = FetchDrugDetailsToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        drug_ids: List[str],
        save_path: Optional[str] = None,
    ) -> str:
        """Execute the tool to fetch drug details."""
        
        if not drug_ids or len(drug_ids) == 0:
            return "Error: No drug IDs provided. Please provide at least one drug ID."
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.biothings.drugs import fetch_drug_details_by_ids
import pandas as pd

# Fetch drug details
df, summary = fetch_drug_details_by_ids(
    drug_ids={repr(drug_ids)},
    save_path={repr(save_path)},
)

# Generate output
if df is None or len(df) == 0:
    print(f"No details found for the provided drug IDs: {{', '.join({repr(drug_ids)})}}")
else:
    print(f"## Drug Details\\n\\n{{summary}}\\n")
    
    for idx, row in df.iterrows():
        print(f"### {{idx + 1}}. {{row.get('name', 'Unknown Drug')}}\\n")
        if pd.notna(row.get('drug_id')):
            print(f"**ID:** {{row['drug_id']}}\\n")
        if pd.notna(row.get('tradename')) and row.get('tradename'):
            print(f"**Trade Names:** {{row['tradename']}}\\n")
        if pd.notna(row.get('drugbank_id')):
            print(f"**DrugBank ID:** {{row['drugbank_id']}}\\n")
        if pd.notna(row.get('chebi_id')):
            print(f"**ChEBI ID:** {{row['chebi_id']}}\\n")
        if pd.notna(row.get('chembl_id')):
            print(f"**ChEMBL ID:** {{row['chembl_id']}}\\n")
        if pd.notna(row.get('pubchem_cid')):
            print(f"**PubChem CID:** {{row['pubchem_cid']}}\\n")
        if pd.notna(row.get('formula')):
            print(f"**Formula:** {{row['formula']}}\\n")
        if pd.notna(row.get('description')) and row.get('description'):
            print(f"**Description:** {{row['description']}}\\n")
        if pd.notna(row.get('indication')) and row.get('indication'):
            print(f"**Indication:** {{row['indication']}}\\n")
        if pd.notna(row.get('mechanism_of_action')) and row.get('mechanism_of_action'):
            print(f"**Mechanism of Action:** {{row['mechanism_of_action']}}\\n")
        if pd.notna(row.get('pharmacology')) and row.get('pharmacology'):
            print(f"**Pharmacology:** {{str(row['pharmacology'])[:300]}}...\\n")
        print("---\\n")
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
            df, summary = fetch_drug_details_by_ids(
                drug_ids=drug_ids,
                save_path=save_path,
            )
            
            if df is None or len(df) == 0:
                output = f"No details found for the provided drug IDs: {', '.join(drug_ids)}"
            else:
                output = f"## Drug Details\n\n{summary}\n\n"
                for idx, row in df.iterrows():
                    output += f"### {idx + 1}. {row.get('name', 'Unknown Drug')}\n\n"
                    if pd.notna(row.get('drug_id')):
                        output += f"**ID:** {row['drug_id']}\n\n"
                    if pd.notna(row.get('tradename')) and row.get('tradename'):
                        output += f"**Trade Names:** {row['tradename']}\n\n"
                    if pd.notna(row.get('drugbank_id')):
                        output += f"**DrugBank ID:** {row['drugbank_id']}\n\n"
                    if pd.notna(row.get('chebi_id')):
                        output += f"**ChEBI ID:** {row['chebi_id']}\n\n"
                    if pd.notna(row.get('chembl_id')):
                        output += f"**ChEMBL ID:** {row['chembl_id']}\n\n"
                    if pd.notna(row.get('pubchem_cid')):
                        output += f"**PubChem CID:** {row['pubchem_cid']}\n\n"
                    if pd.notna(row.get('formula')):
                        output += f"**Formula:** {row['formula']}\n\n"
                    if pd.notna(row.get('description')) and row.get('description'):
                        output += f"**Description:** {row['description']}\n\n"
                    if pd.notna(row.get('indication')) and row.get('indication'):
                        output += f"**Indication:** {row['indication']}\n\n"
                    if pd.notna(row.get('mechanism_of_action')) and row.get('mechanism_of_action'):
                        output += f"**Mechanism of Action:** {row['mechanism_of_action']}\n\n"
                    if pd.notna(row.get('pharmacology')) and row.get('pharmacology'):
                        output += f"**Pharmacology:** {str(row['pharmacology'])[:300]}...\n\n"
                    output += "---\n\n"
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result


# =====================================================
# Gene Tools
# =====================================================
class SearchGenesToolInput(BaseModel):
    """Input schema for SearchGenesTool."""
    
    search: Optional[str] = Field(
        default=None,
        description="General search term to query across all fields"
    )
    symbol: Optional[str] = Field(
        default=None,
        description="Gene symbol (e.g., 'TP53', 'BRCA1', 'EGFR')"
    )
    name: Optional[str] = Field(
        default=None,
        description="Gene name (e.g., 'tumor protein p53')"
    )
    entrezgene: Optional[str] = Field(
        default=None,
        description="Entrez Gene ID (NCBI gene ID)"
    )
    ensembl_gene: Optional[str] = Field(
        default=None,
        description="Ensembl Gene ID (e.g., 'ENSG00000141510')"
    )
    species: Optional[str] = Field(
        default="human",
        description="Species (default: 'human', can also use 'mouse', 'rat', etc.)"
    )
    limit: int = Field(
        default=100,
        description="Maximum number of results to return (1-1000)"
    )
    skip: int = Field(
        default=0,
        description="Number of results to skip for pagination"
    )
    save_path: Optional[str] = Field(
        default=None,
        description="Path to save the search results"
    )


class SearchGenesTool(BaseTool):
    """
    Tool to search for genes using MyGene.info API.
    
    This comprehensive search tool allows searching by:
    - Gene symbols and names
    - Gene identifiers (Entrez, Ensembl)
    - General search terms
    - Species (human, mouse, rat, etc.)
    
    Returns detailed gene information including symbols, names, summaries, aliases,
    and cross-references to multiple gene databases.
    """
    
    name: str = "search_genes"
    description: str = (
        "Search for genes using MyGene.info. "
        "Find genes by symbol, name, or specific identifiers (Entrez, Ensembl). "
        "Returns gene information including symbols, names, summaries, aliases, gene types, and database cross-references. "
        "Supports multiple species (human, mouse, rat, etc.). "
        "CRITICAL USE: When researching genes, gene function, genetic variants, "
        "finding gene identifiers, or exploring gene relationships and aliases."
    )
    args_schema: Type[BaseModel] = SearchGenesToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        search: Optional[str] = None,
        symbol: Optional[str] = None,
        name: Optional[str] = None,
        entrezgene: Optional[str] = None,
        ensembl_gene: Optional[str] = None,
        species: Optional[str] = "human",
        limit: int = 100,
        skip: int = 0,
        save_path: Optional[str] = None,
    ) -> str:
        """Execute the tool to search genes."""
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.biothings.genes import search_genes
import pandas as pd

# Search for genes
df, summary = search_genes(
    search={repr(search)},
    symbol={repr(symbol)},
    name={repr(name)},
    entrezgene={repr(entrezgene)},
    ensembl_gene={repr(ensembl_gene)},
    species={repr(species)},
    limit={limit},
    skip={skip},
    save_path={repr(save_path)},
)

# Generate output
if df is None or len(df) == 0:
    print("No genes found matching the search criteria.")
else:
    print(f"## Gene Search Results\\n\\n{{summary}}\\n")
    print("### Results:\\n")
    
    for idx, row in df.iterrows():
        gene_line = f"**{{idx + 1}}. {{row.get('symbol', 'N/A')}}**"
        if pd.notna(row.get('name')):
            gene_line += f" - {{row['name']}}"
        print(gene_line)
        
        if pd.notna(row.get('gene_id')):
            print(f"- **Gene ID:** {{row['gene_id']}}")
        if pd.notna(row.get('entrezgene')):
            print(f"- **Entrez ID:** {{row['entrezgene']}}")
        if pd.notna(row.get('type_of_gene')):
            print(f"- **Type:** {{row['type_of_gene']}}")
        if pd.notna(row.get('summary')) and row.get('summary'):
            summary_text = str(row['summary'])[:200]
            print(f"- **Summary:** {{summary_text}}{{'...' if len(str(row['summary'])) > 200 else ''}}")
        if pd.notna(row.get('alias')) and row.get('alias'):
            aliases = str(row['alias'])
            if len(aliases) > 100:
                aliases = aliases[:100] + "..."
            print(f"- **Aliases:** {{aliases}}")
        print()
    
    if len(df) >= {limit}:
        print(f"\\n---\\n**Note:** Showing first {limit} results. Use `skip={{{skip + limit}}}` to see more.")
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
            df, summary = search_genes(
                search=search,
                symbol=symbol,
                name=name,
                entrezgene=entrezgene,
                ensembl_gene=ensembl_gene,
                species=species,
                limit=limit,
                skip=skip,
                save_path=save_path,
            )
            
            if df is None or len(df) == 0:
                output = "No genes found matching the search criteria."
            else:
                output = f"## Gene Search Results\n\n{summary}\n\n"
                output += "### Results:\n\n"
                for idx, row in df.iterrows():
                    output += f"**{idx + 1}. {row.get('symbol', 'N/A')}**"
                    if pd.notna(row.get('name')):
                        output += f" - {row['name']}\n"
                    else:
                        output += "\n"
                    
                    if pd.notna(row.get('gene_id')):
                        output += f"- **Gene ID:** {row['gene_id']}\n"
                    if pd.notna(row.get('entrezgene')):
                        output += f"- **Entrez ID:** {row['entrezgene']}\n"
                    if pd.notna(row.get('type_of_gene')):
                        output += f"- **Type:** {row['type_of_gene']}\n"
                    if pd.notna(row.get('summary')) and row.get('summary'):
                        summary_text = str(row['summary'])[:200]
                        output += f"- **Summary:** {summary_text}{'...' if len(str(row['summary'])) > 200 else ''}\n"
                    if pd.notna(row.get('alias')) and row.get('alias'):
                        aliases = str(row['alias'])
                        if len(aliases) > 100:
                            aliases = aliases[:100] + "..."
                        output += f"- **Aliases:** {aliases}\n"
                    output += "\n"
                
                if len(df) >= limit:
                    output += f"\n---\n**Note:** Showing first {limit} results. Use `skip={skip + limit}` to see more."
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result


class FetchGeneDetailsToolInput(BaseModel):
    """Input schema for FetchGeneDetailsTool."""
    
    gene_ids: List[str] = Field(
        ...,
        description="List of gene IDs to fetch detailed information for (e.g., ['7157', 'ENSG00000141510'])"
    )
    save_path: Optional[str] = Field(
        default=None,
        description="Optional path to save the results as CSV"
    )


class FetchGeneDetailsTool(BaseTool):
    """
    Tool to fetch detailed information for specific genes by their IDs.
    
    This tool retrieves comprehensive information about genes including:
    - Complete gene summaries and descriptions
    - All known aliases
    - Cross-references to multiple databases (Ensembl, RefSeq)
    - Gene type and taxonomic information
    
    Use this when you have specific gene IDs and need complete details.
    """
    
    name: str = "fetch_gene_details"
    description: str = (
        "Fetch detailed information for specific genes using their IDs (Entrez, Ensembl, gene symbols, etc.). "
        "Returns comprehensive gene data including full summaries, all aliases, "
        "cross-references (Ensembl, RefSeq), gene types, and taxonomic information. "
        "CRITICAL USE: When you have identified genes by ID and need complete details "
        "for in-depth analysis, comparison, or extracting specific gene characteristics and functions."
    )
    args_schema: Type[BaseModel] = FetchGeneDetailsToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        gene_ids: List[str],
        save_path: Optional[str] = None,
    ) -> str:
        """Execute the tool to fetch gene details."""
        
        if not gene_ids or len(gene_ids) == 0:
            return "Error: No gene IDs provided. Please provide at least one gene ID."
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.biothings.genes import fetch_gene_details_by_ids
import pandas as pd

# Fetch gene details
df, summary = fetch_gene_details_by_ids(
    gene_ids={repr(gene_ids)},
    save_path={repr(save_path)},
)

# Generate output
if df is None or len(df) == 0:
    print(f"No details found for the provided gene IDs: {{', '.join({repr(gene_ids)})}}")
else:
    print(f"## Gene Details\\n\\n{{summary}}\\n")
    
    for idx, row in df.iterrows():
        gene_line = f"### {{idx + 1}}. {{row.get('symbol', 'Unknown Gene')}}"
        if pd.notna(row.get('name')):
            gene_line += f" - {{row['name']}}"
        print(gene_line + "\\n")
        
        if pd.notna(row.get('gene_id')):
            print(f"**Gene ID:** {{row['gene_id']}}\\n")
        if pd.notna(row.get('entrezgene')):
            print(f"**Entrez ID:** {{row['entrezgene']}}\\n")
        if pd.notna(row.get('type_of_gene')):
            print(f"**Type:** {{row['type_of_gene']}}\\n")
        if pd.notna(row.get('taxid')):
            print(f"**Taxonomy ID:** {{row['taxid']}}\\n")
        if pd.notna(row.get('summary')) and row.get('summary'):
            print(f"**Summary:** {{row['summary']}}\\n")
        if pd.notna(row.get('alias')) and row.get('alias'):
            print(f"**Aliases:** {{row['alias']}}\\n")
        if pd.notna(row.get('ensembl')) and row.get('ensembl'):
            print(f"**Ensembl:** {{str(row['ensembl'])[:300]}}...\\n")
        if pd.notna(row.get('refseq')) and row.get('refseq'):
            print(f"**RefSeq:** {{str(row['refseq'])[:300]}}...\\n")
        print("---\\n")
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
            df, summary = fetch_gene_details_by_ids(
                gene_ids=gene_ids,
                save_path=save_path,
            )
            
            if df is None or len(df) == 0:
                output = f"No details found for the provided gene IDs: {', '.join(gene_ids)}"
            else:
                output = f"## Gene Details\n\n{summary}\n\n"
                for idx, row in df.iterrows():
                    output += f"### {idx + 1}. {row.get('symbol', 'Unknown Gene')}"
                    if pd.notna(row.get('name')):
                        output += f" - {row['name']}\n\n"
                    else:
                        output += "\n\n"
                    
                    if pd.notna(row.get('gene_id')):
                        output += f"**Gene ID:** {row['gene_id']}\n\n"
                    if pd.notna(row.get('entrezgene')):
                        output += f"**Entrez ID:** {row['entrezgene']}\n\n"
                    if pd.notna(row.get('type_of_gene')):
                        output += f"**Type:** {row['type_of_gene']}\n\n"
                    if pd.notna(row.get('taxid')):
                        output += f"**Taxonomy ID:** {row['taxid']}\n\n"
                    if pd.notna(row.get('summary')) and row.get('summary'):
                        output += f"**Summary:** {row['summary']}\n\n"
                    if pd.notna(row.get('alias')) and row.get('alias'):
                        output += f"**Aliases:** {row['alias']}\n\n"
                    if pd.notna(row.get('ensembl')) and row.get('ensembl'):
                        output += f"**Ensembl:** {str(row['ensembl'])[:300]}...\n\n"
                    if pd.notna(row.get('refseq')) and row.get('refseq'):
                        output += f"**RefSeq:** {str(row['refseq'])[:300]}...\n\n"
                    output += "---\n\n"
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result


# =====================================================
# Variant Tools
# =====================================================
class SearchVariantsToolInput(BaseModel):
    """Input schema for SearchVariantsTool."""
    
    search: Optional[str] = Field(
        default=None,
        description="General search term to query across all fields"
    )
    rsid: Optional[str] = Field(
        default=None,
        description="dbSNP rsID (e.g., 'rs58991260', 'rs121913529')"
    )
    gene: Optional[str] = Field(
        default=None,
        description="Gene symbol or Entrez gene ID (e.g., 'TP53', 'BRCA1')"
    )
    chrom: Optional[str] = Field(
        default=None,
        description="Chromosome (e.g., '1', '17', 'X', 'MT')"
    )
    position: Optional[int] = Field(
        default=None,
        description="Genomic position"
    )
    hgvs: Optional[str] = Field(
        default=None,
        description="HGVS notation (e.g., 'chr1:g.35367G>A', 'NM_000546.5:c.215C>G')"
    )
    clinvar_significance: Optional[str] = Field(
        default=None,
        description="ClinVar clinical significance (e.g., 'pathogenic', 'benign', 'likely pathogenic')"
    )
    cosmic_id: Optional[str] = Field(
        default=None,
        description="COSMIC database ID"
    )
    limit: int = Field(
        default=100,
        description="Maximum number of results to return (1-1000)"
    )
    skip: int = Field(
        default=0,
        description="Number of results to skip for pagination"
    )
    save_path: Optional[str] = Field(
        default=None,
        description="Path to save the search results"
    )


class SearchVariantsTool(BaseTool):
    """
    Tool to search for genetic variants using MyVariant.info API.
    
    This comprehensive search tool allows searching by:
    - rsID (dbSNP identifiers)
    - Gene symbols or IDs
    - Chromosomal location and position
    - HGVS notation
    - Clinical significance (ClinVar)
    - COSMIC identifiers
    
    Returns detailed variant information including genomic coordinates, alleles,
    gene associations, and clinical annotations.
    """
    
    name: str = "search_variants"
    description: str = (
        "Search for genetic variants using MyVariant.info. "
        "Find variants by rsID, gene symbol, chromosomal location, HGVS notation, "
        "or clinical significance. Returns variant information including genomic coordinates, "
        "reference and alternate alleles, gene associations, and clinical annotations. "
        "CRITICAL USE: When researching genetic variants, mutations, SNPs, "
        "clinical significance of variants, or exploring variant-gene-disease relationships."
    )
    args_schema: Type[BaseModel] = SearchVariantsToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        search: Optional[str] = None,
        rsid: Optional[str] = None,
        gene: Optional[str] = None,
        chrom: Optional[str] = None,
        position: Optional[int] = None,
        hgvs: Optional[str] = None,
        clinvar_significance: Optional[str] = None,
        cosmic_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
        save_path: Optional[str] = None,
    ) -> str:
        """Execute the tool to search variants."""
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.biothings.variants import search_variants
import pandas as pd

# Search for variants
df, summary = search_variants(
    search={repr(search)},
    rsid={repr(rsid)},
    gene={repr(gene)},
    chrom={repr(chrom)},
    position={position},
    hgvs={repr(hgvs)},
    clinvar_significance={repr(clinvar_significance)},
    cosmic_id={repr(cosmic_id)},
    limit={limit},
    skip={skip},
    save_path={repr(save_path)},
)

# Generate output
if df is None or len(df) == 0:
    print("No variants found matching the search criteria.")
else:
    print(f"## Variant Search Results\\n\\n{{summary}}\\n")
    print("### Results:\\n")
    
    for idx, row in df.iterrows():
        print(f"**{{idx + 1}}. {{row.get('variant_id', 'N/A')}}**")
        if pd.notna(row.get('rsid')):
            print(f"- **rsID:** {{row['rsid']}}")
        if pd.notna(row.get('chrom')) and pd.notna(row.get('pos')):
            print(f"- **Location:** chr{{row['chrom']}}:{{row['pos']}}")
        if pd.notna(row.get('ref')) and pd.notna(row.get('alt')):
            print(f"- **Alleles:** {{row['ref']}} > {{row['alt']}}")
        if pd.notna(row.get('gene_symbol')):
            print(f"- **Gene:** {{row['gene_symbol']}}")
        if pd.notna(row.get('variant_type')) and row.get('variant_type'):
            print(f"- **Type:** {{row['variant_type']}}")
        if pd.notna(row.get('clinical_significance')) and row.get('clinical_significance'):
            print(f"- **Clinical Significance:** {{row['clinical_significance']}}")
        print()
    
    if len(df) >= {limit}:
        print(f"\\n---\\n**Note:** Showing first {limit} results. Use `skip={{{skip + limit}}}` to see more.")
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
            df, summary = search_variants(
                search=search,
                rsid=rsid,
                gene=gene,
                chrom=chrom,
                position=position,
                hgvs=hgvs,
                clinvar_significance=clinvar_significance,
                cosmic_id=cosmic_id,
                limit=limit,
                skip=skip,
                save_path=save_path,
            )
            
            if df is None or len(df) == 0:
                output = "No variants found matching the search criteria."
            else:
                output = f"## Variant Search Results\n\n{summary}\n\n"
                output += "### Results:\n\n"
                for idx, row in df.iterrows():
                    output += f"**{idx + 1}. {row.get('variant_id', 'N/A')}**\n"
                    if pd.notna(row.get('rsid')):
                        output += f"- **rsID:** {row['rsid']}\n"
                    if pd.notna(row.get('chrom')) and pd.notna(row.get('pos')):
                        output += f"- **Location:** chr{row['chrom']}:{row['pos']}\n"
                    if pd.notna(row.get('ref')) and pd.notna(row.get('alt')):
                        output += f"- **Alleles:** {row['ref']} > {row['alt']}\n"
                    if pd.notna(row.get('gene_symbol')):
                        output += f"- **Gene:** {row['gene_symbol']}\n"
                    if pd.notna(row.get('variant_type')) and row.get('variant_type'):
                        output += f"- **Type:** {row['variant_type']}\n"
                    if pd.notna(row.get('clinical_significance')) and row.get('clinical_significance'):
                        output += f"- **Clinical Significance:** {row['clinical_significance']}\n"
                    output += "\n"
                
                if len(df) >= limit:
                    output += f"\n---\n**Note:** Showing first {limit} results. Use `skip={skip + limit}` to see more."
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result


class FetchVariantDetailsToolInput(BaseModel):
    """Input schema for FetchVariantDetailsTool."""
    
    variant_ids: List[str] = Field(
        ...,
        description="List of variant IDs to fetch detailed information for (HGVS notation, rsIDs, e.g., ['chr1:g.35367G>A', 'rs58991260'])"
    )
    save_path: Optional[str] = Field(
        default=None,
        description="Optional path to save the results as CSV"
    )


class FetchVariantDetailsTool(BaseTool):
    """
    Tool to fetch detailed information for specific variants by their IDs.
    
    This tool retrieves comprehensive information about genetic variants including:
    - Complete genomic annotations
    - Clinical significance from ClinVar
    - Functional predictions (CADD, dbNSFP)
    - Population frequencies (dbSNP)
    - Cancer associations (COSMIC)
    
    Use this when you have specific variant IDs and need complete details.
    """
    
    name: str = "fetch_variant_details"
    description: str = (
        "Fetch detailed information for specific genetic variants using their IDs (HGVS notation or rsIDs). "
        "Returns comprehensive variant data including genomic annotations, clinical significance (ClinVar), "
        "functional predictions (CADD, dbNSFP), population frequencies, and cancer associations (COSMIC). "
        "CRITICAL USE: When you have identified variants and need complete details "
        "for clinical interpretation, functional analysis, or understanding variant pathogenicity."
    )
    args_schema: Type[BaseModel] = FetchVariantDetailsToolInput
    sandbox: ExecutionSandboxWrapper = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox
    
    def _run(
        self,
        variant_ids: List[str],
        save_path: Optional[str] = None,
    ) -> str:
        """Execute the tool to fetch variant details."""
        
        if not variant_ids or len(variant_ids) == 0:
            return "Error: No variant IDs provided. Please provide at least one variant ID."
        
        # Generate Python code template
        code_template = f"""
from biodsa.tools.biothings.variants import fetch_variant_details_by_ids
import pandas as pd

# Fetch variant details
df, summary = fetch_variant_details_by_ids(
    variant_ids={repr(variant_ids)},
    save_path={repr(save_path)},
)

# Generate output
if df is None or len(df) == 0:
    print(f"No details found for the provided variant IDs: {{', '.join({repr(variant_ids)})}}")
else:
    print(f"## Variant Details\\n\\n{{summary}}\\n")
    
    for idx, row in df.iterrows():
        print(f"### {{idx + 1}}. {{row.get('variant_id', 'Unknown Variant')}}\\n")
        
        if pd.notna(row.get('rsid')):
            print(f"**rsID:** {{row['rsid']}}\\n")
        if pd.notna(row.get('chrom')) and pd.notna(row.get('pos')):
            print(f"**Location:** chr{{row['chrom']}}:{{row['pos']}}\\n")
        if pd.notna(row.get('ref')) and pd.notna(row.get('alt')):
            print(f"**Alleles:** {{row['ref']}} → {{row['alt']}}\\n")
        if pd.notna(row.get('gene')) and row.get('gene'):
            print(f"**Gene Information:** {{row['gene'][:300]}}...\\n")
        if pd.notna(row.get('clinvar')) and row.get('clinvar'):
            print(f"**ClinVar:** {{row['clinvar']}}\\n")
        if pd.notna(row.get('dbsnp')) and row.get('dbsnp'):
            print(f"**dbSNP:** {{row['dbsnp']}}\\n")
        if pd.notna(row.get('cadd')) and row.get('cadd'):
            print(f"**CADD Scores:** {{row['cadd']}}\\n")
        if pd.notna(row.get('cosmic')) and row.get('cosmic'):
            print(f"**COSMIC:** {{row['cosmic']}}\\n")
        print("---\\n")
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
            df, summary = fetch_variant_details_by_ids(
                variant_ids=variant_ids,
                save_path=save_path,
            )
            
            if df is None or len(df) == 0:
                output = f"No details found for the provided variant IDs: {', '.join(variant_ids)}"
            else:
                output = f"## Variant Details\n\n{summary}\n\n"
                for idx, row in df.iterrows():
                    output += f"### {idx + 1}. {row.get('variant_id', 'Unknown Variant')}\n\n"
                    
                    if pd.notna(row.get('rsid')):
                        output += f"**rsID:** {row['rsid']}\n\n"
                    if pd.notna(row.get('chrom')) and pd.notna(row.get('pos')):
                        output += f"**Location:** chr{row['chrom']}:{row['pos']}\n\n"
                    if pd.notna(row.get('ref')) and pd.notna(row.get('alt')):
                        output += f"**Alleles:** {row['ref']} → {row['alt']}\n\n"
                    if pd.notna(row.get('gene')) and row.get('gene'):
                        output += f"**Gene Information:** {row['gene'][:300]}...\n\n"
                    if pd.notna(row.get('clinvar')) and row.get('clinvar'):
                        output += f"**ClinVar:** {row['clinvar']}\n\n"
                    if pd.notna(row.get('dbsnp')) and row.get('dbsnp'):
                        output += f"**dbSNP:** {row['dbsnp']}\n\n"
                    if pd.notna(row.get('cadd')) and row.get('cadd'):
                        output += f"**CADD Scores:** {row['cadd']}\n\n"
                    if pd.notna(row.get('cosmic')) and row.get('cosmic'):
                        output += f"**COSMIC:** {row['cosmic']}\n\n"
                    output += "---\n\n"
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += "*Executed locally (no sandbox)*"
            
            return result

