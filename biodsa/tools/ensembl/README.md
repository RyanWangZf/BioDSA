# Ensembl Tools

Comprehensive tools for accessing and analyzing genomic data from the Ensembl database.

## Overview

Ensembl is a genome browser for vertebrate genomes that provides comprehensive, high-quality genomic annotations. This module provides a Python interface to the Ensembl REST API, enabling access to genes, transcripts, sequences, variants, and comparative genomics data.

## Features

### Gene & Transcript Information
- **Lookup gene**: Get detailed gene information by ID or symbol
- **Get transcripts**: Retrieve all transcripts for a gene
- **Search genes**: Search by name, description, or identifier
- **Get gene by symbol**: Direct symbol-to-gene lookup
- **Batch gene lookup**: Process multiple genes simultaneously

### Sequence Data
- **Get sequence**: Retrieve DNA sequences for regions or features
- **Get CDS sequence**: Extract coding sequences from transcripts
- **Translate sequence**: Convert DNA to protein sequences
- **Batch sequence fetch**: Retrieve multiple sequences efficiently

### Comparative Genomics
- **Get homologs**: Find orthologs and paralogs across species
- **Get gene tree**: Retrieve phylogenetic trees for gene families
- **Compare genes across species**: Multi-species gene comparison

### Variant Analysis
- **Get variants**: Find variants in genomic regions
- **Get variant info**: Detailed variant information

### Regulatory Features
- **Get regulatory features**: Find enhancers, promoters, TFBS
- **Get overlapping features**: Find all features in a region

### Annotations & Assembly
- **Get cross-references**: External database links
- **List species**: Available species and assemblies
- **Get assembly info**: Genome assembly statistics
- **Get karyotype**: Chromosome information

## Installation

This module is part of the BioDSA package. Make sure you have the required dependencies:

```bash
pip install requests pandas
```

## Quick Start

```python
from biodsa.tools.ensembl import (
    lookup_gene,
    get_transcripts,
    get_sequence,
    get_homologs
)

# Look up a gene
gene = lookup_gene("BRCA2")
print(f"Gene: {gene['display_name']} ({gene['id']})")
print(f"Location: {gene['seq_region_name']}:{gene['start']}-{gene['end']}")

# Get transcripts
transcripts = get_transcripts("ENSG00000139618")
print(f"Transcripts: {transcripts['transcript_count']}")

# Get sequence
seq = get_sequence("1:1000000-1001000")
print(f"Sequence length: {len(seq['seq'])}")

# Find homologs in mouse
homologs = get_homologs("ENSG00000139618", target_species="mus_musculus")
if 'ortholog' in homologs:
    print(f"Mouse ortholog: {homologs['ortholog']['symbol']}")
```

## Usage Examples

### Gene Operations

```python
from biodsa.tools.ensembl import (
    lookup_gene,
    search_genes,
    get_transcripts
)

# Search for genes
results = search_genes("BRCA", limit=10)
print(results[['id', 'display_name', 'biotype', 'description']])

# Get specific gene with full details
gene = lookup_gene("ENSG00000139618", expand=True)
print(f"Gene: {gene['display_name']}")
print(f"Description: {gene['description']}")
print(f"Biotype: {gene['biotype']}")

# Get all transcripts
transcripts = get_transcripts("ENSG00000139618")
for t in transcripts['transcripts']:
    print(f"Transcript: {t['id']} (canonical: {t.get('is_canonical', 0)})")

# Get only canonical transcript
canonical = get_transcripts("ENSG00000139618", canonical_only=True)
print(f"Canonical transcript: {canonical['transcripts'][0]['id']}")
```

### Sequence Operations

```python
from biodsa.tools.ensembl import (
    get_sequence,
    get_cds_sequence,
    translate_sequence
)

# Get genomic sequence
seq = get_sequence("17:43044295-43125483")  # BRCA1 locus
print(f"Sequence: {seq['seq'][:100]}...")

# Get coding sequence
cds = get_cds_sequence("ENST00000380152")
print(f"CDS length: {len(cds['seq'])} bp")

# Translate DNA to protein
result = translate_sequence("ATGGCCTAA")
print(f"Protein: {result['protein_sequence']}")

# Get sequence with masking
masked_seq = get_sequence("1:1000000-1001000", mask="soft")
print(f"Masked sequence length: {len(masked_seq['seq'])}")
```

