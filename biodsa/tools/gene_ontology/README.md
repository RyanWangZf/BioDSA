

# Gene Ontology Tools

This module provides Python tools for interacting with the [Gene Ontology (GO)](http://geneontology.org/).

## Overview

The Gene Ontology project provides a computational representation of current scientific knowledge about the functions of genes and gene products. It provides three structured, controlled vocabularies (ontologies):

- **Molecular Function**: Molecular-level activities performed by gene products
- **Biological Process**: Larger processes accomplished by multiple molecular activities
- **Cellular Component**: Locations relative to cellular structures

## Installation

The required dependencies are:
- `requests` - For HTTP API calls
- `pandas` - For data manipulation
- `logging` - For error handling

These should already be available in the BioDSA environment.

## Available Tools

### Term Tools

#### `search_go_terms(query, ontology=None, limit=25, exact=False, include_obsolete=False, save_path=None)`
Search across Gene Ontology terms.

**Parameters:**
- `query` (str): Search query (term name, keyword, or definition)
- `ontology` (str, optional): GO ontology to search ("molecular_function", "biological_process", "cellular_component", or None for all)
- `limit` (int): Number of results to return (1-500, default: 25)
- `exact` (bool): Exact match only (default: False)
- `include_obsolete` (bool): Include obsolete terms (default: False)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with results, formatted output string)

**Example:**
```python
from biodsa.tools.gene_ontology import search_go_terms

df, output = search_go_terms("kinase activity", limit=10)
print(output)
print(df[['id', 'name', 'namespace']])
```

#### `get_go_term_details(go_id, save_path=None)`
Get detailed information for a specific GO term.

**Parameters:**
- `go_id` (str): GO term identifier (e.g., "GO:0008150")
- `save_path` (str, optional): Path to save results as JSON

**Returns:**
- Tuple of (dictionary with details, formatted output string)

**Example:**
```python
from biodsa.tools.gene_ontology import get_go_term_details

# GO:0008150 is "biological_process"
details, output = get_go_term_details("GO:0008150")
print(output)
```

#### `get_go_term_hierarchy(go_id, direction="ancestors", save_path=None)`
Get hierarchical relationships for a GO term.

**Parameters:**
- `go_id` (str): GO term identifier
- `direction` (str): "ancestors" for parent terms, "descendants" for child terms, or "children" for direct children
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with related terms, formatted output string)

**Example:**
```python
from biodsa.tools.gene_ontology import get_go_term_hierarchy

# Get parent terms
df, output = get_go_term_hierarchy("GO:0004672", direction="ancestors")
print(output)

# Get child terms
df, output = get_go_term_hierarchy("GO:0004672", direction="children")
print(df)
```

#### `validate_go_id(go_id)`
Validate a GO identifier.

**Parameters:**
- `go_id` (str): GO identifier to validate

**Returns:**
- Tuple of (validation results dictionary, formatted output string)

**Example:**
```python
from biodsa.tools.gene_ontology import validate_go_id

result, output = validate_go_id("GO:0008150")
print(output)
print(result['valid_format'], result['exists'])
```

#### `get_ontology_statistics()`
Get statistics about GO ontologies.

**Returns:**
- Tuple of (statistics dictionary, formatted output string)

**Example:**
```python
from biodsa.tools.gene_ontology import get_ontology_statistics

stats, output = get_ontology_statistics()
print(output)
```

### Annotation Tools

#### `get_gene_annotations(gene_product_id, taxon_id=None, ontology=None, evidence_code=None, limit=100, save_path=None)`
Get GO annotations for a specific gene.

**Parameters:**
- `gene_product_id` (str): Gene product identifier (e.g., UniProt ID, gene symbol)
- `taxon_id` (int, optional): NCBI taxonomy ID (e.g., 9606 for human)
- `ontology` (str, optional): GO ontology filter
- `evidence_code` (str, optional): Evidence code filter (e.g., "IDA", "IEA")
- `limit` (int): Number of results to return (default: 100)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with annotations, formatted output string)

**Example:**
```python
from biodsa.tools.gene_ontology import get_gene_annotations

# Get annotations for a human protein
df, output = get_gene_annotations("P31749", taxon_id=9606)
print(output)
print(df[['go_id', 'go_name', 'evidence_code']])
```

#### `get_term_annotations(go_id, taxon_id=None, evidence_code=None, limit=100, save_path=None)`
Get annotations for a specific GO term.

**Parameters:**
- `go_id` (str): GO term identifier
- `taxon_id` (int, optional): NCBI taxonomy ID filter
- `evidence_code` (str, optional): Evidence code filter
- `limit` (int): Number of results to return (default: 100)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with annotations, formatted output string)

**Example:**
```python
from biodsa.tools.gene_ontology import get_term_annotations

# Get genes annotated with protein kinase activity in human
df, output = get_term_annotations("GO:0004672", taxon_id=9606)
print(output)
print(df[['gene_symbol', 'gene_product_id', 'evidence_code']])
```

#### `get_evidence_codes()`
Get list of GO evidence codes.

