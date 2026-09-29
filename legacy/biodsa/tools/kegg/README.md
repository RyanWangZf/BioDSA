# KEGG REST API Client

A comprehensive Python client for interacting with the KEGG (Kyoto Encyclopedia of Genes and Genomes) REST API.

## Overview

This client provides easy access to the KEGG database, which is a comprehensive database resource for understanding high-level functions and utilities of biological systems from molecular-level information.

## Features

The client implements **33 tools** covering all major KEGG databases:

### Database Information & Statistics
- `get_database_info()` - Get release information and statistics for any KEGG database
- `list_organisms()` - Get all KEGG organisms with codes and names

### Pathway Analysis
- `search_pathways()` - Search pathways by keywords or pathway names
- `get_pathway_info()` - Get detailed information for a specific pathway
- `get_pathway_genes()` - Get all genes involved in a specific pathway
- `get_pathway_compounds()` - Get all compounds involved in a specific pathway
- `get_pathway_reactions()` - Get all reactions involved in a specific pathway

### Gene Analysis
- `search_genes()` - Search genes by name, symbol, or keywords
- `get_gene_info()` - Get detailed information for a specific gene
- `get_gene_orthologs()` - Find orthologous genes across organisms

### Compound Analysis
- `search_compounds()` - Search compounds by name, formula, or chemical structure
- `get_compound_info()` - Get detailed information for a specific compound
- `get_compound_reactions()` - Get all reactions involving a specific compound

### Reaction & Enzyme Analysis
- `search_reactions()` - Search biochemical reactions by keywords
- `get_reaction_info()` - Get detailed information for a specific reaction
- `search_enzymes()` - Search enzymes by EC number or enzyme name
- `get_enzyme_info()` - Get detailed enzyme information by EC number

### Disease & Drug Analysis
- `search_diseases()` - Search human diseases by name or keywords
- `get_disease_info()` - Get detailed information for a specific disease
- `search_drugs()` - Search drugs by name, target, or indication
- `get_drug_info()` - Get detailed information for a specific drug
- `get_drug_interactions()` - Find adverse drug-drug interactions

### Module & Orthology Analysis
- `search_modules()` - Search KEGG modules by name or function
- `get_module_info()` - Get detailed information for a specific module
- `search_ko_entries()` - Search KEGG Orthology entries
- `get_ko_info()` - Get detailed information for a specific KO entry

### Glycan Analysis
- `search_glycans()` - Search glycan structures by name or composition
- `get_glycan_info()` - Get detailed information for a specific glycan

### BRITE Hierarchy Analysis
- `search_brite()` - Search BRITE functional hierarchies
- `get_brite_info()` - Get detailed information for a specific BRITE entry

### Advanced Tools
- `batch_entry_lookup()` - Process multiple KEGG entries efficiently
- `convert_identifiers()` - Convert between KEGG and external database identifiers
- `find_related_entries()` - Find related entries across KEGG databases

## Installation

The client requires the `requests` library:

```bash
pip install requests
```

## Usage

### Basic Usage

```python
from biodsa.tools.kegg import KEGGClient

# Initialize the client
client = KEGGClient()

# Search for pathways
pathways = client.search_pathways("glycolysis", max_results=10)
for pathway in pathways:
    print(f"{pathway['id']}: {pathway['description']}")

# Get detailed pathway information
pathway_info = client.get_pathway_info("hsa00010")
print(pathway_info)
```

### Using Context Manager

```python
from biodsa.tools.kegg import KEGGClient

with KEGGClient() as client:
    # Search genes
    genes = client.search_genes("BRCA1", organism_code="hsa")
    
    # Get gene details
    if genes:
        gene_info = client.get_gene_info(genes[0]['id'])
        print(gene_info)
```

### Examples by Category

#### 1. Pathway Analysis

```python
# Search pathways
pathways = client.search_pathways("cancer", organism_code="hsa", max_results=5)

# Get pathway info in different formats
pathway_json = client.get_pathway_info("hsa05200", format="json")
pathway_kgml = client.get_pathway_info("hsa05200", format="kgml")
pathway_image_url = client.get_pathway_info("hsa05200", format="image")

# Get pathway components
genes = client.get_pathway_genes("hsa00010")
compounds = client.get_pathway_compounds("hsa00010")
reactions = client.get_pathway_reactions("rn00010")
```

#### 2. Gene Analysis

```python
# Search genes
genes = client.search_genes("insulin receptor", organism_code="hsa", max_results=10)

# Get gene information with sequences
gene_info = client.get_gene_info("hsa:3643", include_sequences=True)

# Find orthologs
orthologs = client.get_gene_orthologs("hsa:3643", target_organisms=["mmu", "rno"])
```

