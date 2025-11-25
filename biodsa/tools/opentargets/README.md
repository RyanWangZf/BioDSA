# Open Targets Platform Tools

This module provides Python tools for interacting with the [Open Targets Platform](https://platform.opentargets.org/) API.

## Overview

Open Targets Platform is a comprehensive resource for target identification and validation. It integrates multiple data sources to provide evidence for target-disease associations, including:

- Genetics & Genomics
- Somatic Mutations
- Drugs
- Pathways & Systems Biology
- Text Mining
- RNA Expression
- Animal Models

## Installation

The required dependencies are:
- `requests` - For HTTP API calls
- `pandas` - For data manipulation
- `logging` - For error handling

These should already be available in the BioDSA environment.

## Available Tools

### Target Tools

#### `search_targets(query, size=25, save_path=None)`
Search for therapeutic targets by gene symbol, name, or description.

**Parameters:**
- `query` (str): Search query (gene symbol, name, description)
- `size` (int): Number of results to return (1-500, default: 25)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with results, formatted output string)

**Example:**
```python
from biodsa.tools.opentargets import search_targets

df, output = search_targets("BRCA1", size=10)
print(output)
print(df[['id', 'name', 'description']])
```

#### `get_target_details(target_id, save_path=None)`
Get comprehensive target information including genomic location, pathways, protein IDs, and tractability.

**Parameters:**
- `target_id` (str): Target Ensembl gene ID (e.g., "ENSG00000139618")
- `save_path` (str, optional): Path to save results as JSON

**Returns:**
- Tuple of (dictionary with details, formatted output string)

**Example:**
```python
from biodsa.tools.opentargets import get_target_details

details, output = get_target_details("ENSG00000139618")
print(output)
```

#### `get_target_associated_diseases(target_id, size=25, min_score=None, save_path=None)`
Get diseases associated with a specific target.

**Parameters:**
- `target_id` (str): Target Ensembl gene ID
- `size` (int): Number of associations to return (default: 25)
- `min_score` (float, optional): Minimum association score threshold (0-1)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with associations, formatted output string)

**Example:**
```python
from biodsa.tools.opentargets import get_target_associated_diseases

df, output = get_target_associated_diseases(
    "ENSG00000139618",
    size=10,
    min_score=0.5
)
print(df[['disease_id', 'disease_name', 'score']])
```

### Disease Tools

#### `search_diseases(query, size=25, save_path=None)`
Search for diseases by name, synonym, or description.

**Parameters:**
- `query` (str): Search query (disease name, synonym, description)
- `size` (int): Number of results to return (1-500, default: 25)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with results, formatted output string)

**Example:**
```python
from biodsa.tools.opentargets import search_diseases

df, output = search_diseases("lung cancer", size=10)
print(output)
```

#### `get_disease_details(disease_id, save_path=None)`
Get comprehensive disease information including synonyms, therapeutic areas, and ontology.

**Parameters:**
- `disease_id` (str): Disease EFO ID (e.g., "EFO_0000508")
- `save_path` (str, optional): Path to save results as JSON

**Returns:**
- Tuple of (dictionary with details, formatted output string)

**Example:**
```python
from biodsa.tools.opentargets import get_disease_details

details, output = get_disease_details("EFO_0000508")
print(output)
```

#### `get_disease_associated_targets(disease_id, size=25, min_score=None, save_path=None)`
Get targets associated with a specific disease.

**Parameters:**
- `disease_id` (str): Disease EFO ID
- `size` (int): Number of associations to return (default: 25)
- `min_score` (float, optional): Minimum association score threshold (0-1)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with associations, formatted output string)

**Example:**
```python
from biodsa.tools.opentargets import get_disease_associated_targets

df, output = get_disease_associated_targets(
    "EFO_0000508",
    size=20,
    min_score=0.5
)
print(df[['target_symbol', 'target_name', 'score']])
```

#### `get_disease_targets_summary(disease_id, size=50, min_score=None, save_path=None)`
Get overview of all targets associated with a disease with top targets highlighted.

**Parameters:**
- `disease_id` (str): Disease EFO ID
- `size` (int): Number of targets to return (default: 50)
- `min_score` (float, optional): Minimum association score threshold (0-1)
- `save_path` (str, optional): Path to save results as JSON

**Returns:**
- Tuple of (dictionary with summary, formatted output string)

**Example:**
```python
from biodsa.tools.opentargets import get_disease_targets_summary

summary, output = get_disease_targets_summary(
    "EFO_0000508",
    size=20,
    min_score=0.6
)
print(output)
print(summary['topTargets'])
```

