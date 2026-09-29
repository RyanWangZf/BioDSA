# NCBI Datasets API Tools

Python client and tools for the NCBI Datasets API, providing programmatic access to genome, gene, taxonomy, and assembly data from NCBI.

## Overview

The NCBI Datasets API provides comprehensive access to:
- **Genome assemblies**: Complete and draft genomes with annotations
- **Gene information**: Gene symbols, descriptions, sequences, and genomic locations
- **Taxonomic data**: Organism classification and lineage information
- **Assembly metadata**: Quality metrics, statistics, and download links

API Documentation: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/api/

## Installation

The NCBI tools are part of the BioDSA toolkit:

```bash
pip install requests pandas
```

## Authentication

The NCBI Datasets API supports optional API keys for higher rate limits. Set your API key as an environment variable:

```bash
export NCBI_API_KEY="your_api_key_here"
```

Or pass it directly to the client:

```python
from biodsa.tools.ncbi import NCBIDatasetsClient

client = NCBIDatasetsClient(api_key="your_api_key_here")
```

## Quick Start

### Search Genomes

```python
from biodsa.tools.ncbi import search_genomes

# Search human genomes (tax_id=9606)
genomes = search_genomes(tax_id=9606, assembly_level='complete', max_results=10)
print(genomes[['accession', 'assembly_name', 'organism_name']])
```

### Get Gene Information

```python
from biodsa.tools.ncbi import search_genes, get_gene_info

# Search for TP53 gene in humans
genes = search_genes(gene_symbol='TP53', organism='Homo sapiens')
print(genes[['gene_id', 'symbol', 'description', 'chromosome']])

# Get detailed information
gene_info = get_gene_info(gene_id=7157)
print(f"Gene: {gene_info['symbol']} - {gene_info['description']}")
```

### Taxonomy Information

```python
from biodsa.tools.ncbi import search_taxonomy, get_taxonomy_info

# Search for organism
taxonomy = search_taxonomy('Homo sapiens')
print(taxonomy[['tax_id', 'organism_name', 'rank']])

# Get detailed taxonomy
tax_info = get_taxonomy_info(tax_id=9606, include_lineage=True)
print(f"Organism: {tax_info['organism_name']}")
print(f"Lineage: {tax_info.get('lineage', [])}")
```

### Assembly Information

```python
from biodsa.tools.ncbi import search_assemblies, get_assembly_info

# Search assemblies
assemblies = search_assemblies(tax_id=9606, assembly_level='complete')
print(assemblies[['assembly_accession', 'assembly_name']])

# Get assembly details
assembly_info = get_assembly_info('GCF_000001405.40')
print(assembly_info)
```

## Available Functions

### Genome Operations

- `search_genomes(tax_id, assembly_level, assembly_source, max_results, page_token)`
  - Search genome assemblies by taxonomy ID
  
- `get_genome_info(accession, include_annotation)`
  - Get detailed information for a specific genome
  
- `get_genome_summary(accession)`
  - Get summary statistics for a genome
  
- `download_genome_data(accession, include_annotation, file_format)`
  - Get download URLs for genome data files

### Gene Operations

- `search_genes(gene_symbol, gene_id, organism, tax_id, chromosome, max_results, page_token)`
  - Search genes by various criteria
  
- `get_gene_info(gene_id, include_sequences)`
  - Get detailed information for a specific gene
  
- `get_gene_sequences(gene_id, sequence_type)`
  - Retrieve sequences for a specific gene

### Taxonomy Operations

- `search_taxonomy(query, rank, max_results)`
  - Search taxonomic information
  
- `get_taxonomy_info(tax_id, include_lineage)`
  - Get detailed taxonomic information
  
- `get_organism_info(organism, tax_id)`
  - Get organism information and available datasets
  
- `get_taxonomic_lineage(tax_id, include_ranks, include_synonyms, format)`
  - Get complete taxonomic lineage

### Assembly Operations

- `search_assemblies(query, assembly_level, assembly_source, tax_id, exclude_atypical, max_results, page_token)`
  - Search genome assemblies with filtering
  
