# ChEMBL Database Tools

This module provides Python tools for interacting with the [ChEMBL Database](https://www.ebi.ac.uk/chembl/) API.

## Overview

ChEMBL is a manually curated database of bioactive molecules with drug-like properties. It brings together chemical, bioactivity and genomic data to aid the translation of genomic information into effective new drugs. The database contains:

- Over 2 million bioactive compounds
- Over 1.9 million assay results
- Over 76,000 targets
- Drug development information
- Bioactivity measurements

## Installation

The required dependencies are:
- `requests` - For HTTP API calls
- `pandas` - For data manipulation
- `logging` - For error handling

These should already be available in the BioDSA environment.

## Available Tools

ChEMBL tools are organized into three categories:
1. **Compound Tools** - Search and retrieve chemical compound information
2. **Drug Tools** - Access drug development and clinical information
3. **Target Tools** - Search biological targets and bioactivity data

### Compound Tools

#### `search_compounds(query, limit=25, offset=0, save_path=None)`
Search ChEMBL database for compounds by name, synonym, or identifier.

**Parameters:**
- `query` (str): Search query (compound name, synonym, or identifier)
- `limit` (int): Number of results to return (1-1000, default: 25)
- `offset` (int): Number of results to skip (default: 0)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with results, formatted output string)

**Example:**
```python
from biodsa.tools.chembl import search_compounds

df, output = search_compounds("aspirin", limit=10)
print(output)
print(df[['molecule_chembl_id', 'pref_name']])
```

#### `get_compound_details(chembl_id, save_path=None)`
Get detailed information for a specific compound by ChEMBL ID.

**Parameters:**
- `chembl_id` (str): ChEMBL compound ID (e.g., "CHEMBL25")
- `save_path` (str, optional): Path to save results as JSON

**Returns:**
- Tuple of (dictionary with details, formatted output string)

**Example:**
```python
from biodsa.tools.chembl import get_compound_details

# CHEMBL25 is aspirin
details, output = get_compound_details("CHEMBL25")
print(output)
print(details['molecule_properties'])
```

#### `search_similar_compounds(smiles, similarity=70, limit=25, save_path=None)`
Find chemically similar compounds using Tanimoto similarity.

**Parameters:**
- `smiles` (str): SMILES string of the query molecule
- `similarity` (int): Similarity threshold percentage (0-100, default: 70)
- `limit` (int): Number of results to return (default: 25)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with similar compounds, formatted output string)

**Example:**
```python
from biodsa.tools.chembl import search_similar_compounds

# Search for compounds similar to aspirin
df, output = search_similar_compounds(
    "CC(=O)Oc1ccccc1C(=O)O",  # Aspirin SMILES
    similarity=70
)
print(output)
print(df[['molecule_chembl_id', 'pref_name', 'similarity']])
```

#### `search_substructure(smiles, limit=25, save_path=None)`
Find compounds containing specific substructures.

**Parameters:**
- `smiles` (str): SMILES string of the substructure query
- `limit` (int): Number of results to return (default: 25)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with matching compounds, formatted output string)

**Example:**
```python
from biodsa.tools.chembl import search_substructure

# Search for compounds containing benzene ring
df, output = search_substructure("c1ccccc1", limit=10)
print(output)
```

#### `batch_compound_lookup(chembl_ids, save_path=None)`
Process multiple ChEMBL IDs efficiently.

**Parameters:**
- `chembl_ids` (List[str]): List of ChEMBL compound IDs (1-50)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with compounds, formatted output string)

**Example:**
```python
from biodsa.tools.chembl import batch_compound_lookup

df, output = batch_compound_lookup(["CHEMBL25", "CHEMBL59", "CHEMBL192"])
print(output)
```

### Drug Tools

#### `get_drug_indications(molecule_chembl_id=None, indication=None, limit=25, save_path=None)`
Search for therapeutic indications and disease areas.

**Parameters:**
- `molecule_chembl_id` (str, optional): ChEMBL compound ID filter
- `indication` (str, optional): Disease or indication search term
- `limit` (int): Number of results to return (default: 25)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with indications, formatted output string)

