# UniProt Tools

Comprehensive tools for accessing and analyzing protein data from the UniProt database.

## Overview

UniProt (Universal Protein Resource) is the most comprehensive, high-quality, and freely accessible resource of protein sequence and functional information. This module provides a Python interface to the UniProt REST API, enabling seamless integration of protein data into your bioinformatics workflows.

## Features

### Basic Protein Operations
- **Search proteins**: Search by name, keyword, or complex queries
- **Get protein info**: Retrieve detailed information for specific proteins
- **Search by gene**: Find proteins by gene name or symbol
- **Get protein features**: Extract functional features and domains
- **Validate accessions**: Check if accession numbers are valid

### Sequence Analysis
- **Get protein sequence**: Retrieve amino acid sequences in various formats
- **Analyze composition**: Calculate amino acid composition and properties
- **Export data**: Export protein data in specialized formats (GFF, GenBank, EMBL, XML)

### Comparative & Evolutionary Analysis
- **Compare proteins**: Side-by-side comparison of multiple proteins
- **Find homologs**: Identify homologous proteins across species
- **Find orthologs**: Identify orthologous proteins for evolutionary studies
- **Phylogenetic info**: Retrieve evolutionary relationships and lineage
- **Taxonomy info**: Get detailed taxonomic information

### Structure & Function
- **Get protein structure**: Retrieve 3D structure information from PDB
- **Domain analysis**: Enhanced domain analysis with InterPro, Pfam, and SMART
- **Get variants**: Disease-associated variants and mutations
- **Annotation confidence**: Quality scores for different annotations

### Biological Context
- **Get pathways**: Associated biological pathways (KEGG, Reactome)
- **Get interactions**: Protein-protein interaction networks
- **Search by function**: Search proteins by GO terms or functional annotations
- **Search by localization**: Find proteins by subcellular localization
- **External references**: Links to other databases (PDB, EMBL, RefSeq, etc.)
- **Literature references**: Associated publications and citations

### Advanced Search
- **Batch protein lookup**: Process multiple accessions efficiently
- **Advanced search**: Complex queries with multiple filters
- **Search by taxonomy**: Search by detailed taxonomic classification

## Installation

This module is part of the BioDSA package. Make sure you have the required dependencies:

```bash
pip install requests pandas
```

## Quick Start

```python
from biodsa.tools.uniprot import (
    search_proteins,
    get_protein_info,
    get_protein_sequence,
    compare_proteins
)

# Search for proteins
results = search_proteins("p53", organism="human", size=5)
print(results[['primaryAccession', 'proteinName', 'geneName']])

# Get detailed protein information
protein = get_protein_info("P04637")  # TP53
print(f"Protein: {protein['uniProtkbId']}")

# Get protein sequence
sequence = get_protein_sequence("P04637", format="fasta")
print(sequence)

# Compare multiple proteins
comparison = compare_proteins(["P04637", "P53039"])  # Human and mouse p53
print(comparison)
```

## Usage Examples

### Search and Filter

```python
from biodsa.tools.uniprot import search_proteins, search_by_gene

# Search for kinases in humans
kinases = search_proteins("kinase", organism="human", size=10)

# Search by gene name
tp53_proteins = search_by_gene("TP53", organism="human")
print(tp53_proteins)
```

### Sequence Analysis

```python
from biodsa.tools.uniprot import (
    get_protein_sequence,
    analyze_sequence_composition
)

# Get FASTA sequence
fasta = get_protein_sequence("P04637", format="fasta")

# Analyze amino acid composition
composition = analyze_sequence_composition("P04637")
print(f"Length: {composition['sequenceLength']}")
print(f"Hydrophobic residues: {composition['hydrophobicResidues']}")
```

### Comparative Analysis

```python
from biodsa.tools.uniprot import (
    get_protein_homologs,
    get_protein_orthologs,
    get_phylogenetic_info
)

# Find homologs in mouse
homologs = get_protein_homologs("P04637", organism="mouse", size=10)
print(homologs)

# Find orthologs
orthologs = get_protein_orthologs("P04637", organism="mouse")
print(orthologs)

# Get phylogenetic information
phylo = get_phylogenetic_info("P04637")
print(phylo['taxonomicLineage'])
```

### Structure and Function

```python
from biodsa.tools.uniprot import (
    get_protein_structure,
    get_protein_domains_detailed,
    get_protein_variants
)

# Get structure information
structure = get_protein_structure("P04637")
print(f"PDB structures: {len(structure['pdbReferences'])}")

# Get detailed domain information
domains = get_protein_domains_detailed("P04637")
print(f"Domains: {len(domains['domains'])}")

# Get disease variants
variants = get_protein_variants("P04637")
print(f"Natural variants: {len(variants['naturalVariants'])}")
print(f"Disease variants: {len(variants['diseaseVariants'])}")
```

### Biological Context

```python
from biodsa.tools.uniprot import (
    get_protein_pathways,
    get_protein_interactions,
    search_by_function
)

# Get pathway information
pathways = get_protein_pathways("P04637")
print(f"KEGG pathways: {len(pathways['keggReferences'])}")
print(f"Reactome pathways: {len(pathways['reactomeReferences'])}")

# Get protein interactions
interactions = get_protein_interactions("P04637")
print(f"Interaction partners: {len(interactions['interactionComments'])}")

# Search by GO term
atp_binding = search_by_function(go_term="GO:0005524", organism="human", size=10)
print(atp_binding)
```

### Advanced Searches

```python
from biodsa.tools.uniprot import (
    advanced_search,
    batch_protein_lookup,
    search_by_taxonomy
)

# Advanced search with multiple filters
results = advanced_search(
    query="kinase",
    organism="human",
    min_length=300,
    max_length=500,
    keywords=["ATP-binding"],
    size=20
)
print(results)

# Batch lookup multiple proteins
accessions = ["P04637", "P53039", "Q16637"]
batch_results = batch_protein_lookup(accessions)
for result in batch_results:
    if result['success']:
        print(f"{result['accession']}: OK")
    else:
        print(f"{result['accession']}: {result['error']}")

# Search by taxonomy
human_proteins = search_by_taxonomy(taxonomy_id=9606, size=10)
print(human_proteins)
```

## API Documentation

### UniProtClient

The base client for making API requests to UniProt.

```python
from biodsa.tools.uniprot import UniProtClient

client = UniProtClient(base_url="https://rest.uniprot.org", timeout=30)
```

## Data Sources

- **UniProt API**: https://rest.uniprot.org
- **Documentation**: https://www.uniprot.org/help/api
- **REST API**: https://www.uniprot.org/help/api_queries

## Notes

- The UniProt API has rate limits. Be respectful when making requests.
- Some functions may take longer for proteins with extensive annotations.
- Use batch operations when processing multiple proteins for better efficiency.
- All search functions return DataFrames for easy data manipulation.
- Reviewed entries (Swiss-Prot) generally have higher quality annotations than unreviewed entries (TrEMBL).

## References

- The UniProt Consortium. "UniProt: the universal protein knowledgebase in 2023." Nucleic Acids Research (2023).
- UniProt REST API Documentation: https://www.uniprot.org/help/api

## License

This module is part of BioDSA and follows the same license terms.

