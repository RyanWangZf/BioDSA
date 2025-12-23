
# BioDSA Knowledge Graph Tools

This directory contains a comprehensive library of tools for querying and integrating biomedical knowledge graphs and databases. These tools enable agents to search, retrieve, and synthesize information from 17+ authoritative biomedical data sources.

## Architecture

Each knowledge graph integration follows a consistent two-layer architecture:

1. **Client Layer** (`client.py`): Low-level API wrapper handling authentication, rate limiting, error handling, and response parsing
2. **Tool Layer** (`*_tools.py`): High-level functions providing task-oriented interfaces that return pandas DataFrames with formatted output strings

This separation allows the same underlying API client to support multiple tool functions while maintaining clean abstractions.

## Available Knowledge Bases

| Knowledge Base | Directory | Description |
|----------------|-----------|-------------|
| BioThings | `biothings/` | Unified gene, drug, disease, and variant information |
| ChEMBL | `chembl/` | Chemical compounds, drug targets, and bioactivity data |
| ClinicalTrials.gov | `clinical_trials/` | Clinical trial registry and results |
| Ensembl | `ensembl/` | Genome annotation and comparative genomics |
| Gene Ontology | `gene_ontology/` | Gene function annotations and ontology |
| Human Phenotype Ontology | `hpo/` | Human phenotype terms and disease associations |
| KEGG | `kegg/` | Pathways, genes, compounds, and drug interactions |
| NCBI Datasets | `ncbi/` | Gene annotations, genomes, and taxonomy |
| OpenFDA | `openfda/` | FDA drug approvals and safety data |
| Open Genes | `opengenes/` | Aging-related genes and longevity research |
| Open Targets | `opentargets/` | Target-disease associations and drug evidence |
| ProteinAtlas | `proteinatlas/` | Protein expression across tissues and cells |
| PubChem | `pubchem/` | Chemical compounds, properties, and bioactivities |
| PubMed/PubTator | `pubmed/` | Literature search and biomedical entity extraction |
| Reactome | `reactome/` | Biological pathways and reactions |
| StringDB | `stringdb/` | Protein-protein interaction networks |
| UMLS | `umls/` | Unified medical language system concepts |
| UniProt | `uniprot/` | Protein sequences, functions, and annotations |

## Tool Reference

### BioThings (MyGene.info, MyChem.info, MyDisease.info, MyVariant.info)

| Tool | Description |
|------|-------------|
| `search_genes` | Search for genes by symbol, name, Entrez ID, or Ensembl ID |
| `fetch_gene_details_by_ids` | Fetch detailed gene information including aliases, pathways, and GO terms |
| `search_drugs` | Search for drugs by name, DrugBank ID, ChEBI ID, ChEMBL ID, or PubChem CID |
| `fetch_drug_details_by_ids` | Fetch detailed drug information including indications and pharmacology |
| `search_diseases` | Search for diseases by name, MONDO ID, DOID, OMIM ID, or MeSH ID |
| `fetch_disease_details_by_ids` | Fetch detailed disease information including phenotypes |
| `search_variants` | Search for genetic variants by rsID, gene, HGVS notation, or ClinVar significance |
| `fetch_variant_details_by_ids` | Fetch detailed variant annotations including clinical significance |

### ChEMBL

| Tool | Description |
|------|-------------|
| `search_compounds` | Search ChEMBL database for compounds by name or identifier |
| `get_compound_details` | Get detailed compound information including molecular properties |
| `search_similar_compounds` | Find chemically similar compounds using Tanimoto similarity |
| `search_substructure` | Find compounds containing a specific chemical substructure |
| `batch_compound_lookup` | Process multiple ChEMBL IDs efficiently in batch mode |
| `search_targets` | Search for biological targets by name, type, or organism |
| `get_target_details` | Get detailed target information including components and synonyms |
| `search_by_uniprot` | Find ChEMBL targets by UniProt accession number |
| `get_target_bioactivities` | Retrieve bioactivity measurements (IC50, Ki, EC50) for a target |
| `get_compounds_for_target` | Get active compounds for a target filtered by activity threshold |
| `get_drug_indications` | Search for therapeutic indications and disease areas |
| `get_drug_mechanisms` | Get mechanism of action and target interaction data |
| `get_drug_clinical_data` | Get comprehensive clinical and drug development data |
| `search_drugs_by_indication` | Search for drugs treating a specific indication |

### ClinicalTrials.gov

| Tool | Description |
|------|-------------|
| `search_trials` | Search clinical trials by condition, intervention, sponsor, phase, or status |
| `fetch_trial_details` | Fetch comprehensive trial information including eligibility and outcomes |

### Gene Ontology

| Tool | Description |
|------|-------------|
| `search_go_terms` | Search GO terms by name or keyword across all ontologies |
| `get_go_term_details` | Get detailed information for a GO term |
| `get_go_term_hierarchy` | Get hierarchical relationships for a GO term |
| `validate_go_id` | Validate a GO identifier format and existence |
| `get_ontology_statistics` | Get statistics about GO ontologies |
| `get_gene_annotations` | Get GO annotations for a specific gene |
| `get_term_annotations` | Get gene products annotated with a specific GO term |
| `get_evidence_codes` | Get list of GO evidence codes with descriptions |