### Comparative Genomics

```python
from biodsa.tools.ensembl import (
    get_homologs,
    compare_genes_across_species,
    get_gene_tree
)

# Find mouse ortholog
homologs = get_homologs("ENSG00000139618", target_species="mus_musculus")
print(f"Human: {homologs['source_gene']['symbol']}")
if 'ortholog' in homologs:
    print(f"Mouse: {homologs['ortholog']['symbol']}")

# Compare gene across multiple species
comparison = compare_genes_across_species(
    "TP53",
    ["homo_sapiens", "mus_musculus", "rattus_norvegicus"]
)
for species, data in comparison.items():
    if data['found']:
        print(f"{species}: {data['id']} at {data['location']}")

# Get gene tree
tree = get_gene_tree("ENSG00000139618")
print(f"Tree ID: {tree.get('id')}")
```

### Variant Analysis

```python
from biodsa.tools.ensembl import (
    get_variants,
    get_variant_info
)

# Get variants in a region
variants = get_variants("17:43044295-43045000")
print(f"Found {len(variants)} variants")
print(variants[['id', 'start', 'allele_string', 'consequence_type']])

# Get specific variant info
info = get_variant_info("rs699")
print(f"Variant: {info.get('name')}")
print(f"Location: {info.get('mappings')}")
```

### Assembly & Species Information

```python
from biodsa.tools.ensembl import (
    list_species,
    get_assembly_info,
    get_karyotype,
    get_xrefs
)

# List available species
species = list_species(division="vertebrates")
print(species[['name', 'display_name', 'assembly']].head())

# Get assembly information
assembly = get_assembly_info("homo_sapiens")
print(f"Assembly: {assembly['assembly_name']}")
print(f"Genome length: {assembly.get('total_genome_length'):,} bp")

# Get karyotype
karyotype = get_karyotype("homo_sapiens")
print(f"Chromosomes: {karyotype['karyotype']}")

# Get cross-references
xrefs = get_xrefs("ENSG00000139618")
print(xrefs[['dbname', 'display_id', 'description']].head())
```

### Batch Operations

```python
from biodsa.tools.ensembl import (
    batch_gene_lookup,
    batch_sequence_fetch
)

# Batch gene lookup
genes = batch_gene_lookup([
    "ENSG00000139618",  # BRCA2
    "ENSG00000141510",  # TP53
    "ENSG00000012048"   # BRCA1
])
for gene_id, gene_data in genes.items():
    print(f"{gene_id}: {gene_data.get('display_name')}")

# Batch sequence fetch
sequences = batch_sequence_fetch([
    "1:1000000-1001000",
    "2:2000000-2001000"
])
for result in sequences:
    if result['success']:
        print(f"{result['region']}: {len(result['data']['seq'])} bp")
```

## API Client

The base client for making API requests to Ensembl.

```python
from biodsa.tools.ensembl import EnsemblClient

client = EnsemblClient(base_url="https://rest.ensembl.org")

# Use client for custom requests
gene = client.lookup_gene("BRCA2")
sequence = client.get_sequence("1:1000000-1001000")
```

## Data Sources

- **Ensembl REST API**: https://rest.ensembl.org
- **Documentation**: https://rest.ensembl.org/documentation
- **Genome Browser**: https://www.ensembl.org

## Notes

- Default species is `homo_sapiens`. Specify other species using the `species` parameter.
- The Ensembl API has rate limits. Be respectful when making requests.
- Use batch operations when processing multiple items for better efficiency.
- Gene IDs are stable across releases, but genomic coordinates may change between assemblies.
- Some endpoints may return different data formats depending on the query.

## Common Species Names

- Human: `homo_sapiens`
- Mouse: `mus_musculus`
- Rat: `rattus_norvegicus`
- Zebrafish: `danio_rerio`
- Fruit fly: `drosophila_melanogaster`
- C. elegans: `caenorhabditis_elegans`

Use `list_species()` to see all available species.

## References

- Ensembl 2023. Nucleic Acids Research.
- Ensembl REST API: https://rest.ensembl.org

## License

This module is part of BioDSA and follows the same license terms.

