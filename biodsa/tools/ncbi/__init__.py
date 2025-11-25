"""
NCBI Datasets API Tools

This module provides access to NCBI Datasets API for genomic, genetic, and taxonomic data.
"""

from biodsa.tools.ncbi.client import NCBIDatasetsClient
from biodsa.tools.ncbi.genome_tools import (
    search_genomes,
    get_genome_info,
    get_genome_summary,
    download_genome_data,
)
from biodsa.tools.ncbi.gene_tools import (
    search_genes,
    get_gene_info,
    get_gene_sequences,
)
from biodsa.tools.ncbi.taxonomy_tools import (
    search_taxonomy,
    get_taxonomy_info,
    get_organism_info,
    get_taxonomic_lineage,
)
from biodsa.tools.ncbi.assembly_tools import (
    search_assemblies,
    get_assembly_info,
    get_assembly_reports,
    get_assembly_quality,
    batch_assembly_info,
)

__all__ = [
    # Client
    'NCBIDatasetsClient',
    # Genome operations
    'search_genomes',
    'get_genome_info',
    'get_genome_summary',
    'download_genome_data',
    # Gene operations
    'search_genes',
    'get_gene_info',
    'get_gene_sequences',
    # Taxonomy operations
    'search_taxonomy',
    'get_taxonomy_info',
    'get_organism_info',
    'get_taxonomic_lineage',
    # Assembly operations
    'search_assemblies',
    'get_assembly_info',
    'get_assembly_reports',
    'get_assembly_quality',
    'batch_assembly_info',
]

