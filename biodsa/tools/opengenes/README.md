# OpenGenes Tools

Tools for accessing and analyzing genes related to aging and longevity from the OpenGenes database.

## Overview

OpenGenes is a curated database of genes associated with aging and longevity across different species. This module provides a Python interface to the OpenGenes API, enabling access to gene data, functional classifications, model organisms, and research on aging mechanisms.

## Features

### Gene Operations
- **Search genes**: Search for genes with various filters
- **Get gene by symbol**: Retrieve detailed information for a specific gene
- **Get latest genes**: Get recently added genes
- **Get lifespan-extending genes**: Find genes associated with increased lifespan
- **Get genes by criteria**: Filter by protein class, aging mechanisms, etc.

### Taxonomy Operations
- **Get model organisms**: List all model organisms in the database
- **Get organism info**: Get detailed information about specific organisms

### Protein Classification
- **Get protein classes**: List all protein functional classes
- **Get class info**: Get detailed information about specific protein classes

### Disease Information
- **Get diseases**: List diseases associated with aging-related genes
- **Get disease categories**: Get disease classification categories

### Research Data
- **Get aging mechanisms**: List known mechanisms of aging
- **Get calorie experiments**: Access data on caloric restriction experiments

## Installation

This module is part of the BioDSA package. Make sure you have the required dependencies:

```bash
pip install requests pandas
```

## Quick Start

```python
from biodsa.tools.opengenes import (
    search_genes,
    get_gene_by_symbol,
    get_model_organisms,
    get_aging_mechanisms
)

# Search for genes
genes = search_genes(page_size=10)
print(genes[['symbol', 'name']].head())

# Get specific gene information
foxo3 = get_gene_by_symbol('FOXO3')
print(f"Gene: {foxo3['symbol']} - {foxo3['name']}")

# Get model organisms
organisms = get_model_organisms()
print(organisms[['name', 'latin_name']].head())

# Get aging mechanisms
mechanisms = get_aging_mechanisms()
print(mechanisms['name'].head())
```

## Usage Examples

### Gene Search and Retrieval

```python
from biodsa.tools.opengenes import (
    search_genes,
    get_gene_by_symbol,
    get_latest_genes
)

# Search for genes with filters
genes = search_genes(
    by_protein_class='transcription_factor',
    page_size=20
)
print(genes)

# Get specific gene
tp53 = get_gene_by_symbol('TP53')
print(f"Gene: {tp53['name']}")

# Get recently added genes
latest = get_latest_genes(page_size=10)
print(latest)
```

### Taxonomy and Organisms

```python
from biodsa.tools.opengenes import get_model_organisms

# Get all model organisms
organisms = get_model_organisms()
print(f"Total organisms: {len(organisms)}")
print(organisms[['name', 'latin_name', 'taxon_id']])
```

### Protein Classes

```python
from biodsa.tools.opengenes import get_protein_classes

# Get all protein classes
classes = get_protein_classes()
print(f"Protein classes: {len(classes)}")
print(classes['name'].head(10))
```

### Aging Research

```python
from biodsa.tools.opengenes import (
    get_aging_mechanisms,
    get_calorie_experiments
)

# Get aging mechanisms
mechanisms = get_aging_mechanisms()
print(mechanisms['name'])

# Get caloric restriction experiments
experiments = get_calorie_experiments(page_size=20)
print(experiments[['organism', 'diet_type', 'median_lifespan_change']])
```

## API Client

The base client for making API requests to OpenGenes.

```python
from biodsa.tools.opengenes import OpenGenesClient

client = OpenGenesClient(base_url="https://open-genes.com/api")

# Use client for custom requests
data = client.search_genes(page=1, page_size=10)
```

## Data Sources

- **OpenGenes API**: https://open-genes.com/api
- **OpenGenes Website**: https://open-genes.com
- **Documentation**: Available on the OpenGenes website

## Notes

- The OpenGenes API may change over time. Some endpoints may return different data structures.
- API rate limits may apply. Be respectful when making requests.
- Not all genes have complete annotation data.
- Some specialized endpoints may require specific parameters or may not be publicly available.

## References

- OpenGenes: A comprehensive database of human genes associated with aging and longevity
- Website: https://open-genes.com

## License

This module is part of BioDSA and follows the same license terms.