### Human Phenotype Ontology (HPO)

| Tool | Description |
|------|-------------|
| `search_hpo_terms` | Search HPO terms by keyword, HPO ID, or synonym |
| `get_hpo_term_details` | Get detailed information for an HPO term |
| `get_term_genes` | Get genes associated with a specific HPO term |
| `get_term_diseases` | Get diseases associated with a specific HPO term |
| `get_gene_phenotypes` | Get phenotypes associated with a specific gene |

### KEGG

| Tool | Description |
|------|-------------|
| `search_pathways` | Search biological pathways by name or keyword |
| `get_pathway_info` | Get detailed pathway information including genes and compounds |
| `get_pathway_genes` | Get list of genes involved in a pathway |
| `get_pathway_compounds` | Get list of compounds involved in a pathway |
| `search_genes` | Search genes by symbol or description |
| `get_gene_info` | Get detailed gene information including pathways |
| `search_compounds` | Search chemical compounds |
| `get_compound_info` | Get detailed compound information |
| `search_diseases` | Search human diseases |
| `get_disease_info` | Get detailed disease information |
| `search_drugs` | Search approved drugs |
| `get_drug_info` | Get detailed drug information |
| `get_drug_interactions` | Retrieve drug-drug interaction information |
| `search_reactions` | Search biochemical reactions |
| `search_enzymes` | Search enzymes by EC number or name |
| `search_modules` | Search functional modules |
| `search_ko_entries` | Search KEGG Orthology entries |

### NCBI Datasets

| Tool | Description |
|------|-------------|
| `search_genes` | Search genes by symbol and taxonomy ID |
| `get_gene_info` | Fetch gene annotations, genomic locations, and orthologs |
| `search_genomes` | Search genome assemblies by organism or accession |
| `get_taxonomy_info` | Retrieve taxonomic classification and lineage |

### OpenFDA

| Tool | Description |
|------|-------------|
| `search_openfda_drugs` | Search FDA-approved drugs by brand name, generic name, or application number |
| `search_drug_labels` | Search drug labeling for indications, warnings, and dosage |

### Open Genes

| Tool | Description |
|------|-------------|
| `search_genes` | Search aging-related genes by symbol, mechanism, or disease |
| `get_gene_by_symbol` | Get detailed aging gene information including longevity evidence |
| `get_calorie_experiments` | Get caloric restriction experiment data |
| `get_aging_mechanisms` | Get list of aging mechanisms and associated genes |
| `get_protein_classes` | Get protein classes related to aging |
| `get_model_organisms` | Get model organisms used in aging research |

### Open Targets

| Tool | Description |
|------|-------------|
| `search_targets` | Search therapeutic targets by symbol, name, or description |
| `get_target_details` | Get comprehensive target information including tractability |
| `get_target_associated_diseases` | Get diseases associated with a target |
| `search_diseases` | Search diseases by name, synonym, or EFO ID |
| `get_disease_details` | Get comprehensive disease information |
| `get_disease_associated_targets` | Get targets associated with a disease |
| `get_disease_targets_summary` | Get summary of all targets for a disease |
| `search_drugs` | Search drugs by name or ChEMBL ID |
| `get_drug_details` | Get comprehensive drug information |
| `get_target_disease_evidence` | Get detailed evidence for target-disease pair |
| `analyze_association_evidence` | Analyze evidence types for associations |

### ProteinAtlas

| Tool | Description |
|------|-------------|
| `search_proteins` | Search proteins by gene name, symbol, or description |
| `get_protein_info` | Get detailed protein information including expression data |
| `batch_protein_lookup` | Look up multiple proteins by gene symbols |
| `get_tissue_expression` | Get tissue-specific expression levels |
| `get_blood_expression` | Get blood cell expression data |
| `get_brain_expression` | Get brain region expression data |
| `search_by_tissue` | Find proteins expressed in specific tissues |
| `get_subcellular_location` | Get subcellular localization annotations |
| `get_pathology_data` | Get cancer-related expression and survival data |
| `search_cancer_markers` | Search for cancer biomarker proteins |
| `get_antibody_info` | Get antibody validation information |

### PubChem

| Tool | Description |
|------|-------------|
| `search_compounds` | Search compounds by name, CAS, SMILES, InChI, or formula |
| `get_compound_info` | Get detailed compound information |
| `get_compound_properties` | Get molecular properties for compounds |
| `get_compound_synonyms` | Get all synonyms for a compound |
| `search_similar_compounds` | Find structurally similar compounds |
| `substructure_search` | Find compounds containing a substructure |
| `get_safety_data` | Get safety and hazard information |
| `get_toxicity_info` | Get toxicity information |
| `get_assay_info` | Get bioassay information |
| `get_compound_bioactivities` | Get bioactivity data across assays |
| `get_external_references` | Get cross-references to external databases |
| `assess_drug_likeness` | Assess drug-likeness using Lipinski rules |

### PubMed / PubTator

