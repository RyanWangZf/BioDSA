"""
Test suite for NCBI Datasets API tools.
"""

import sys
import unittest
from biodsa.tools.ncbi import (
    NCBIDatasetsClient,
    search_genomes,
    get_genome_info,
    get_genome_summary,
    search_genes,
    get_gene_info,
    search_taxonomy,
    get_taxonomy_info,
    get_organism_info,
    search_assemblies,
    get_assembly_info,
)


class TestNCBIDatasetsClient(unittest.TestCase):
    """Test NCBI Datasets API client."""
    
    def setUp(self):
        """Set up test client."""
        self.client = NCBIDatasetsClient()
    
    def test_client_initialization(self):
        """Test client initialization."""
        self.assertIsNotNone(self.client)
        self.assertEqual(self.client.base_url, "https://api.ncbi.nlm.nih.gov/datasets/v2alpha")
    
    def test_search_genomes(self):
        """Test genome search."""
        print("\nTesting genome search...")
        # Search for E. coli genomes (tax_id=562)
        result = search_genomes(tax_id=562, max_results=5)
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
        print(f"Found {len(result)} E. coli genomes")
        print(result[['accession', 'organism_name', 'assembly_name']].head())
    
    def test_get_genome_info(self):
        """Test getting genome information."""
        print("\nTesting get genome info...")
        # Get info for E. coli K-12 MG1655
        accession = "GCF_000005845.2"
        result = get_genome_info(accession)
        self.assertIsNotNone(result)
        print(f"Retrieved info for {accession}")
    
    def test_search_genes(self):
        """Test gene search."""
        print("\nTesting gene search...")
        # Search for TP53 gene in humans (tax_id=9606)
        result = search_genes(gene_symbol='TP53', tax_id=9606)
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
        print(f"Found {len(result)} TP53 gene(s)")
        print(result[['gene_id', 'symbol', 'organism_name', 'description']].head())
    
    def test_get_gene_info(self):
        """Test getting gene information."""
        print("\nTesting get gene info...")
        # Get info for human TP53 (gene_id=7157)
        result = get_gene_info(gene_id=7157)
        self.assertIsNotNone(result)
        # Extract gene from reports
        if 'reports' in result and len(result['reports']) > 0:
            gene = result['reports'][0].get('gene', {})
            self.assertEqual(gene.get('symbol'), 'TP53')
            print(f"Gene: {gene.get('symbol')} - {gene.get('description')}")
        else:
            self.fail("No gene reports found in response")
    
    def test_search_taxonomy(self):
        """Test taxonomy search."""
        print("\nTesting taxonomy search (using known tax_id)...")
        # v2alpha requires tax_id, so test with known human tax_id
        result = search_taxonomy('9606')  # Homo sapiens
        self.assertIsNotNone(result)
        print(f"Retrieved taxonomy info for tax_id 9606")
        if hasattr(result, 'shape'):
            print(result[['tax_id', 'organism_name']].head() if 'tax_id' in result.columns else result.head())
    
    def test_get_taxonomy_info(self):
        """Test getting taxonomy information."""
        print("\nTesting get taxonomy info...")
        # Get info for Homo sapiens (tax_id=9606)
        result = get_taxonomy_info(tax_id=9606)
        self.assertIsNotNone(result)
        # Extract organism info from the genome reports
        if 'reports' in result and len(result['reports']) > 0:
            organism = result['reports'][0].get('organism', {})
            print(f"Organism: {organism.get('organism_name')}")
            self.assertEqual(organism.get('tax_id'), 9606)
        else:
            print(f"Result keys: {result.keys()}")
    
    def test_get_organism_info(self):
        """Test getting organism information."""
        print("\nTesting get organism info (using tax_id)...")
        # Use E. coli tax_id directly
        result = get_organism_info(tax_id=562)
        self.assertIsNotNone(result)
        self.assertIn('organism_info', result)
        self.assertIn('genome_count', result)
        print(f"E. coli genome count: {result['genome_count']}")
    
    def test_search_assemblies(self):
        """Test assembly search."""
        print("\nTesting assembly search...")
        result = search_assemblies(tax_id=9606, assembly_level='complete', max_results=5)
        self.assertIsNotNone(result)
        print(f"Found {len(result)} complete human assemblies")
        if len(result) > 0:
            print(result[['assembly_accession', 'assembly_name', 'organism_name']].head())
    
    def test_get_assembly_info(self):
        """Test getting assembly information."""
        print("\nTesting get assembly info...")
        # Get info for human reference genome
        accession = "GCF_000001405.40"
        result = get_assembly_info(accession)
        self.assertIsNotNone(result)
        print(f"Retrieved assembly info for {accession}")


def run_tests():
    """Run all tests."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNCBIDatasetsClient)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())