**Example:**
```python
from biodsa.tools.chembl import get_drug_indications

# Get indications for a specific drug
df, output = get_drug_indications(molecule_chembl_id="CHEMBL25")
print(output)

# Search by indication
df, output = get_drug_indications(indication="cancer")
print(output)
```

#### `get_drug_mechanisms(molecule_chembl_id=None, target_chembl_id=None, limit=50, save_path=None)`
Get mechanism of action and target interaction data.

**Parameters:**
- `molecule_chembl_id` (str, optional): ChEMBL compound ID filter
- `target_chembl_id` (str, optional): ChEMBL target ID filter
- `limit` (int): Number of results to return (default: 50)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with mechanisms, formatted output string)

**Example:**
```python
from biodsa.tools.chembl import get_drug_mechanisms

# Get mechanisms for a specific drug
df, output = get_drug_mechanisms(molecule_chembl_id="CHEMBL25")
print(output)

# Get drugs targeting a specific target
df, output = get_drug_mechanisms(target_chembl_id="CHEMBL2095173")
print(output)
```

#### `get_drug_clinical_data(chembl_id, save_path=None)`
Get comprehensive clinical and drug development data for a compound.

**Parameters:**
- `chembl_id` (str): ChEMBL compound ID
- `save_path` (str, optional): Path to save results as JSON

**Returns:**
- Tuple of (dictionary with clinical data, formatted output string)

**Example:**
```python
from biodsa.tools.chembl import get_drug_clinical_data

# Get all clinical data for aspirin
data, output = get_drug_clinical_data("CHEMBL25")
print(output)
print(data.keys())  # ['compound', 'indications', 'mechanisms']
```

#### `search_drugs_by_indication(indication, min_phase=0, limit=25, save_path=None)`
Search for drugs treating a specific indication or disease.

**Parameters:**
- `indication` (str): Disease or indication name
- `min_phase` (int): Minimum development phase (0=Preclinical, 4=Approved, default: 0)
- `limit` (int): Number of results to return (default: 25)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with drugs, formatted output string)

**Example:**
```python
from biodsa.tools.chembl import search_drugs_by_indication

# Find all drugs for cancer
df, output = search_drugs_by_indication("cancer", min_phase=1)
print(output)

# Find approved drugs for diabetes
df, output = search_drugs_by_indication("diabetes", min_phase=4)
print(output)
```

### Target Tools

#### `search_targets(query, target_type=None, organism=None, limit=25, save_path=None)`
Search for biological targets by name or type.

**Parameters:**
- `query` (str): Target name or search query
- `target_type` (str, optional): Target type filter (e.g., "SINGLE PROTEIN", "PROTEIN COMPLEX")
- `organism` (str, optional): Organism filter (e.g., "Homo sapiens")
- `limit` (int): Number of results to return (default: 25)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with targets, formatted output string)

**Example:**
```python
from biodsa.tools.chembl import search_targets

# Search for kinase targets
df, output = search_targets("kinase", limit=10)
print(output)

# Search for human protein targets
df, output = search_targets(
    "receptor",
    target_type="SINGLE PROTEIN",
    organism="Homo sapiens"
)
print(output)
```

#### `get_target_details(chembl_id, save_path=None)`
Get detailed information for a specific target by ChEMBL target ID.

**Parameters:**
- `chembl_id` (str): ChEMBL target ID (e.g., "CHEMBL2095173")
- `save_path` (str, optional): Path to save results as JSON

**Returns:**
- Tuple of (dictionary with target details, formatted output string)

**Example:**
```python
from biodsa.tools.chembl import get_target_details

# Get details for COX-2
details, output = get_target_details("CHEMBL2095173")
print(output)
```

#### `search_by_uniprot(uniprot_id, limit=25, save_path=None)`
Find ChEMBL targets by UniProt accession.

**Parameters:**
- `uniprot_id` (str): UniProt accession number (e.g., "P00533")
- `limit` (int): Number of results to return (default: 25)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with targets, formatted output string)

**Example:**
```python
from biodsa.tools.chembl import search_by_uniprot

# Find targets for EGFR UniProt ID
df, output = search_by_uniprot("P00533")
print(output)
```