| Tool | Description |
|------|-------------|
| `search_papers` | Search PubMed articles with entity typing (@CHEMICAL, @DISEASE, @GENE) |
| `pubtator_api_fetch_paper_annotations` | Retrieve NER annotations for PubMed articles |
| `pubtator_api_find_entities` | Discover biomedical entities with autocomplete |
| `pubtator_api_find_related_entities` | Find entities related through semantic predicates |
| `pubmed_api_search_papers` | Search PubMed using E-utilities |
| `pubmed_api_get_paper_references` | Retrieve citation relationships |
| `fetch_paper_content_by_pmid` | Fetch full-text content via PubMed Central |
| `get_pubmed_articles` | Get article metadata |
| `extract_relevant_sections` | Extract sections matching a pattern |

### Reactome

| Tool | Description |
|------|-------------|
| `search_pathways` | Search biological pathways by name or identifier |
| `get_pathway_details` | Get detailed pathway information |
| `get_pathway_hierarchy` | Get parent and child pathways |
| `get_pathway_reactions` | Get reactions in a pathway |
| `get_pathway_participants` | Get molecules participating in a pathway |
| `find_pathways_by_gene` | Find pathways containing a gene |
| `get_gene_pathways_dataframe` | Get pathways for a gene as DataFrame |
| `get_protein_interactions` | Retrieve protein-protein interactions |
| `find_pathways_by_disease` | Find pathways associated with a disease |

### UMLS

| Tool | Description |
|------|-------------|
| `search_concepts` | Search UMLS Metathesaurus concepts |
| `get_cui_info` | Retrieve concept definitions and semantic types |
| `get_atoms` | Get atoms from source vocabularies |
| `get_definitions` | Get definitions from various sources |
| `get_relations` | Retrieve semantic relationships |
| `get_crosswalk` | Map identifiers across vocabularies (ICD, SNOMED, MeSH, RxNorm) |
| `get_semantic_type` | Get semantic type information |
| `get_source_concept` | Get concept from a specific vocabulary |

### UniProt

| Tool | Description |
|------|-------------|
| `search_proteins` | Search protein database by name, gene, organism, or function |
| `get_protein_info` | Retrieve comprehensive protein information |
| `search_by_gene` | Search proteins by gene name |
| `get_protein_sequence` | Get protein sequence in FASTA format |
| `get_protein_features` | Get protein features (domains, active sites, PTMs) |
| `get_protein_structure` | Get structural information and domain annotations |
| `get_protein_variants` | Get natural and disease-associated variants |
| `get_protein_pathways` | Get pathway associations |
| `get_protein_interactions` | Retrieve protein-protein interaction data |
| `get_protein_homologs` | Find homologous proteins across species |
| `get_protein_orthologs` | Find orthologous proteins |
| `search_by_function` | Search proteins by molecular function |
| `search_by_localization` | Search proteins by subcellular localization |
| `search_by_taxonomy` | Search proteins by taxonomic classification |
| `batch_protein_lookup` | Process multiple UniProt accessions |
| `get_literature_references` | Get literature references |
| `get_external_references` | Get cross-references to external databases |

### Unified (Multi-source) Tools

These tools aggregate results from multiple knowledge bases for comprehensive searches:

| Tool | Description |
|------|-------------|
| `search_genes_unified` | Search genes across BioThings, KEGG, and Open Targets |
| `fetch_gene_details_unified` | Fetch gene details from multiple sources |
| `search_drugs_unified` | Search drugs across BioThings, OpenFDA, KEGG, Open Targets, and ChEMBL |
| `fetch_drug_details_unified` | Fetch drug details aggregated from multiple sources |
| `search_targets_unified` | Search therapeutic targets across multiple databases |
| `fetch_target_details_unified` | Fetch target information with cross-database identifiers |
| `search_pathways_unified` | Search pathways across KEGG, Reactome, and others |
| `fetch_pathway_details_unified` | Fetch pathway information from multiple sources |
| `search_compounds_unified` | Search compounds across PubChem, ChEMBL, and KEGG |
| `fetch_compound_details_unified` | Fetch compound information from multiple databases |

## Usage Example

```python
from biodsa.tools.chembl.compound_tools import search_compounds, get_compound_details
from biodsa.tools.pubmed.pubmed_api import pubmed_api_search_papers

# Search for a compound
results_df, results_str = search_compounds("ibuprofen")
print(results_str)

# Get detailed compound information
details_df, details_str = get_compound_details("CHEMBL521")
print(details_str)

# Search PubMed for related literature
papers_df, papers_str = pubmed_api_search_papers("ibuprofen mechanism of action", max_results=10)
print(papers_str)
```

## Adding New Tools

To add a new knowledge graph integration:

1. Create a new directory under `biodsa/tools/` (e.g., `biodsa/tools/new_database/`)
2. Implement `client.py` with the API wrapper class
3. Implement `*_tools.py` with high-level tool functions
4. Each tool function should return `Tuple[pd.DataFrame, str]` for structured data and formatted output
5. Add the new tools to the tool registry for agent access

## References

For detailed citations of the knowledge bases, see the main [README.md](../../README.md).
