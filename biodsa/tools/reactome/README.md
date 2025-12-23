# Reactome API Tools

Python client and tools for the Reactome Content Service API, providing programmatic access to curated biological pathway data.

## Overview

Reactome is a free, open-source, curated database of pathways and reactions in human biology. The Reactome API provides access to:
- **Biological Pathways**: Curated pathway information across multiple organisms
- **Biochemical Reactions**: Detailed reaction mechanisms and catalysis
- **Protein Interactions**: Molecular interactions within pathways
- **Disease Pathways**: Disease-associated molecular mechanisms
- **Gene/Protein Associations**: Pathway membership and participation

API Documentation: https://reactome.org/ContentService/

## Installation

The Reactome tools are part of the BioDSA toolkit:

```bash
pip install requests pandas
```

## Quick Start

### Search for Pathways

```python
from biodsa.tools.reactome import search_pathways

# Search for apoptosis pathways
pathways = search_pathways('apoptosis', size=10)
print(pathways[['id', 'name', 'species']])
```

### Get Pathway Details

```python
from biodsa.tools.reactome import get_pathway_details

# Get details for a specific pathway
details = get_pathway_details('R-HSA-109581')
print(f"Pathway: {details['basicInfo']['displayName']}")
```

### Find Pathways by Gene

```python
from biodsa.tools.reactome import find_pathways_by_gene

# Find pathways containing TP53
result = find_pathways_by_gene('TP53')
print(f"Found {result['pathwayCount']} pathways")

# Convert to DataFrame
import pandas as pd
pathways_df = pd.DataFrame(result['pathways'])
print(pathways_df[['id', 'name']].head())
```

### Find Disease-Associated Pathways

```python
from biodsa.tools.reactome import find_pathways_by_disease

# Find cancer-related pathways
cancer_pathways = find_pathways_by_disease('cancer', size=20)
print(cancer_pathways[['id', 'name', 'description']].head())
```

## Available Functions

### Pathway Operations

- `search_pathways(query, entity_type, size)`
  - Search for pathways, reactions, proteins, or complexes
  
- `get_pathway_details(pathway_id)`
  - Get comprehensive pathway information
  
- `get_pathway_hierarchy(pathway_id)`
  - Get parent/child relationships and pathway structure
  
- `get_pathway_reactions(pathway_id)`
  - Get all biochemical reactions in a pathway
  
- `get_pathway_participants(pathway_id, max_results)`
  - Get all molecules participating in a pathway

### Gene/Protein Operations

- `find_pathways_by_gene(gene, species)`
  - Find pathways containing a specific gene or protein
  
- `get_gene_pathways_dataframe(gene, species)`
  - Find gene pathways and return as DataFrame
  
- `get_protein_interactions(pathway_id, interaction_type)`
  - Get protein-protein interactions within pathways

### Disease Operations

- `find_pathways_by_disease(disease, size)`
  - Find disease-associated pathways

## Common Use Cases

### 1. Explore Pathways for a Gene of Interest

```python
from biodsa.tools.reactome import find_pathways_by_gene, get_pathway_details

# Find pathways for BRCA1
result = find_pathways_by_gene('BRCA1')
print(f"BRCA1 participates in {result['pathwayCount']} pathways")

# Get details for the first pathway
if result['pathways']:
    pathway_id = result['pathways'][0]['id']
    details = get_pathway_details(pathway_id)
    print(f"\nPathway: {details['basicInfo']['displayName']}")
```

### 2. Find Interactions in a Pathway

```python
from biodsa.tools.reactome import search_pathways, get_protein_interactions

# Search for DNA repair pathways
pathways = search_pathways('DNA repair', entity_type='pathway', size=5)

# Get interactions in the first pathway
if len(pathways) > 0:
    pathway_id = pathways.iloc[0]['id']
    interactions = get_protein_interactions(pathway_id)
    print(f"Found {interactions['proteinCount']} proteins")
    print(f"Found {interactions['reactionCount']} reactions")
```

### 3. Analyze Disease Mechanisms

```python
from biodsa.tools.reactome import find_pathways_by_disease, get_pathway_participants

# Find Alzheimer's disease pathways
ad_pathways = find_pathways_by_disease("Alzheimer's disease", size=10)
print(f"Found {len(ad_pathways)} Alzheimer's-related pathways")

# Get participants in the first pathway
if len(ad_pathways) > 0:
    pathway_id = ad_pathways.iloc[0]['id']
    participants = get_pathway_participants(pathway_id, max_results=20)
    print(f"\nKey molecules in {ad_pathways.iloc[0]['name']}:")
    print(participants[['name', 'type']].head())
```

### 4. Compare Pathways Across Species

