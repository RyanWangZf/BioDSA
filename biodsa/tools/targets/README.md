# Unified Biological Target Search

This module provides unified search and retrieval of biological targets, integrating information from multiple authoritative databases:

- **Open Targets Platform**: Therapeutic targets and target-disease associations
- **KEGG**: Biological pathways, genes, and molecular interactions
- **Gene Ontology**: Functional annotations and biological process classifications
- **Human Protein Atlas**: Protein expression, cancer markers, and pathology data

## Features

- **Unified Search**: Search across multiple databases with a single query
- **Multi-Type Search**: Search for targets, pathways, genes, or GO terms
- **Comprehensive Results**: Aggregates information from all sources
- **Automatic ID Detection**: Intelligently detects identifier types
- **Cross-Database References**: Links identifiers across different databases
- **Target-Disease Associations**: Includes disease associations for therapeutic targets
- **Pathway Information**: Complete pathway details with associated genes
- **Functional Annotations**: GO term classifications and hierarchies
- **Protein Expression**: Tissue-specific and subcellular localization data
- **Cancer Markers**: Cancer-associated proteins and prognostic information

## Installation

The module is part of the BioDSA toolkit and requires:

```python
from biodsa.tools.targets import search_targets_unified, fetch_target_details_unified
```

## Quick Start

### Basic Target Search

```python
from biodsa.tools.targets import search_targets_unified

# Search for a target across all databases
results, output = search_targets_unified("BRCA1", limit_per_source=10)
print(output)

# Search specifically for pathways
results, output = search_targets_unified(
    "apoptosis", 
    search_type='pathway',
    limit_per_source=5
)
print(output)

# Search for GO terms
results, output = search_targets_unified(
    "protein kinase activity",
    search_type='go_term'
)
print(output)
```

### Fetch Target Details

```python
from biodsa.tools.targets import fetch_target_details_unified

# Fetch by Ensembl ID (auto-detected)
details, output = fetch_target_details_unified("ENSG00000012048")
print(output)

# Fetch by gene symbol
details, output = fetch_target_details_unified(
    "TP53",
    id_type='gene_symbol',
    include_associations=True  # Include disease associations
)
print(output)

# Fetch pathway details
details, output = fetch_target_details_unified(
    "hsa04210",
    id_type='pathway'
)
print(output)

# Fetch GO term details
details, output = fetch_target_details_unified(
    "GO:0004672",
    id_type='go_term'
)
print(output)
```

## Search Options

### Search Types

- `'target'`: Search for therapeutic targets (Open Targets)
- `'pathway'`: Search for biological pathways (KEGG)
- `'gene'`: Search for genes (KEGG, Open Targets)
- `'go_term'`: Search for Gene Ontology terms
- `None`: Search all types (default)

### Data Sources

- `'opentargets'`: Therapeutic targets from Open Targets Platform
- `'kegg_pathways'`: Biological pathways from KEGG
- `'kegg_genes'`: Gene information from KEGG
- `'gene_ontology'`: GO terms and annotations
- `'proteinatlas'`: Protein expression, cancer markers, and pathology from Human Protein Atlas

### ID Types (Auto-Detected)

- `'ensembl'`: Ensembl gene IDs (e.g., ENSG00000012048)
- `'gene_symbol'`: Gene symbols (e.g., BRCA1, TP53)
- `'pathway'`: KEGG pathway IDs (e.g., hsa04210)
- `'go_term'`: GO term IDs (e.g., GO:0004672)

## Advanced Usage

### Custom Source Selection

```python
# Search only in Open Targets and KEGG pathways
results, output = search_targets_unified(
    "EGFR",
    sources=['opentargets', 'kegg_pathways']
)
```

### Save Results

```python
# Save search results to file
results, output = search_targets_unified(
    "MAPK signaling",
    save_path="/path/to/results.json"
)

# Save detailed information
details, output = fetch_target_details_unified(
    "ENSG00000139618",
    save_path="/path/to/details.json"
)
```

### Access Raw Results

```python
# Get raw results dictionary
results, output = search_targets_unified("kinase activity")

# Access individual source results
opentargets_df = results.get('opentargets')  # Pandas DataFrame
kegg_pathways = results.get('kegg_pathways')  # List of dicts
go_terms_df = results.get('gene_ontology')  # Pandas DataFrame

# Fetch details with associations
details, output = fetch_target_details_unified(
    "BRCA1",
    include_associations=True
)

# Access target information
target_info = details.get('opentargets', {}).get('target', {})
associated_diseases = details.get('opentargets', {}).get('associated_diseases')  # DataFrame
kegg_gene_info = details.get('kegg_gene', {})
```

## Return Formats

### Search Results

The `search_targets_unified()` function returns a tuple:

1. **Results Dictionary**: Contains data from each source
   - DataFrames for Open Targets and Gene Ontology
   - Lists of dictionaries for KEGG sources

2. **Formatted Output String**: Human-readable summary including:
   - Search summary by source
   - Detailed results from each database
   - Aggregated target names and identifiers
   - Cross-database references

### Fetch Details

The `fetch_target_details_unified()` function returns a tuple:

1. **Details Dictionary**: Contains detailed information from each source
   - Target properties and functions
   - Associated diseases (if requested)
   - Pathway information
   - GO term details

2. **Formatted Output String**: Comprehensive summary including:
   - Target overview and properties
   - Disease associations
   - Pathway memberships
   - Functional annotations
   - Cross-database identifiers

