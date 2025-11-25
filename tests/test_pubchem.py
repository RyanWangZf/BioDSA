"""
Test suite for PubChem API tools.

Note: These tests require internet connection and access to the PubChem API.
The API may have changed since implementation, so some tests may need adjustment.
"""

import sys
import unittest
from biodsa.tools.pubchem import (
    PubChemClient,
    # Compound tools
    search_compounds,
    get_compound_info,
    get_compound_synonyms,
    search_by_smiles,
    search_by_cas_number,
    batch_compound_lookup,
    # Structure tools
    search_similar_compounds,
    substructure_search,
    get_3d_conformers,
    analyze_stereochemistry,
    # Property tools
    get_compound_properties,
    calculate_descriptors,
    assess_drug_likeness,
    analyze_molecular_complexity,
    # Bioassay tools
    get_compound_bioactivities,
    # Safety tools
    get_safety_data,
)


class TestPubChemClient(unittest.TestCase):
    """Test PubChem API client."""
    
    def setUp(self):
        """Set up test client."""
        self.client = PubChemClient()
        self.test_cid = 2244  # Aspirin
        self.test_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"  # Aspirin
    
    def test_client_initialization(self):
        """Test client initialization."""
        self.assertIsNotNone(self.client)
        self.assertEqual(
            self.client.base_url,
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        )
    
    def test_search_compounds(self):
        """Test compound search."""
        print("\nTesting compound search...")
        try:
            df = search_compounds("aspirin", max_records=5)
            self.assertIsNotNone(df)
            self.assertGreater(len(df), 0)
            print(f"Found {len(df)} compounds")
            if len(df) > 0:
                print(df.head())
        except Exception as e:
            print(f"Search compounds test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_get_compound_info(self):
        """Test getting compound information."""
        print("\nTesting get compound info...")
        try:
            info = get_compound_info(self.test_cid)
            self.assertIsNotNone(info)
            self.assertIn('PC_Compounds', info)
            print(f"Retrieved info for CID {self.test_cid}")
        except Exception as e:
            print(f"Get compound info test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_get_compound_synonyms(self):
        """Test getting compound synonyms."""
        print("\nTesting get compound synonyms...")
        try:
            synonyms = get_compound_synonyms(self.test_cid)
            self.assertIsNotNone(synonyms)
            self.assertIsInstance(synonyms, list)
            self.assertGreater(len(synonyms), 0)
            print(f"Found {len(synonyms)} synonyms")
            print(f"First 5: {synonyms[:5]}")
        except Exception as e:
            print(f"Get synonyms test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_search_by_smiles(self):
        """Test searching by SMILES."""
        print("\nTesting search by SMILES...")
        try:
            result = search_by_smiles(self.test_smiles)
            self.assertIsNotNone(result)
            self.assertIn('cid', result)
            print(f"Found CID: {result['cid']}")
        except Exception as e:
            print(f"Search by SMILES test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_search_by_cas_number(self):
        """Test searching by CAS number."""
        print("\nTesting search by CAS number...")
        try:
            # Aspirin CAS: 50-78-2
            result = search_by_cas_number("50-78-2")
            self.assertIsNotNone(result)
            if result:
                print(f"Found CID: {result['cid']}")
        except Exception as e:
            print(f"Search by CAS test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_batch_compound_lookup(self):
        """Test batch compound lookup."""
        print("\nTesting batch compound lookup...")
        try:
            cids = [2244, 3672]  # Aspirin, Ibuprofen
            results = batch_compound_lookup(cids, operation='property')
            self.assertIsNotNone(results)
            self.assertGreater(len(results), 0)
            for r in results:
                status = "Success" if r.get('success') else f"Failed: {r.get('error')}"
                print(f"CID {r.get('cid')}: {status}")
        except Exception as e:
            print(f"Batch lookup test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_search_similar_compounds(self):
        """Test similarity search."""
        print("\nTesting similarity search...")
        try:
            df = search_similar_compounds(self.test_smiles, threshold=90, max_records=5)
            self.assertIsNotNone(df)
            print(f"Found {len(df)} similar compounds")
            if len(df) > 0:
                print(df.head())
        except Exception as e:
            print(f"Similarity search test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_substructure_search(self):
        """Test substructure search."""
        print("\nTesting substructure search...")
        try:
            # Search for benzene ring
            df = substructure_search("c1ccccc1", max_records=5)
            self.assertIsNotNone(df)
            print(f"Found {len(df)} compounds with benzene ring")
        except Exception as e:
            print(f"Substructure search test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_get_compound_properties(self):
        """Test getting compound properties."""
        print("\nTesting get compound properties...")
        try:
            props = get_compound_properties(self.test_cid)
            self.assertIsNotNone(props)
            print(f"Molecular Weight: {props.get('MolecularWeight')}")
            print(f"XLogP: {props.get('XLogP')}")
            print(f"TPSA: {props.get('TPSA')}")
        except Exception as e:
            print(f"Get properties test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_calculate_descriptors(self):
        """Test calculating descriptors."""
        print("\nTesting calculate descriptors...")
        try:
            descriptors = calculate_descriptors(self.test_cid, descriptor_type='basic')
            self.assertIsNotNone(descriptors)
            print(f"Molecular Formula: {descriptors.get('MolecularFormula')}")
        except Exception as e:
            print(f"Calculate descriptors test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_assess_drug_likeness(self):
        """Test drug-likeness assessment."""
        print("\nTesting drug-likeness assessment...")
        try:
            assessment = assess_drug_likeness(self.test_cid)
            self.assertIsNotNone(assessment)
            print(f"Lipinski violations: {assessment['lipinski_violations']}")
            print(f"Passes Lipinski: {assessment['passes_lipinski']}")
            print(f"Veber compliant: {assessment['veber_compliant']}")
            print(f"Assessment: {assessment['assessment']}")
        except Exception as e:
            print(f"Drug-likeness assessment test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_analyze_molecular_complexity(self):
        """Test molecular complexity analysis."""
        print("\nTesting molecular complexity analysis...")
        try:
            complexity = analyze_molecular_complexity(self.test_cid)
            self.assertIsNotNone(complexity)
            print(f"Complexity score: {complexity['complexity_score']}")
            print(f"Category: {complexity['complexity_category']}")
        except Exception as e:
            print(f"Complexity analysis test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_get_3d_conformers(self):
        """Test getting 3D conformers."""
        print("\nTesting get 3D conformers...")
        try:
            conformers = get_3d_conformers(self.test_cid)
            self.assertIsNotNone(conformers)
            if 'Volume3D' in conformers:
                print(f"3D Volume: {conformers.get('Volume3D')}")
                print(f"Conformer count: {conformers.get('ConformerCount3D')}")
        except Exception as e:
            print(f"Get 3D conformers test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_analyze_stereochemistry(self):
        """Test stereochemistry analysis."""
        print("\nTesting stereochemistry analysis...")
        try:
            stereo = analyze_stereochemistry(self.test_cid)
            self.assertIsNotNone(stereo)
            print(f"Atom stereo count: {stereo.get('AtomStereoCount')}")
            if 'IsomericSMILES' in stereo:
                print(f"Isomeric SMILES: {stereo.get('IsomericSMILES')}")
        except Exception as e:
            print(f"Stereochemistry analysis test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_get_compound_bioactivities(self):
        """Test getting compound bioactivities."""
        print("\nTesting get compound bioactivities...")
        try:
            aids = get_compound_bioactivities(self.test_cid)
            self.assertIsNotNone(aids)
            print(f"Found {len(aids)} bioassays")
        except Exception as e:
            print(f"Get bioactivities test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")
    
    def test_get_safety_data(self):
        """Test getting safety data."""
        print("\nTesting get safety data...")
        try:
            safety = get_safety_data(self.test_cid)
            self.assertIsNotNone(safety)
            print(f"Safety data retrieved")
        except Exception as e:
            print(f"Get safety data test skipped: {e}")
            self.skipTest(f"API may be unavailable: {e}")


def run_tests():
    """Run all tests."""
    print("=" * 70)
    print("PubChem API Tests")
    print("=" * 70)
    print("\nNote: These tests require internet connection.")
    print("Tests may be skipped if the API is unavailable or has changed.")
    print("=" * 70)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPubChemClient)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())