```python
from biodsa.tools.reactome import find_pathways_by_gene

# Find TP53 pathways in human
human_result = find_pathways_by_gene('TP53', species='Homo sapiens')
print(f"Human TP53: {human_result['pathwayCount']} pathways")

# Find Trp53 pathways in mouse
mouse_result = find_pathways_by_gene('Trp53', species='Mus musculus')
print(f"Mouse Trp53: {mouse_result['pathwayCount']} pathways")
```

### 5. Get Complete Pathway Information

```python
from biodsa.tools.reactome import (
    get_pathway_details,
    get_pathway_reactions,
    get_pathway_participants,
    get_pathway_hierarchy
)

pathway_id = 'R-HSA-109581'

# Get all pathway information
details = get_pathway_details(pathway_id)
reactions = get_pathway_reactions(pathway_id)
participants = get_pathway_participants(pathway_id)
hierarchy = get_pathway_hierarchy(pathway_id)

print(f"Pathway: {details['basicInfo']['displayName']}")
print(f"Reactions: {len(reactions)}")
print(f"Participants: {len(participants)}")
print(f"Child pathways: {len(hierarchy.get('children', []))}")
```

## Data Models

### Entity Types

- `pathway`: Biological pathways
- `reaction`: Biochemical reactions
- `protein`: Protein entities
- `complex`: Protein complexes
- `disease`: Disease entities

### Interaction Types

- `protein-protein`: Direct protein-protein interactions
- `regulatory`: Regulatory interactions
- `catalysis`: Catalytic reactions
- `all`: All interaction types

### Species

Common species in Reactome:
- `Homo sapiens` (Human)
- `Mus musculus` (Mouse)
- `Rattus norvegicus` (Rat)
- `Saccharomyces cerevisiae` (Yeast)
- `Caenorhabditis elegans` (C. elegans)
- `Drosophila melanogaster` (Fruit fly)

## Pathway Identifiers

Reactome uses stable identifiers in the format: `R-XXX-#######`

Examples:
- `R-HSA-109581` (Apoptosis, human)
- `R-MMU-109581` (Apoptosis, mouse)
- `R-RNO-109581` (Apoptosis, rat)

Where:
- `R` = Reactome
- `HSA` = Homo sapiens, `MMU` = Mus musculus, etc.
- Numbers = Unique pathway identifier

## Error Handling

```python
from biodsa.tools.reactome import get_pathway_details

try:
    details = get_pathway_details('R-HSA-999999')  # Invalid ID
except Exception as e:
    print(f"Error: {e}")
```

## API Performance

**Important Note**: The Reactome Content Service API can be slow, especially for:
- Complex search queries (e.g., searching for "cancer")
- Proteins that participate in many pathways (e.g., TP53, BRCA1)
- Large pathway queries

Typical response times:
- Simple searches: 5-15 seconds
- Gene-pathway lookups: 10-30 seconds
- Complex queries: 15-60 seconds

The client is configured with a 45-second default timeout. You may need to increase this for complex queries:

```python
from biodsa.tools.reactome import ReactomeClient

# Increase timeout for complex queries
client = ReactomeClient(timeout=90)
```

## Rate Limits

The Reactome API does not have strict rate limits, but please be respectful:
- Implement reasonable delays between requests for bulk operations
- Cache results when possible
- Use batch operations when available
- Be patient with slow responses - this is normal for the Reactome API

## Client Configuration

```python
from biodsa.tools.reactome import ReactomeClient

# Custom configuration
client = ReactomeClient(
    base_url="https://reactome.org/ContentService",
    timeout=60  # seconds
)

# Use with high-level functions
from biodsa.tools.reactome import search_pathways

pathways = search_pathways('apoptosis', client=client)
```

## Data Visualization

Reactome provides pathway diagrams through their PathwayBrowser:

```python
from biodsa.tools.reactome import get_pathway_details

details = get_pathway_details('R-HSA-109581')
print(f"View pathway diagram: {details['diagramUrl']}")
# Opens: https://reactome.org/PathwayBrowser/#R-HSA-109581
```

## References

- Reactome Website: https://reactome.org/
- Reactome API Documentation: https://reactome.org/ContentService/
- Reactome Publications: https://reactome.org/about/publications

### Citing Reactome

If you use Reactome in your research, please cite:
- Gillespie M, et al. The reactome pathway knowledgebase 2022. Nucleic Acids Res. 2022

## Support

For issues related to the Reactome API itself, please refer to:
- Reactome Help: https://reactome.org/help

For issues with this Python client:
- Open an issue in the BioDSA repository

## Additional Features

### Pathway Analysis

Reactome provides pathway analysis tools through their web interface. For programmatic analysis, consider:
- Over-representation analysis
- Gene set enrichment analysis
- Pathway-based data visualization

Visit https://reactome.org/PathwayBrowser/ for interactive analysis tools.

### Data Downloads

For bulk data access, Reactome provides downloadable databases:
- https://reactome.org/download-data

These can be useful for:
- Local pathway databases
- Custom analysis pipelines
- Large-scale data integration