**Returns:**
- Tuple of (DataFrame with evidence codes, formatted output string)

**Example:**
```python
from biodsa.tools.gene_ontology import get_evidence_codes

df, output = get_evidence_codes()
print(output)
print(df[df['category'] == 'experimental'])
```

## Using the Client Directly

For advanced use cases, you can use the `GeneOntologyClient` class directly:

```python
from biodsa.tools.gene_ontology import GeneOntologyClient

client = GeneOntologyClient()

# Search terms
results = client.search_terms("kinase activity", limit=10)

# Get term details
term = client.get_term("GO:0004672")

# Get term hierarchy
ancestors = client.get_term_ancestors("GO:0004672")
descendants = client.get_term_descendants("GO:0004672")
children = client.get_term_children("GO:0004672")

# Get annotations
annotations = client.get_annotations(
    go_id="GO:0004672",
    taxon_id=9606,
    limit=100
)

# Get gene annotations
gene_annotations = client.get_gene_annotations(
    "P31749",
    taxon_id=9606
)

# Validate GO ID
validation = client.validate_term("GO:0008150")
```

## Common ID Formats

- **GO IDs**: Format is `GO:NNNNNNN` (e.g., `GO:0008150`)
- **Gene Product IDs**: UniProt IDs (e.g., `P31749`), gene symbols, or other database IDs
- **Taxonomy IDs**: NCBI Taxonomy database IDs (e.g., `9606` for human, `10090` for mouse)

## GO Ontologies

### Molecular Function (F)
- **Root term:** GO:0003674
- **Description:** Molecular-level activities performed by gene products
- **Examples:** kinase activity, DNA binding, receptor activity

### Biological Process (P)
- **Root term:** GO:0008150
- **Description:** Larger processes accomplished by multiple molecular activities
- **Examples:** cell division, signal transduction, DNA repair

### Cellular Component (C)
- **Root term:** GO:0005575
- **Description:** Locations relative to cellular structures
- **Examples:** nucleus, mitochondrion, membrane

## Evidence Codes

GO annotations include evidence codes that indicate how the annotation was determined:

### Experimental Evidence (Most Reliable)
- **EXP**: Inferred from Experiment
- **IDA**: Inferred from Direct Assay
- **IPI**: Inferred from Physical Interaction
- **IMP**: Inferred from Mutant Phenotype
- **IGI**: Inferred from Genetic Interaction
- **IEP**: Inferred from Expression Pattern

### Computational Evidence
- **ISS**: Inferred from Sequence or Structural Similarity
- **ISO**: Inferred from Sequence Orthology
- **ISA**: Inferred from Sequence Alignment
- **ISM**: Inferred from Sequence Model

### Author/Curator Statements
- **TAS**: Traceable Author Statement
- **NAS**: Non-traceable Author Statement
- **IC**: Inferred by Curator
- **ND**: No biological Data available

### Electronic Annotation (Least Reliable)
- **IEA**: Inferred from Electronic Annotation

## Common Use Cases

### Finding GO Terms

```python
from biodsa.tools.gene_ontology import search_go_terms

# Search for terms related to cell division
df, output = search_go_terms("cell division", ontology="biological_process")
print(output)
```

### Getting Gene Function

```python
from biodsa.tools.gene_ontology import get_gene_annotations

# Get functional annotations for a gene
df, output = get_gene_annotations("P31749", taxon_id=9606)

# Filter for experimental evidence
experimental = df[df['evidence_code'].isin(['IDA', 'IMP', 'IGI', 'IEP'])]
print(experimental)
```

### Exploring GO Hierarchy

```python
from biodsa.tools.gene_ontology import get_go_term_hierarchy

# Get parent terms (more general)
ancestors, _ = get_go_term_hierarchy("GO:0004672", direction="ancestors")

# Get child terms (more specific)
descendants, _ = get_go_term_hierarchy("GO:0004672", direction="descendants")
```

### Finding Genes with Specific Function

```python
from biodsa.tools.gene_ontology import get_term_annotations

# Find all human genes with protein kinase activity
df, output = get_term_annotations(
    "GO:0004672",  # protein kinase activity
    taxon_id=9606,  # human
    evidence_code="IDA"  # experimental evidence only
)
print(df[['gene_symbol', 'gene_product_id']])
```

## Common Taxonomy IDs

- **9606**: Homo sapiens (human)
- **10090**: Mus musculus (mouse)
- **10116**: Rattus norvegicus (rat)
- **7227**: Drosophila melanogaster (fruit fly)
- **6239**: Caenorhabditis elegans (worm)
- **559292**: Saccharomyces cerevisiae S288C (baker's yeast)
- **3702**: Arabidopsis thaliana (thale cress)

## API Rate Limiting

The QuickGO API has rate limits. Best practices:
- Cache results when possible
- Avoid making too many requests in rapid succession
- Use appropriate limit parameters

## References

- Gene Ontology Consortium: http://geneontology.org/
- QuickGO: https://www.ebi.ac.uk/QuickGO/
- AmiGO: http://amigo.geneontology.org/
- GO Publications: https://geneontology.org/docs/publications/