- `get_assembly_info(assembly_accession, include_annotation)`
  - Get detailed assembly metadata
  
- `get_assembly_reports(assembly_accession, report_type)`
  - Get assembly quality reports
  
- `get_assembly_quality(accession)`
  - Get quality metrics for an assembly
  
- `batch_assembly_info(accessions, include_annotation)`
  - Get information for multiple assemblies

## Common Use Cases

### 1. Find Reference Genome for an Organism

```python
from biodsa.tools.ncbi import search_taxonomy, search_genomes

# Find organism taxonomy ID
taxonomy = search_taxonomy('Arabidopsis thaliana')
tax_id = taxonomy.iloc[0]['tax_id']

# Get reference genome
genomes = search_genomes(
    tax_id=tax_id,
    assembly_level='complete',
    assembly_source='refseq',
    max_results=1
)
print(f"Reference genome: {genomes.iloc[0]['accession']}")
```

### 2. Compare Gene Locations Across Species

```python
from biodsa.tools.ncbi import search_genes

# Search for orthologous genes
human_brca1 = search_genes(gene_symbol='BRCA1', tax_id=9606)
mouse_brca1 = search_genes(gene_symbol='Brca1', tax_id=10090)

print("Human BRCA1:")
print(human_brca1[['gene_id', 'chromosome', 'start', 'end']])

print("\nMouse Brca1:")
print(mouse_brca1[['gene_id', 'chromosome', 'start', 'end']])
```

### 3. Batch Download Assembly Information

```python
from biodsa.tools.ncbi import batch_assembly_info

accessions = [
    'GCF_000001405.40',  # Human
    'GCF_000001635.27',  # Mouse
    'GCF_000001735.4',   # Arabidopsis
]

batch_info = batch_assembly_info(accessions, include_annotation=True)
print(batch_info[['assembly_accession', 'organism_name', 'total_sequence_length']])
```

### 4. Get Complete Taxonomic Classification

```python
from biodsa.tools.ncbi import get_taxonomic_lineage

# Get lineage for Homo sapiens
lineage = get_taxonomic_lineage(tax_id=9606, include_ranks=True)
print(f"Taxonomic lineage: {lineage}")
```

## Data Models

### Genome Assembly Levels

- `complete`: Complete genome assembly
- `chromosome`: Chromosome-level assembly
- `scaffold`: Scaffold-level assembly
- `contig`: Contig-level assembly

### Assembly Sources

- `refseq`: RefSeq assemblies (curated reference sequences)
- `genbank`: GenBank assemblies
- `all`: Both RefSeq and GenBank

### Sequence Types

- `genomic`: Genomic DNA sequences
- `transcript`: mRNA/transcript sequences
- `protein`: Protein sequences
- `all`: All available sequence types

### File Formats

- `fasta`: FASTA sequence format
- `genbank`: GenBank flat file format
- `gff3`: GFF3 annotation format
- `gtf`: GTF annotation format
- `all`: All available formats

## Error Handling

```python
from biodsa.tools.ncbi import get_gene_info

try:
    gene_info = get_gene_info(gene_id=9999999)  # Invalid ID
except Exception as e:
    print(f"Error: {e}")
```

## Rate Limits

- Without API key: ~3 requests per second
- With API key: ~10 requests per second

## Client Configuration

```python
from biodsa.tools.ncbi import NCBIDatasetsClient

# Custom configuration
client = NCBIDatasetsClient(
    base_url="https://api.ncbi.nlm.nih.gov/datasets/v2alpha",
    api_key="your_api_key",
    timeout=60  # seconds
)

# Use with high-level functions
from biodsa.tools.ncbi import search_genes

genes = search_genes(gene_symbol='TP53', client=client)
```

## References

- NCBI Datasets: https://www.ncbi.nlm.nih.gov/datasets/
- API Documentation: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/api/
- RefSeq: https://www.ncbi.nlm.nih.gov/refseq/

## Support

For issues related to the NCBI Datasets API itself, please refer to:
- NCBI Help: https://support.ncbi.nlm.nih.gov/

For issues with this Python client:
- Open an issue in the BioDSA repository

