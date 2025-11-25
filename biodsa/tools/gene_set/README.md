# Gene Set Tools

This module provides LangChain-compatible tools for gene set analysis and single gene information retrieval.

## Acknowledgments

GeneAgent for implementing all of these API functions.

Reference: https://github.com/ncbi-nlp/GeneAgent/tree/main

## Available Tools

### Gene Set Analysis Tools

These tools operate on sets of genes (multiple genes):

1. **GetPathwayForGeneSetTool**
   - Get top-5 biological pathway names for a gene set
   - Queries KEGG, Reactome, BioPlanet, and MSigDB Hallmark databases via Enrichr
   - Returns pathway terms, overlapping genes, and source database

2. **GetEnrichmentForGeneSetTool**
   - Get top-5 enrichment function names including biological regulation, signaling, and metabolism
   - Uses g:Profiler API for comprehensive enrichment analysis
   - Returns enriched terms with statistics and gene overlaps

3. **GetInteractionsForGeneSetTool**
   - Get protein-protein interaction information for a gene set
   - Queries PubTator3 API for up to 50 interactions
   - Useful for understanding gene networks and interaction partners

4. **GetComplexForGeneSetTool**
   - Get protein complex information for a gene set
   - Returns complex protocol IDs and corresponding complex names
   - Queries PubTator3 API

### Single Gene Analysis Tools

These tools operate on individual genes (one gene at a time):

5. **GetGeneSummaryForSingleGeneTool**
   - Get comprehensive summary information for a single gene
   - Queries NCBI Gene database via E-utilities
   - Returns function, location, aliases, and other metadata
   - Supports human (Homo) and mouse (Mus) species

6. **GetDiseaseForSingleGeneTool**
   - Get disease associations for a single gene
   - Returns up to 100 disease IDs and corresponding disease names
   - Queries PubTator API for gene-disease associations from literature mining

7. **GetDomainForSingleGeneTool**
   - Get protein domain information for a single gene
   - Returns up to 10 domain IDs and corresponding domain names
   - Queries PubTator CDD API for conserved domain information

## Usage

### Basic Example

```python
from biodsa.tools.gene_set import (
    GetPathwayForGeneSetTool,
    GetGeneSummaryForSingleGeneTool,
)

# Analyze pathways for a gene set
pathway_tool = GetPathwayForGeneSetTool()
pathways = pathway_tool._run(gene_set="BRCA1,TP53,EGFR")
print(pathways)

# Get summary for a single gene
summary_tool = GetGeneSummaryForSingleGeneTool()
summary = summary_tool._run(gene_name="BRCA1", specie="Homo")
print(summary)
```

### Using with LangChain Agents

```python
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from biodsa.tools.gene_set import (
    GetPathwayForGeneSetTool,
    GetEnrichmentForGeneSetTool,
    GetDiseaseForSingleGeneTool,
)

# Initialize tools
tools = [
    GetPathwayForGeneSetTool(),
    GetEnrichmentForGeneSetTool(),
    GetDiseaseForSingleGeneTool(),
]

# Create agent
llm = ChatOpenAI(temperature=0)
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Use the agent
result = agent.run("What pathways are associated with BRCA1, TP53, and EGFR?")
```

## Input Format

**Important:** For gene set tools, genes must be separated by commas **without spaces**:
- ✅ Correct: `"BRCA1,TP53,EGFR"`
- ❌ Incorrect: `"BRCA1, TP53, EGFR"` (spaces will cause issues)

## Testing

Run the test suite to verify all tools are working:

```bash
python tests/test_gene_set_tools.py
```

## API Rate Limits

These tools query external APIs with various rate limits:
- Enrichr: Generally permissive
- g:Profiler: Generally permissive
- PubTator3 API: ~3 requests per second recommended
- NCBI E-utilities: ~3 requests per second recommended

The underlying functions handle basic error cases but may need additional rate limiting for heavy usage.