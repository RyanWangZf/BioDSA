# Human Protein Atlas Tools

Comprehensive tools for accessing and analyzing protein data from the Human Protein Atlas.

## Overview

The Human Protein Atlas is a Swedish-based program containing millions of high-resolution images showing the spatial distribution of proteins in 44 different normal human tissue types, 20 different cancer types, 47 different human cell lines, and multiple subcellular locations. This module provides a Python interface to access this rich protein data.

## Features

### Protein Search and Information
- **Search proteins**: Search by gene name, protein name, or keywords
- **Get protein info**: Detailed information for specific proteins
- **Batch protein lookup**: Process multiple proteins simultaneously
- **Get protein classes**: Protein classification and functional annotations
- **Advanced search**: Complex queries with multiple filters

### Expression Analysis
- **Tissue expression**: Tissue-specific RNA expression data
- **Blood expression**: Blood cell expression profiles
- **Brain expression**: Brain region expression data
- **Search by tissue**: Find proteins expressed in specific tissues
- **Compare expression profiles**: Compare expression across multiple proteins

### Subcellular Localization
- **Get subcellular location**: Protein localization data
- **Search by location**: Find proteins in specific cellular compartments

### Pathology and Cancer
- **Get pathology data**: Cancer and pathology information
- **Search cancer markers**: Find cancer-associated proteins and prognostic markers

### Antibody Information
- **Get antibody info**: Antibody validation and staining data

## Installation

This module is part of the BioDSA package. Make sure you have the required dependencies:

```bash
pip install requests pandas
```

## Quick Start

```python
from biodsa.tools.proteinatlas import (
    search_proteins,
    get_protein_info,
    get_tissue_expression,
    get_subcellular_location
)

# Search for proteins
results = search_proteins("p53", max_results=5)
print(results[['Gene', 'Ensembl', 'Gene description']])

# Get detailed protein information
info = get_protein_info("TP53")
print(f"Gene: {info.get('Gene')}")
print(f"Description: {info.get('Gene description')}")

# Get tissue expression
tissue_expr = get_tissue_expression("TP53")
print(f"Liver expression: {tissue_expr.get('t_RNA_liver')}")

# Get subcellular localization
location = get_subcellular_location("TP53")
print(f"Location: {location.get('Subcellular location')}")
```

## Usage Examples

### Protein Search

```python
from biodsa.tools.proteinatlas import search_proteins, get_protein_info

# Basic search
results = search_proteins("BRCA", max_results=10)
print(results)

# Get specific protein information
protein = get_protein_info("BRCA1")
print(f"Gene: {protein.get('Gene')}")
print(f"Ensembl: {protein.get('Ensembl')}")
print(f"Chromosome: {protein.get('Chromosome')}")
```

### Expression Analysis

```python
from biodsa.tools.proteinatlas import (
    get_tissue_expression,
    get_blood_expression,
    get_brain_expression,
    search_by_tissue
)

# Get tissue expression
tissue = get_tissue_expression("ALB")
print(f"Liver expression: {tissue.get('t_RNA_liver')}")
print(f"Kidney expression: {tissue.get('t_RNA_kidney')}")

# Get blood cell expression
blood = get_blood_expression("CD4")
print(f"NK-cell expression: {blood.get('blood_RNA_NK-cell')}")

# Get brain region expression
brain = get_brain_expression("APP")
print(f"Hippocampus: {brain.get('brain_RNA_hippocampal_formation')}")

# Search for liver-specific proteins
liver_proteins = search_by_tissue("liver", expression_level="high", max_results=20)
print(liver_proteins[['Gene', 'Gene description']])
```

### Subcellular Localization

```python
from biodsa.tools.proteinatlas import (
    get_subcellular_location,
    search_by_subcellular_location
)

# Get protein localization
location = get_subcellular_location("TP53")
print(f"Location: {location.get('Subcellular location')}")

# Search for nuclear proteins
nuclear = search_by_subcellular_location("nucleus", reliability="approved")
print(nuclear[['Gene', 'Subcellular location']])
```

