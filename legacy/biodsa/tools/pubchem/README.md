# PubChem Tools

Comprehensive tools for accessing and analyzing chemical compound data from PubChem.

## Overview

PubChem is the world's largest collection of freely accessible chemical information. It provides information on the biological activities of small molecules, serving as a chemical information resource for scientists, students, and the general public. This module provides a Python interface to the PubChem PUG REST API.

## Features

### Compound Search and Retrieval
- **Search compounds**: Search by name, SMILES, InChI, CAS number, or formula
- **Get compound info**: Detailed information for specific compounds
- **Get synonyms**: All names and synonyms for compounds
- **Batch lookup**: Process multiple compounds efficiently

### Structure Similarity and Analysis
- **Similarity search**: Find chemically similar compounds using Tanimoto similarity
- **Substructure search**: Find compounds containing specific substructures
- **Superstructure search**: Find larger compounds containing query structure
- **3D conformers**: Get 3D structural information
- **Stereochemistry analysis**: Analyze chirality and stereoisomers

### Chemical Properties and Descriptors
- **Molecular properties**: MW, LogP, TPSA, H-bond donors/acceptors, etc.
- **Calculate descriptors**: Comprehensive molecular descriptors
- **Drug-likeness**: Assess using Lipinski Rule of Five and Veber rules
- **Molecular complexity**: Analyze complexity and synthetic accessibility

### Bioassay and Activity Data
- **Assay information**: Detailed bioassay descriptions
- **Compound bioactivities**: All bioassay results for compounds
- **Activity comparison**: Compare bioactivity profiles across compounds

### Safety and Toxicity
- **Safety data**: GHS hazard classifications
- **Toxicity information**: LD50, carcinogenicity, mutagenicity data

### Cross-References and Integration
- **External references**: Links to ChEMBL, DrugBank, KEGG, etc.
- **Literature references**: PubMed citations and publications

## Installation

This module is part of the BioDSA package. Make sure you have the required dependencies:

```bash
pip install requests pandas
```

## Quick Start

```python
from biodsa.tools.pubchem import (
    search_compounds,
    get_compound_info,
    search_similar_compounds,
    assess_drug_likeness
)

# Search for compounds
results = search_compounds("aspirin", max_records=10)
print(results[['CID', 'MolecularFormula', 'MolecularWeight']])

# Get compound information
info = get_compound_info(2244)  # Aspirin CID
print(info)

# Search for similar compounds
similar = search_similar_compounds("CC(=O)OC1=CC=CC=C1C(=O)O", threshold=85)
print(similar)

# Assess drug-likeness
assessment = assess_drug_likeness(2244)
print(f"Passes Lipinski: {assessment['passes_lipinski']}")
print(f"Violations: {assessment['lipinski_violations']}")
```

## Usage Examples

### Compound Search

```python
from biodsa.tools.pubchem import (
    search_compounds,
    search_by_smiles,
    search_by_cas_number
)

# Search by name
df = search_compounds("ibuprofen", max_records=5)
print(df)

# Search by SMILES
result = search_by_smiles("CC(C)Cc1ccc(cc1)C(C)C(=O)O")
print(f"Found CID: {result['cid']}")

# Search by CAS number
result = search_by_cas_number("15687-27-1")
print(f"Found CID: {result['cid']}")
```

### Structure Similarity

```python
from biodsa.tools.pubchem import (
    search_similar_compounds,
    substructure_search,
    superstructure_search
)

# Find similar compounds
aspirin_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"
similar = search_similar_compounds(aspirin_smiles, threshold=90)
print(f"Found {len(similar)} similar compounds")

# Substructure search (find benzene-containing compounds)
benzene_smiles = "c1ccccc1"
results = substructure_search(benzene_smiles, max_records=50)
print(results)

# Superstructure search
ethyl_smiles = "CC"
results = superstructure_search(ethyl_smiles, max_records=50)
print(results)
```

### Chemical Properties

```python
from biodsa.tools.pubchem import (
    get_compound_properties,
    calculate_descriptors,
    assess_drug_likeness,
    analyze_molecular_complexity
)

cid = 2244  # Aspirin

# Get basic properties
props = get_compound_properties(cid)
print(f"Molecular Weight: {props.get('MolecularWeight')}")
print(f"LogP: {props.get('XLogP')}")
print(f"TPSA: {props.get('TPSA')}")

# Calculate all descriptors
descriptors = calculate_descriptors(cid, descriptor_type='all')
print(descriptors)

# Assess drug-likeness
assessment = assess_drug_likeness(cid)
print(f"Lipinski violations: {assessment['lipinski_violations']}")
print(f"Veber compliant: {assessment['veber_compliant']}")
print(f"Assessment: {assessment['assessment']}")

# Analyze complexity
complexity = analyze_molecular_complexity(cid)
print(f"Complexity score: {complexity['complexity_score']}")
print(f"Category: {complexity['complexity_category']}")
```