### Association Tools

#### `get_target_disease_evidence(target_id, disease_id, size=10, save_path=None)`
Get evidence linking a specific target to a specific disease.

**Parameters:**
- `target_id` (str): Target Ensembl gene ID
- `disease_id` (str): Disease EFO ID
- `size` (int): Number of evidence items to return (default: 10)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with evidence, formatted output string)

**Example:**
```python
from biodsa.tools.opentargets import get_target_disease_evidence

df, output = get_target_disease_evidence(
    "ENSG00000139618",
    "EFO_0000508",
    size=5
)
print(df[['datasourceId', 'datatypeId', 'score']])
```

#### `analyze_association_evidence(target_id=None, disease_id=None, min_score=0.5, size=25, save_path=None)`
Analyze target-disease associations with evidence breakdown.

**Parameters:**
- `target_id` (str, optional): Target Ensembl gene ID (provide either this or disease_id)
- `disease_id` (str, optional): Disease EFO ID (provide either this or target_id)
- `min_score` (float): Minimum association score threshold (0-1, default: 0.5)
- `size` (int): Number of associations to analyze (default: 25)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with associations and evidence, formatted output string)

**Example:**
```python
from biodsa.tools.opentargets import analyze_association_evidence

# Analyze associations for a target
df, output = analyze_association_evidence(
    target_id="ENSG00000139618",
    min_score=0.6,
    size=10
)
print(output)
```

### Drug Tools

#### `search_drugs(query, size=25, save_path=None)`
Search for drugs by name or ChEMBL ID.

**Parameters:**
- `query` (str): Search query (drug name or ChEMBL ID)
- `size` (int): Number of results to return (1-500, default: 25)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with results, formatted output string)

**Example:**
```python
from biodsa.tools.opentargets import search_drugs

df, output = search_drugs("aspirin", size=10)
print(output)
```

#### `get_drug_details(drug_id, save_path=None)`
Get comprehensive drug information.

**Parameters:**
- `drug_id` (str): Drug ChEMBL ID (e.g., "CHEMBL25")
- `save_path` (str, optional): Path to save results as JSON

**Returns:**
- Tuple of (dictionary with details, formatted output string)

**Example:**
```python
from biodsa.tools.opentargets import get_drug_details

details, output = get_drug_details("CHEMBL25")
print(output)
```

## Using the Client Directly

For advanced use cases, you can use the `OpenTargetsClient` class directly:

```python
from biodsa.tools.opentargets import OpenTargetsClient

client = OpenTargetsClient()

# Search targets
results = client.search_targets("EGFR", size=10)

# Get target associations
assocs = client.get_target_associations("ENSG00000146648", size=20, min_score=0.5)

# Get disease associations
assocs = client.get_disease_associations("EFO_0000508", size=20)

# Get target-disease evidence
evidence = client.get_target_disease_evidence(
    "ENSG00000146648",
    "EFO_0000508",
    size=10
)
```

## Common ID Formats

- **Target IDs**: Ensembl gene IDs (e.g., `ENSG00000139618` for BRCA2)
- **Disease IDs**: EFO IDs (e.g., `EFO_0000508` for Alzheimer's disease)
- **Drug IDs**: ChEMBL IDs (e.g., `CHEMBL25` for aspirin)

## Finding IDs

You can use the search functions to find IDs:

```python
# Find target ID for a gene
df, _ = search_targets("BRCA2")
target_id = df.iloc[0]['id']  # ENSG00000139618

# Find disease ID
df, _ = search_diseases("Alzheimer's disease")
disease_id = df.iloc[0]['id']  # EFO_0000508
```

## Association Scores

Association scores range from 0 to 1, where:
- **0.7-1.0**: Strong association
- **0.5-0.7**: Moderate association
- **0.0-0.5**: Weak association

The overall score is computed from multiple evidence types:
- `genetic_association`: Genetic evidence
- `somatic_mutation`: Cancer somatic mutations
- `known_drug`: Drugs with known mechanisms
- `affected_pathway`: Pathway perturbations
- `literature`: Text mining evidence
- `rna_expression`: Differential expression
- `animal_model`: Animal model phenotypes

## References

- Open Targets Platform: https://platform.opentargets.org/
- API Documentation: https://platform-docs.opentargets.org/data-access/graphql-api
- GraphQL Playground: https://api.platform.opentargets.org/api/v4/graphql/browser

