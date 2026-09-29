# Pathway Tool Wrappers

This module provides unified LangChain-compatible tools for searching and fetching biological pathway information from KEGG and Gene Ontology databases.

## Overview

The pathway tool wrappers aggregate pathway information from multiple authoritative sources:
- **KEGG Pathways**: Metabolic pathways, signaling pathways, disease pathways
- **Gene Ontology (GO)**: Biological processes, functional annotations

## Tools

### 1. UnifiedPathwaySearchTool

Search for biological pathways and processes across KEGG and Gene Ontology databases.

**Use Cases:**
- Find pathways by name or keyword
- Search for biological processes
- Explore metabolic or signaling pathways
- Find disease-associated pathways
- Get comprehensive pathway information from multiple sources

**Parameters:**
- `task_name` (str): Short description for saving results (e.g., "apoptosis pathways")
- `search_term` (str): Search query (e.g., "apoptosis", "MAPK signaling", "glycolysis")
- `organism_code` (str, optional): KEGG organism code (e.g., "hsa" for human, "mmu" for mouse)
- `pathway_source` (str, optional): Source to search - "kegg", "go", or "both" (default: "both")
- `limit_per_source` (int): Maximum results per source (1-100, default: 20)

**Example:**
```python
from biodsa.tool_wrappers.pathway import UnifiedPathwaySearchTool

tool = UnifiedPathwaySearchTool()
result = tool._run(
    task_name="apoptosis search",
    search_term="apoptosis",
    organism_code="hsa",
    pathway_source="both",
    limit_per_source=10
)
print(result)
```

**Output:**
- KEGG pathways with IDs and descriptions
- GO biological processes with IDs, names, and definitions
- Summary statistics
- Results saved to JSON file in workdir

### 2. PathwayDetailsFetchTool

Fetch comprehensive details for a specific pathway using KEGG pathway ID or GO term ID.

**Use Cases:**
- Get detailed pathway information
- Explore pathway components (genes, compounds, reactions)
- Understand pathway relationships and hierarchies
- Get GO annotations and evidence codes
- Access pathway diagrams and visualizations

**Parameters:**
- `task_name` (str): Short description for saving results (e.g., "apoptosis details")
- `pathway_id` (str): Pathway identifier (e.g., "hsa04210", "GO:0006915")
- `include_genes` (bool): Include associated genes/proteins (default: True)
- `include_compounds` (bool): Include compounds/metabolites (default: True, KEGG only)
- `include_reactions` (bool): Include biochemical reactions (default: False, KEGG only)

**Example:**
```python
from biodsa.tool_wrappers.pathway import PathwayDetailsFetchTool

tool = PathwayDetailsFetchTool()

# Fetch KEGG pathway details
result = tool._run(
    task_name="apoptosis pathway",
    pathway_id="hsa04210",
    include_genes=True,
    include_compounds=True
)
print(result)

# Fetch GO term details
result = tool._run(
    task_name="apoptotic process",
    pathway_id="GO:0006915",
    include_genes=True
)
print(result)
```

**Output:**
- Pathway name and description
- Associated genes and proteins
- Compounds and metabolites (KEGG)
- Biochemical reactions (KEGG)
- Pathway hierarchy (ancestors, children)
- GO annotations with evidence codes
- Visualization URLs
- Results saved to JSON file in workdir

## Data Sources

### KEGG (Kyoto Encyclopedia of Genes and Genomes)
- **Website**: https://www.kegg.jp/
- **Coverage**: Metabolic pathways, signaling pathways, disease pathways across multiple organisms
- **Pathway Types**: 
  - Metabolism
  - Genetic Information Processing
  - Environmental Information Processing
  - Cellular Processes
  - Organismal Systems
  - Human Diseases
  - Drug Development

### Gene Ontology (GO)
- **Website**: http://geneontology.org/
- **Coverage**: Biological processes, molecular functions, cellular components
- **Focus**: Functional annotations with evidence codes
- **Aspects**:
  - Biological Process (P)
  - Molecular Function (F)
  - Cellular Component (C)

## Pathway ID Formats

### KEGG Pathway IDs
- **Format**: `{org}{number}` or `map{number}`
- **Examples**:
  - `hsa04210` - Human apoptosis pathway
  - `mmu04110` - Mouse cell cycle pathway
  - `map00010` - Reference glycolysis pathway
  - `ko00010` - KEGG Orthology glycolysis pathway

### GO Term IDs
- **Format**: `GO:{7-digit number}`
- **Examples**:
  - `GO:0006915` - Apoptotic process
  - `GO:0007049` - Cell cycle
  - `GO:0008150` - Biological process (root term)

## Common Organism Codes (KEGG)

| Code | Organism |
|------|----------|
| hsa  | Homo sapiens (human) |
| mmu  | Mus musculus (mouse) |
| rno  | Rattus norvegicus (rat) |
| dme  | Drosophila melanogaster (fruit fly) |
| cel  | Caenorhabditis elegans (nematode) |
| sce  | Saccharomyces cerevisiae (yeast) |
| eco  | Escherichia coli K-12 |
| ath  | Arabidopsis thaliana (thale cress) |

## Integration with Agents

These tools are designed to work with LangChain-based agents:

```python
from biodsa.tool_wrappers.pathway import (
    UnifiedPathwaySearchTool, 
    PathwayDetailsFetchTool
)
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper

# Initialize with sandbox
sandbox = ExecutionSandboxWrapper()
search_tool = UnifiedPathwaySearchTool(sandbox=sandbox)
details_tool = PathwayDetailsFetchTool(sandbox=sandbox)

# Use in agent
tools = [search_tool, details_tool]
# ... configure agent with tools
```

## Output Files

All tools save their results to JSON files in the workdir:
- File naming: `{cleaned_task_name}.json`
- Location: `workdir/` directory (created if doesn't exist)
- Format: Structured JSON with complete API responses

## Error Handling

The tools include robust error handling:
- Network errors are caught and reported
- Invalid pathway IDs return helpful error messages
- API rate limits are respected
- Partial results are returned when possible

## Performance Considerations

- **Search operations**: Fast (< 2 seconds typically)
- **Details fetch**: Moderate (2-5 seconds depending on pathway size)
- **Network dependency**: Requires internet connection
- **Rate limits**: KEGG and GO APIs have rate limits; avoid excessive parallel requests

## Related Tools

- **Targets**: `biodsa.tool_wrappers.targets` - For target/gene information
- **Diseases**: `biodsa.tool_wrappers.diseases` - For disease information
- **Drugs**: `biodsa.tool_wrappers.drugs` - For drug information
- **Genes**: `biodsa.tool_wrappers.genes` - For gene information

## References

1. Kanehisa, M. and Goto, S. (2000) KEGG: Kyoto Encyclopedia of Genes and Genomes. Nucleic Acids Res. 28, 27-30.
2. The Gene Ontology Consortium (2021) The Gene Ontology resource: enriching a GOld mine. Nucleic Acids Res. 49, D325-D334.
3. Binns, D. et al. (2009) QuickGO: a web-based tool for Gene Ontology searching. Bioinformatics 25, 3045-3046.

## Testing

Run the test suite to verify functionality:

```bash
cd /path/to/BioDSA-dev
python tests/test_pathway_basic.py
```

## License

This module is part of BioDSA and follows the same license terms.