### Stereochemistry Analysis

```python
from biodsa.tools.pubchem import (
    analyze_stereochemistry,
    get_3d_conformers
)

# Analyze stereochemistry
stereo = analyze_stereochemistry(2244)
print(f"Atom stereo centers: {stereo.get('AtomStereoCount')}")
print(f"Defined centers: {stereo.get('DefinedAtomStereoCount')}")
print(f"Isomeric SMILES: {stereo.get('IsomericSMILES')}")

# Get 3D conformer data
conformers = get_3d_conformers(2244)
print(f"3D Volume: {conformers.get('Volume3D')}")
print(f"Conformer count: {conformers.get('ConformerCount3D')}")
```

### Bioassay Data

```python
from biodsa.tools.pubchem import (
    get_compound_bioactivities,
    get_assay_info,
    compare_activity_profiles
)

# Get bioactivities for a compound
aids = get_compound_bioactivities(2244)
print(f"Found {len(aids)} bioassays")

# Get detailed assay information
if aids:
    assay = get_assay_info(aids[0])
    print(assay)

# Compare activity profiles
comparison = compare_activity_profiles([2244, 3672, 5090])
print(comparison)
```

### Safety and Toxicity

```python
from biodsa.tools.pubchem import (
    get_safety_data,
    get_toxicity_info
)

# Get safety classifications
safety = get_safety_data(2244)
print(safety)

# Get toxicity information
toxicity = get_toxicity_info(2244)
print(toxicity)
```

### Batch Operations

```python
from biodsa.tools.pubchem import batch_compound_lookup

# Process multiple compounds
cids = [2244, 3672, 5090, 2520, 3033]  # Various drugs
results = batch_compound_lookup(cids, operation='property')

for r in results:
    if r['success']:
        print(f"CID {r['cid']}: MW = {r['data'].get('MolecularWeight')}")
    else:
        print(f"CID {r['cid']}: Error - {r['error']}")
```

## API Client

The base client for making API requests to PubChem.

```python
from biodsa.tools.pubchem import PubChemClient

client = PubChemClient(base_url="https://pubchem.ncbi.nlm.nih.gov/rest/pug")

# Use client for custom requests
cids = client.search_compounds("caffeine")
props = client.get_compound_properties(cids[0])
```

## Common Use Cases

### Drug Discovery

```python
# Find drug-like compounds similar to a lead compound
lead_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"
similar = search_similar_compounds(lead_smiles, threshold=85)

for idx, row in similar.iterrows():
    cid = row['CID']
    assessment = assess_drug_likeness(cid)
    if assessment['passes_lipinski']:
        print(f"CID {cid}: Drug-like candidate")
```

### Toxicity Screening

```python
# Screen compounds for safety concerns
test_cids = [2244, 3672, 5090]

for cid in test_cids:
    safety = get_safety_data(cid)
    props = get_compound_properties(cid)
    print(f"\nCID {cid}:")
    print(f"  MW: {props.get('MolecularWeight')}")
    print(f"  Safety data: {safety}")
```

### Structure-Activity Relationship (SAR)

```python
# Analyze SAR by comparing similar compounds
base_smiles = "c1ccccc1"
similar = search_similar_compounds(base_smiles, threshold=70)

for idx, row in similar.iterrows():
    cid = row['CID']
    activities = get_compound_bioactivities(cid)
    complexity = analyze_molecular_complexity(cid)
    print(f"CID {cid}: {len(activities)} bioassays, complexity: {complexity['complexity_category']}")
```

## Data Sources

- **PubChem**: https://pubchem.ncbi.nlm.nih.gov/
- **PUG REST API**: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
- **API Tutorial**: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest-tutorial

## Notes

- The PubChem API has rate limits. Be respectful when making requests.
- Some data may not be available for all compounds.
- Batch operations are more efficient than individual requests.
- 3D conformer data is not available for all compounds.
- Safety and toxicity data comes from various sources and should be verified.

## References

- Kim S et al. (2021) PubChem in 2021: new data content and improved web interfaces. Nucleic Acids Res.
- Bolton EE et al. (2008) PubChem: integrated platform of small molecules and biological activities. Annual Reports in Computational Chemistry.

## License

This module is part of BioDSA and follows the same license terms.

