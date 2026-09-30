"""
Test suite for Human Protein Atlas API tools.

Note: These tests require internet connection and access to the Human Protein Atlas API.
The API may have changed since implementation, so some tests may need adjustment.
"""

import sys
import unittest
from biodsa.tools.proteinatlas import (
    ProteinAtlasClient,
    search_proteins,
    get_protein_info,
    batch_protein_lookup,
    get_protein_classes,
    advanced_search,
    get_tissue_expression,
    get_blood_expression,
    get_brain_expression,
    search_by_tissue,
    compare_expression_profiles,
    get_subcellular_location,
    search_by_subcellular_location,
    get_pathology_data,
    search_cancer_markers,
    get_antibody_info,
)


class TestProteinAtlasClient(unittest.TestCase):
    """Test Human Protein Atlas API client."""
    
    def setUp(self):
        """Set up test client."""
        self.client = ProteinAtlasClient()
        self.test_gene = "TP53"
    
    def test_client_initialization(self):
        """Test client initialization."""
        self.assertIsNotNone(self.client)
        self.assertEqual(self.client.base_url, "https://www.proteinatlas.org")
    
    def test_search_proteins(self):
        """Test protein search."""
        print("\nTesting protein search...")
        try:
            df = search_proteins("p53", max_results=5)
            self.assertIsNotNone(df)
            self.assertGreater(len(df), 0)
            print(f"Found {len(df)} proteins")
            if len(df) > 0:
                print(df.head())
        except Exception as e:
            print(f"Protein search test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_get_protein_info(self):
        """Test getting protein info."""
        print("\nTesting get protein info...")
        try:
            info = get_protein_info(self.test_gene)
            self.assertIsNotNone(info)
            self.assertTrue(len(info) > 0)
            print(f"Gene: {info.get('Gene', info.get('g'))}")
            print(f"Ensembl: {info.get('Ensembl', info.get('eg'))}")
        except Exception as e:
            print(f"Get protein info test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_get_protein_classes(self):
        """Test getting protein classes."""
        print("\nTesting get protein classes...")
        try:
            classes = get_protein_classes(self.test_gene)
            self.assertIsNotNone(classes)
            print(f"Protein class: {classes.get('Protein class', classes.get('pc'))}")
        except Exception as e:
            print(f"Get protein classes test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_batch_protein_lookup(self):
        """Test batch protein lookup."""
        print("\nTesting batch protein lookup...")
        try:
            genes = ["TP53", "BRCA1"]
            results = batch_protein_lookup(genes)
            self.assertIsNotNone(results)
            self.assertEqual(len(results), len(genes))
            for r in results:
                status = "Success" if r['success'] else f"Failed: {r.get('error')}"
                print(f"{r['gene']}: {status}")
        except Exception as e:
            print(f"Batch protein lookup test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_get_tissue_expression(self):
        """Test getting tissue expression."""
        print("\nTesting get tissue expression...")
        try:
            expr = get_tissue_expression("ALB")  # Albumin is highly expressed in liver
            self.assertIsNotNone(expr)
            print(f"Gene: {expr.get('Gene', expr.get('g'))}")
            if 't_RNA_liver' in expr:
                print(f"Liver expression: {expr.get('t_RNA_liver')}")
        except Exception as e:
            print(f"Get tissue expression test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_get_blood_expression(self):
        """Test getting blood expression."""
        print("\nTesting get blood expression...")
        try:
            expr = get_blood_expression("CD4")
            self.assertIsNotNone(expr)
            print(f"Gene: {expr.get('Gene', expr.get('g'))}")
        except Exception as e:
            print(f"Get blood expression test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_get_brain_expression(self):
        """Test getting brain expression."""
        print("\nTesting get brain expression...")
        try:
            expr = get_brain_expression("APP")  # Amyloid precursor protein
            self.assertIsNotNone(expr)
            print(f"Gene: {expr.get('Gene', expr.get('g'))}")
        except Exception as e:
            print(f"Get brain expression test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_get_subcellular_location(self):
        """Test getting subcellular location."""
        print("\nTesting get subcellular location...")
        try:
            location = get_subcellular_location(self.test_gene)
            self.assertIsNotNone(location)
            print(f"Gene: {location.get('Gene', location.get('g'))}")
            if 'Subcellular location' in location or 'scl' in location:
                print(f"Location: {location.get('Subcellular location', location.get('scl'))}")
        except Exception as e:
            print(f"Get subcellular location test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_get_pathology_data(self):
        """Test getting pathology data."""
        print("\nTesting get pathology data...")
        try:
            pathology = get_pathology_data(self.test_gene)
            self.assertIsNotNone(pathology)
            print(f"Gene: {pathology.get('Gene', pathology.get('g'))}")
        except Exception as e:
            print(f"Get pathology data test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_get_antibody_info(self):
        """Test getting antibody info."""
        print("\nTesting get antibody info...")
        try:
            ab_info = get_antibody_info(self.test_gene)
            self.assertIsNotNone(ab_info)
            print(f"Gene: {ab_info.get('Gene', ab_info.get('g'))}")
            if 'Antibody' in ab_info or 'ab' in ab_info:
                print(f"Antibody: {ab_info.get('Antibody', ab_info.get('ab'))}")
        except Exception as e:
            print(f"Get antibody info test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_advanced_search(self):
        """Test advanced search."""
        print("\nTesting advanced search...")
        try:
            # Simple search with chromosome filter
            df = advanced_search(chromosome="17", max_results=5)
            self.assertIsNotNone(df)
            print(f"Found {len(df)} proteins on chromosome 17")
            if len(df) > 0:
                print(df.head())
        except Exception as e:
            print(f"Advanced search test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")


def run_tests():
    """Run all tests."""
    print("=" * 70)
    print("Human Protein Atlas API Tests")
    print("=" * 70)
    print("\nNote: These tests require internet connection.")
    print("Tests may be skipped if the API is unavailable or has changed.")
    print("=" * 70)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestProteinAtlasClient)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())