## Use Cases

### Drug Discovery Research

```python
# Find therapeutic targets for a disease
results, _ = search_targets_unified("lung cancer", search_type='target')

# Get target details with disease associations
details, _ = fetch_target_details_unified(
    "EGFR",
    include_associations=True
)
```

### Pathway Analysis

```python
# Search for signaling pathways
results, _ = search_targets_unified("MAPK", search_type='pathway')

# Get complete pathway information
details, _ = fetch_target_details_unified("hsa04010", id_type='pathway')

# Access pathway genes
pathway_genes = details.get('kegg_pathway', {}).get('genes', [])
```

### Functional Annotation

```python
# Search for molecular functions
results, _ = search_targets_unified(
    "protein kinase activity",
    search_type='go_term'
)

# Get GO term hierarchy
details, _ = fetch_target_details_unified("GO:0004672")
```

### Cancer Marker Research

```python
# Search for cancer markers
results, _ = search_targets_unified("breast cancer")

# Search for proteins with proteinatlas only
results, _ = search_targets_unified(
    "BRCA1",
    sources=['proteinatlas']
)

# Get protein details with pathology data
details, _ = fetch_target_details_unified(
    "TP53",
    sources=['proteinatlas']
)

# Access cancer pathology information
protein_info = details.get('proteinatlas', {}).get('protein', {})
pathology_info = details.get('proteinatlas', {}).get('pathology', {})
```

### Multi-Database Integration

```python
# Search a gene across all databases
results, output = search_targets_unified("TP53")

# Access different types of information
therapeutic_targets = results.get('opentargets')  # Clinical relevance
pathways = results.get('kegg_pathways')  # Biological pathways
go_terms = results.get('gene_ontology')  # Functional classifications

# Get comprehensive target details
details, _ = fetch_target_details_unified("TP53", include_associations=True)

# Access integrated information
clinical_info = details.get('opentargets')
pathway_info = details.get('kegg_gene')
```

## API Reference

### search_targets_unified()

```python
search_targets_unified(
    search_term: str,
    search_type: Optional[str] = None,
    limit_per_source: int = 10,
    sources: Optional[List[str]] = None,
    save_path: Optional[str] = None
) -> Tuple[Dict[str, Any], str]
```

**Parameters:**
- `search_term`: Search term for biological targets
- `search_type`: Type of search ('target', 'pathway', 'go_term', 'gene', or None)
- `limit_per_source`: Maximum results per source (default: 10)
- `sources`: List of sources to search (default: all)
- `save_path`: Optional file path to save results

**Returns:**
- Tuple of (results dictionary, formatted output string)

### fetch_target_details_unified()

```python
fetch_target_details_unified(
    target_id: str,
    id_type: Optional[str] = None,
    sources: Optional[List[str]] = None,
    include_associations: bool = True,
    save_path: Optional[str] = None
) -> Tuple[Dict[str, Any], str]
```

**Parameters:**
- `target_id`: Target identifier (Ensembl ID, gene symbol, pathway ID, GO ID)
- `id_type`: Type of identifier ('ensembl', 'gene_symbol', 'pathway', 'go_term')
- `sources`: List of sources to fetch from (default: all relevant)
- `include_associations`: Include target-disease associations (default: True)
- `save_path`: Optional file path to save details

**Returns:**
- Tuple of (details dictionary, formatted output string)

## Database Coverage

### Open Targets Platform
- **Therapeutic Targets**: ~60,000 targets
- **Target-Disease Associations**: Evidence-based associations
- **Tractability**: Drug development tractability assessments
- **Safety**: Known and predicted safety liabilities

### KEGG
- **Pathways**: ~500 reference pathways
- **Genes**: Organism-specific gene databases
- **Molecular Interactions**: Pathway maps and networks
- **Diseases**: Disease-gene associations

### Gene Ontology
- **GO Terms**: ~45,000 terms
- **Molecular Function**: Molecular activities of gene products
- **Biological Process**: Larger biological programs
- **Cellular Component**: Subcellular locations

### Human Protein Atlas
- **Proteins**: ~20,000 human proteins
- **Expression Data**: Tissue and cell type-specific expression
- **Subcellular Location**: Protein localization in cells
- **Cancer Pathology**: Cancer-associated proteins and prognostic markers
- **Antibody Validation**: Quality-controlled antibodies

## Best Practices

1. **Start Broad**: Use `search_targets_unified()` first to explore available information
2. **Specify Type**: Use `search_type` to narrow down results when searching specific entity types
3. **Save Results**: Use `save_path` to cache results for later analysis
4. **Include Associations**: Set `include_associations=True` when fetching target details for comprehensive information
5. **Cross-Reference**: Use returned identifiers to link information across databases

## Error Handling

The module handles errors gracefully:

```python
results, output = search_targets_unified("invalid_query")

# Check for errors in output
if "⚠️" in output:
    print("Some sources encountered errors")

# Individual source errors don't prevent other sources from working
if results.get('opentargets') is not None:
    print("Open Targets results available")
```

## Notes

- API rate limits may apply for some databases
- Large pathway queries may take longer to fetch
- Some GO terms may be obsolete (indicated in results)
- Pathway IDs require organism codes (e.g., 'hsa' for human)

## Support

For issues or questions:
- Check the main BioDSA documentation
- Review individual database API documentation
- Report issues to the BioDSA repository