#### `get_target_bioactivities(target_chembl_id, activity_type=None, limit=100, save_path=None)`
Get bioactivity measurements for a specific target.

**Parameters:**
- `target_chembl_id` (str): ChEMBL target ID (e.g., "CHEMBL2095173")
- `activity_type` (str, optional): Activity type filter (e.g., "IC50", "Ki", "EC50")
- `limit` (int): Number of results to return (default: 100)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with bioactivities, formatted output string)

**Example:**
```python
from biodsa.tools.chembl import get_target_bioactivities

# Get all IC50 values for COX-2
df, output = get_target_bioactivities(
    "CHEMBL2095173",
    activity_type="IC50"
)
print(output)
```

#### `get_compounds_for_target(target_chembl_id, activity_threshold=None, activity_type="IC50", limit=50, save_path=None)`
Get active compounds for a specific target.

**Parameters:**
- `target_chembl_id` (str): ChEMBL target ID (e.g., "CHEMBL2095173")
- `activity_threshold` (float, optional): Maximum activity value threshold (e.g., 1000 for IC50 < 1000nM)
- `activity_type` (str): Activity type to filter (default: "IC50")
- `limit` (int): Number of results to return (default: 50)
- `save_path` (str, optional): Path to save results as CSV

**Returns:**
- Tuple of (DataFrame with compounds, formatted output string)

**Example:**
```python
from biodsa.tools.chembl import get_compounds_for_target

# Get compounds with IC50 < 100nM for COX-2
df, output = get_compounds_for_target(
    "CHEMBL2095173",
    activity_threshold=100,
    activity_type="IC50"
)
print(output)
```

## Using the Client Directly

For advanced use cases, you can use the `ChEMBLClient` class directly:

```python
from biodsa.tools.chembl import ChEMBLClient

client = ChEMBLClient()

# Search compounds
results = client.search_compounds("ibuprofen", limit=10)

# Get compound details
compound = client.get_compound_by_id("CHEMBL521")

# Search similar compounds
similar = client.search_similar_compounds(
    "CC(C)Cc1ccc(cc1)C(C)C(=O)O",  # Ibuprofen
    similarity=70
)

# Search for targets
targets = client.search_targets("kinase", limit=20)

# Get activities
activities = client.search_activities(
    molecule_chembl_id="CHEMBL25",
    limit=50
)

# Get drug indications
indications = client.get_drug_indications(
    molecule_chembl_id="CHEMBL25"
)

# Get mechanisms of action
mechanisms = client.get_mechanisms(
    molecule_chembl_id="CHEMBL25"
)

# Advanced search with property filters
results = client.advanced_compound_search(
    min_mw=200,
    max_mw=500,
    max_hbd=5,
    max_hba=10,
    limit=25
)
```

## Common ID Formats

- **Compound IDs**: ChEMBL IDs (e.g., `CHEMBL25` for aspirin)
- **Target IDs**: ChEMBL target IDs (e.g., `CHEMBL2095173` for COX-2)
- **Assay IDs**: ChEMBL assay IDs (e.g., `CHEMBL1217643`)

## Finding IDs

You can use the search functions to find IDs:

```python
# Find compound ID
df, _ = search_compounds("aspirin")
chembl_id = df.iloc[0]['molecule_chembl_id']  # CHEMBL25

# Get compound details
details, _ = get_compound_details(chembl_id)
```

## Molecular Properties

ChEMBL provides various molecular properties:
- **MW (Molecular Weight)**: Weight in Daltons
- **LogP**: Lipophilicity
- **HBD**: Hydrogen bond donors
- **HBA**: Hydrogen bond acceptors
- **PSA**: Polar surface area
- **RTB**: Rotatable bonds
- **Lipinski Violations**: Number of Rule of Five violations

## Drug Development Phases

ChEMBL tracks drug development phases:
- **0**: Preclinical
- **1**: Phase I clinical trial
- **2**: Phase II clinical trial
- **3**: Phase III clinical trial
- **4**: Approved drug

## Similarity Search

Similarity searches use the Tanimoto coefficient:
- **70-100%**: Very similar compounds
- **50-70%**: Similar compounds
- **30-50%**: Some structural similarity
- **0-30%**: Different compounds