### Cancer and Pathology

```python
from biodsa.tools.proteinatlas import (
    get_pathology_data,
    search_cancer_markers
)

# Get pathology data
pathology = get_pathology_data("TP53")
print(f"Breast cancer: {pathology.get('prognostic_Breast_Invasive_Carcinoma_(TCGA)')}")

# Search for unfavorable prognostic markers
markers = search_cancer_markers(prognostic="unfavorable", max_results=50)
print(markers[['Gene', 'Gene description']])
```

### Advanced Search

```python
from biodsa.tools.proteinatlas import advanced_search

# Complex search with multiple filters
results = advanced_search(
    tissue_specific="liver",
    subcellular_location="nucleus",
    protein_class="transcription factors",
    max_results=50
)
print(results)
```

### Batch Operations

```python
from biodsa.tools.proteinatlas import (
    batch_protein_lookup,
    compare_expression_profiles
)

# Batch lookup
genes = ["TP53", "BRCA1", "BRCA2", "MYC", "KRAS"]
results = batch_protein_lookup(genes)
for r in results:
    if r['success']:
        print(f"{r['gene']}: {r['data'].get('Gene description')}")

# Compare expression profiles
comparison = compare_expression_profiles(["TP53", "BRCA1"], expression_type="tissue")
for item in comparison:
    print(f"\n{item['gene']}:")
    print(f"  Liver: {item['expressionData'].get('t_RNA_liver')}")
    print(f"  Brain: {item['expressionData'].get('t_RNA_brain')}")
```

### Antibody Information

```python
from biodsa.tools.proteinatlas import get_antibody_info

# Get antibody validation data
ab_info = get_antibody_info("TP53")
print(f"Antibody: {ab_info.get('Antibody')}")
print(f"Reliability: {ab_info.get('Antibody reliability rating')}")
```

## API Client

The base client for making API requests to the Human Protein Atlas.

```python
from biodsa.tools.proteinatlas import ProteinAtlasClient

client = ProteinAtlasClient(base_url="https://www.proteinatlas.org")

# Use client for custom requests
results = client.search_proteins("TP53")
tissue_expr = client.get_tissue_expression("TP53")
```

## Available Data Columns

The Human Protein Atlas provides many data columns. Common ones include:

### Basic Information
- `Gene` (g): Gene name
- `Gene synonym` (gs): Gene synonyms
- `Ensembl` (eg): Ensembl gene ID
- `Gene description` (gd): Gene description
- `Uniprot` (up): UniProt ID
- `Chromosome` (chr): Chromosome location
- `Protein class` (pc): Protein classification
- `Protein evidence` (pe): Evidence level

### Expression Data
- `t_RNA_*`: Tissue RNA expression levels
- `blood_RNA_*`: Blood cell RNA expression levels
- `brain_RNA_*`: Brain region RNA expression levels

### Localization
- `Subcellular location` (scl): Main subcellular location
- `Subcellular main location` (scml): Main location
- `Subcellular additional location` (scal): Additional locations

### Pathology
- `prognostic_*`: Cancer prognostic information

### Antibody
- `Antibody` (ab): Antibody IDs
- `Antibody reliability rating` (abrr): Reliability score

## Data Sources

- **Human Protein Atlas**: https://www.proteinatlas.org
- **API Documentation**: https://www.proteinatlas.org/about/help
- **Download Data**: https://www.proteinatlas.org/about/download

## Notes

- The API may have rate limits. Be respectful when making requests.
- Some data may not be available for all proteins.
- Expression levels are typically reported as normalized transcript per million (nTPM).
- Use batch operations when processing multiple proteins for better efficiency.

## References

- Uhlén M et al. (2015) Tissue-based map of the human proteome. Science.
- Thul PJ et al. (2017) A subcellular map of the human proteome. Science.
- Uhlen M et al. (2017) A pathology atlas of the human cancer transcriptome. Science.

## License

This module is part of BioDSA and follows the same license terms.