#### 3. Compound and Reaction Analysis

```python
# Search compounds by name
compounds = client.search_compounds("glucose", max_results=10)

# Search by molecular formula
compounds = client.search_compounds("C6H12O6", search_type="formula", max_results=10)

# Get compound information
compound_info = client.get_compound_info("C00031")

# Get reactions involving a compound
reactions = client.get_compound_reactions("C00031")
```

#### 4. Disease and Drug Analysis

```python
# Search diseases
diseases = client.search_diseases("breast cancer", max_results=10)

# Get disease details
disease_info = client.get_disease_info("H00031")

# Search drugs
drugs = client.search_drugs("metformin", max_results=10)

# Get drug information with enhanced parsing
drug_info = client.get_drug_info("D00944")
# Returns dict with additional parsed fields:
# - target_gene_ids: ['hsa:5142', 'hsa:7068', ...]
# - target_ko_ids: ['K13293', 'K08362', ...]
# - pathways: [('path:hsa04024', 'cAMP signaling pathway'), ...] (from TARGET field)
# - metabolism: ['Enzyme: CYP3A [HSA:1576 1577 1551]; UGT [KO:K00699]']
# - metabolism_enzymes: [{'enzyme': 'CYP3A', 'hsa_ids': ['hsa:1576', ...], 'ko_ids': []}, ...]
# - disease: ['Type 2 diabetes', ...]
# - efficacy: ['Antidiabetic', ...]

print(f"Target genes: {drug_info['target_gene_ids']}")
print(f"Pathways: {drug_info['pathways']}")
print(f"Metabolism: {drug_info['metabolism']}")
print(f"Metabolism enzymes: {drug_info['metabolism_enzymes']}")

# Check drug interactions
interactions = client.get_drug_interactions(["D00944", "D00123"])
```

#### 5. Enzyme Analysis

```python
# Search enzymes
enzymes = client.search_enzymes("hexokinase", max_results=10)

# Get enzyme information by EC number
enzyme_info = client.get_enzyme_info("2.7.1.1")
```

#### 6. Module and Orthology

```python
# Search modules
modules = client.search_modules("citrate cycle", max_results=10)

# Get module information
module_info = client.get_module_info("M00009")

# Search KO entries
ko_entries = client.search_ko_entries("hexokinase", max_results=10)

# Get KO information
ko_info = client.get_ko_info("K00844")
```

#### 7. Advanced Tools

```python
# Batch lookup
gene_ids = ["hsa:3643", "hsa:3630", "hsa:5468"]
results = client.batch_entry_lookup(gene_ids, operation='info')

# Convert identifiers
conversions = client.convert_identifiers(
    source_db="ncbi-geneid",
    target_db="hsa",
    identifiers=["3643", "5468"]
)

# Find related entries
related = client.find_related_entries(
    source_db="pathway",
    target_db="compound",
    source_entries=["hsa00010"]
)
```

## API Reference

### KEGGClient

#### Constructor

```python
KEGGClient(timeout: int = 30)
```

**Parameters:**
- `timeout`: Request timeout in seconds (default: 30)

#### Methods

All methods are documented with detailed docstrings in the source code. Use `help(KEGGClient.method_name)` to view documentation for any method.

## Error Handling

The client raises `requests.HTTPError` for failed API requests. It's recommended to wrap API calls in try-except blocks:

```python
try:
    pathway_info = client.get_pathway_info("invalid_id")
except requests.HTTPError as e:
    print(f"Error: {e}")
```

## KEGG Database Identifiers

### Common Organism Codes
- `hsa` - Homo sapiens (human)
- `mmu` - Mus musculus (mouse)
- `rno` - Rattus norvegicus (rat)
- `dme` - Drosophila melanogaster (fruit fly)
- `eco` - Escherichia coli K-12 MG1655

### Entry ID Formats
- Pathways: `map00010`, `hsa00010` (map = reference pathway, hsa = human)
- Genes: `hsa:3643`, `mmu:11651` (organism:gene_id)
- Compounds: `C00031`, `C00002`
- Reactions: `R00001`, `R00002`
- Enzymes: `ec:1.1.1.1` or `1.1.1.1`
- Diseases: `H00001`, `H00031`
- Drugs: `D00001`, `D00944`
- Modules: `M00001`, `M00009`
- KO: `K00001`, `K00844`
- Glycans: `G00001`, `G00002`

## Resources

- [KEGG Website](https://www.kegg.jp/)
- [KEGG REST API Documentation](https://www.kegg.jp/kegg/rest/keggapi.html)
- [KEGG Database Overview](https://www.kegg.jp/kegg/kegg1.html)

## License

This client is part of the BioDSA project. Please refer to the main project license.