## Advanced Search

You can filter compounds by multiple properties:

```python
from biodsa.tools.chembl import ChEMBLClient

client = ChEMBLClient()

# Drug-like molecules (Lipinski Rule of Five)
results = client.advanced_compound_search(
    min_mw=180,
    max_mw=500,
    max_logp=5,
    max_hbd=5,
    max_hba=10,
    limit=50
)
```

## Common Use Cases

### Drug Discovery Workflow

```python
from biodsa.tools.chembl import (
    search_targets,
    get_target_bioactivities,
    get_compounds_for_target,
    get_compound_details
)

# 1. Find a target of interest
targets_df, _ = search_targets("kinase", limit=5)
target_id = targets_df.iloc[0]['target_chembl_id']

# 2. Get active compounds for that target
compounds_df, _ = get_compounds_for_target(
    target_id,
    activity_threshold=100,  # IC50 < 100nM
    activity_type="IC50"
)

# 3. Get details for the most potent compound
if not compounds_df.empty:
    best_compound = compounds_df.iloc[0]['molecule_chembl_id']
    details, output = get_compound_details(best_compound)
    print(output)
```

### Clinical Development Research

```python
from biodsa.tools.chembl import (
    search_drugs_by_indication,
    get_drug_clinical_data,
    get_drug_mechanisms
)

# 1. Find approved drugs for a disease
drugs_df, _ = search_drugs_by_indication("cancer", min_phase=4)

# 2. Get comprehensive clinical data
drug_id = drugs_df.iloc[0]['molecule_chembl_id']
clinical_data, output = get_drug_clinical_data(drug_id)
print(output)

# 3. Analyze mechanisms of action
mech_df, _ = get_drug_mechanisms(molecule_chembl_id=drug_id)
print(mech_df[['mechanism_of_action', 'target_pref_name', 'action_type']])
```

### Target-Based Research

```python
from biodsa.tools.chembl import (
    search_by_uniprot,
    get_target_details,
    get_target_bioactivities,
    get_drug_mechanisms
)

# 1. Find target by UniProt ID
targets_df, _ = search_by_uniprot("P00533")  # EGFR
target_id = targets_df.iloc[0]['target_chembl_id']

# 2. Get target details
details, output = get_target_details(target_id)
print(output)

# 3. Get bioactivity data
bioact_df, _ = get_target_bioactivities(target_id, activity_type="IC50")

# 4. Find drugs targeting this target
drugs_df, _ = get_drug_mechanisms(target_chembl_id=target_id)
```

### Finding Similar Drugs

```python
from biodsa.tools.chembl import search_compounds, get_compound_details, search_similar_compounds

# Find a reference drug
df, _ = search_compounds("ibuprofen")
details, _ = get_compound_details(df.iloc[0]['molecule_chembl_id'])

# Get its SMILES
smiles = details['molecule_structures']['canonical_smiles']

# Find similar compounds
similar_df, output = search_similar_compounds(smiles, similarity=70)
print(output)
```

### Checking Drug-like Properties

```python
from biodsa.tools.chembl import get_compound_details

details, output = get_compound_details("CHEMBL25")
props = details['molecule_properties']

# Check Lipinski Rule of Five
violations = props.get('num_ro5_violations', 0)
if violations == 0:
    print("Drug-like (Lipinski compliant)")
else:
    print(f"Not drug-like ({violations} Lipinski violations)")
```

### Finding Compounds with Specific Substructure

```python
from biodsa.tools.chembl import search_substructure

# Find all compounds with a thiazole ring
df, output = search_substructure("c1scnc1", limit=50)
print(f"Found {len(df)} compounds with thiazole rings")
```

## API Rate Limiting

The ChEMBL API has rate limits:
- Be respectful of the service
- Add delays between batch requests if needed
- Cache results when possible

## References

- ChEMBL Database: https://www.ebi.ac.uk/chembl/
- API Documentation: https://chembl.gitbook.io/chembl-interface-documentation/web-services
- ChEMBL Paper: Mendez et al. (2019) Nucleic Acids Research

