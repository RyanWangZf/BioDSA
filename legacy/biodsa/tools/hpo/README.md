# Human Phenotype Ontology (HPO) Tools

This module provides Python tools for interacting with the [Human Phenotype Ontology (HPO)](https://hpo.jax.org/).

## Overview

The Human Phenotype Ontology provides a standardized vocabulary of phenotypic abnormalities encountered in human disease. With over 18,000 terms, the HPO is widely used in:

- Genetic research and rare disease diagnosis
- Clinical decision support systems
- Phenotype-driven gene prioritization
- Patient similarity analysis
- Literature mining and curation

## Installation

The required dependencies are:
- `requests` - For HTTP API calls
- `pandas` - For data manipulation
- `logging` - For error handling

These should already be available in the BioDSA environment.

## Available Tools

### Term Search and Retrieval

#### `search_hpo_terms(query, max_results=20, offset=0, category=None, save_path=None)`
Search for HPO terms by keyword, ID, or synonym.

**Example:**
```python
from biodsa.tools.hpo import search_hpo_terms

df, output = search_hpo_terms("seizure", max_results=10)
print(output)
print(df[['id', 'name']])
```

#### `get_hpo_term_details(hpo_id, save_path=None)`
Get detailed information for a specific HPO term.

**Example:**
```python
from biodsa.tools.hpo import get_hpo_term_details

# HP:0001250 is "Seizure"
details, output = get_hpo_term_details("HP:0001250")
print(output)
```

### Hierarchy Navigation

#### `get_hpo_term_hierarchy(hpo_id, direction="ancestors", max_results=50, offset=0, save_path=None)`
Get hierarchical relationships for an HPO term.

**Parameters:**
- `direction`: "ancestors", "descendants", "parents", or "children"

**Example:**
```python
from biodsa.tools.hpo import get_hpo_term_hierarchy

# Get parent terms
df, output = get_hpo_term_hierarchy("HP:0001250", direction="parents")
print(output)

# Get all ancestors
df, output = get_hpo_term_hierarchy("HP:0001250", direction="ancestors")
print(df)
```

#### `get_hpo_term_path(hpo_id, save_path=None)`
Get the full hierarchical path from root to a specific HPO term.

**Example:**
```python
from biodsa.tools.hpo import get_hpo_term_path

path, output = get_hpo_term_path("HP:0001250")
print(output)
```

### Validation and Comparison

#### `validate_hpo_id(hpo_id)`
Validate an HPO identifier.

**Example:**
```python
from biodsa.tools.hpo import validate_hpo_id

result, output = validate_hpo_id("HP:0001250")
print(output)
print(result['valid_format'], result['exists'])
```

#### `compare_hpo_terms(term1_id, term2_id, save_path=None)`
Compare two HPO terms and find their relationship.

**Example:**
```python
from biodsa.tools.hpo import compare_hpo_terms

comparison, output = compare_hpo_terms("HP:0001250", "HP:0012469")
print(output)
```

### Statistics and Batch Operations

#### `get_hpo_term_statistics(hpo_id, save_path=None)`
Get comprehensive statistics for an HPO term.

**Example:**
```python
from biodsa.tools.hpo import get_hpo_term_statistics

stats, output = get_hpo_term_statistics("HP:0001250")
print(output)
```

#### `batch_get_hpo_terms(hpo_ids, save_path=None)`
Retrieve multiple HPO terms in a single batch (maximum 20).

**Example:**
```python
from biodsa.tools.hpo import batch_get_hpo_terms

df, output = batch_get_hpo_terms(["HP:0001250", "HP:0012469", "HP:0002104"])
print(output)
```

## Using the Client Directly

For advanced use cases, you can use the `HPOClient` class directly:

```python
from biodsa.tools.hpo import HPOClient

client = HPOClient()

# Search terms
results = client.search_terms("microcephaly", max_results=10)

# Get term details
term = client.get_term("HP:0001250")

# Get hierarchy
ancestors = client.get_ancestors("HP:0001250")
descendants = client.get_descendants("HP:0001250")
parents = client.get_parents("HP:0001250")
children = client.get_children("HP:0001250")

# Get full path
path = client.get_term_path("HP:0001250")

# Compare terms
comparison = client.compare_terms("HP:0001250", "HP:0012469")

# Get statistics
stats = client.get_term_statistics("HP:0001250")

# Batch retrieval
terms = client.batch_get_terms(["HP:0001250", "HP:0012469"])
```

## Common ID Formats

- **HPO IDs**: Format is `HP:NNNNNNN` (e.g., `HP:0001250`)
  - The number must be exactly 7 digits
  - The "HP:" prefix is required for API calls

## HPO Structure

The HPO is organized hierarchically:

- **Root term**: HP:0000001 ("All")
- **Main categories**: Include anatomical abnormalities, physiological abnormalities, etc.
- **Depth**: Terms can be many levels deep
- **Relationships**: Terms have parent-child relationships

## Common Use Cases

### Finding Phenotype Terms

```python
from biodsa.tools.hpo import search_hpo_terms

# Search for seizure-related terms
df, output = search_hpo_terms("seizure")
print(output)
```

### Exploring Phenotype Hierarchy

```python
from biodsa.tools.hpo import get_hpo_term_hierarchy

# Get more specific terms (descendants)
descendants, _ = get_hpo_term_hierarchy("HP:0001250", direction="descendants")

# Get more general terms (ancestors)
ancestors, _ = get_hpo_term_hierarchy("HP:0001250", direction="ancestors")
```

### Finding Related Phenotypes

```python
from biodsa.tools.hpo import compare_hpo_terms

# Compare two phenotypes
comparison, output = compare_hpo_terms("HP:0001250", "HP:0012469")
print("Common ancestors:", len(comparison['common_ancestors']))
```

### Batch Phenotype Lookup

```python
from biodsa.tools.hpo import batch_get_hpo_terms

# Get information for multiple phenotypes
phenotypes = ["HP:0001250", "HP:0012469", "HP:0002104", "HP:0001263"]
df, output = batch_get_hpo_terms(phenotypes)
print(df[['id', 'name']])
```

## Common HPO Terms

- **HP:0001250**: Seizure
- **HP:0012469**: Infantile spasms
- **HP:0002104**: Apnea
- **HP:0001263**: Global developmental delay
- **HP:0001298**: Encephalopathy
- **HP:0001999**: Abnormal facial shape
- **HP:0000478**: Abnormality of the eye
- **HP:0000707**: Abnormality of the nervous system

## Evidence and Frequency

HPO terms can be associated with:
- **Frequency information**: How common the phenotype is in a disease
- **Onset information**: When the phenotype typically appears
- **Clinical modifiers**: Severity, progression, etc.

## API Rate Limiting

The HPO API has rate limits. Best practices:
- Cache results when possible
- Use batch operations for multiple terms
- Avoid making too many requests in rapid succession

## References

- HPO Website: https://hpo.jax.org/
- HPO Browser: https://hpo.jax.org/app/browse/term/
- API Documentation: https://hpo.jax.org/api/
- Publications: https://hpo.jax.org/app/help/publications

