"""
Test suite for Reactome API tools.
"""

import sys
import unittest
from biodsa.tools.reactome import (
    ReactomeClient,
    search_pathways,
    get_pathway_details,
    get_pathway_hierarchy,
    get_pathway_reactions,
    get_pathway_participants,
    find_pathways_by_gene,
    get_gene_pathways_dataframe,
    get_protein_interactions,
    find_pathways_by_disease,
)


class TestReactomeClient(unittest.TestCase):
    """Test Reactome API client."""
    
    def setUp(self):
        """Set up test client."""
        self.client = ReactomeClient()
    
    def test_client_initialization(self):
        """Test client initialization."""
        self.assertIsNotNone(self.client)
        self.assertEqual(self.client.base_url, "https://reactome.org/ContentService")
    
    def test_search_pathways(self):
        """Test pathway search."""
        print("\nTesting pathway search...")
        result = search_pathways('apoptosis', size=5)
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
        print(f"Found {len(result)} apoptosis pathways")
        print(result[['id', 'name', 'species']].head())
    
    def test_search_pathways_with_type(self):
        """Test pathway search with entity type filter."""
        print("\nTesting pathway search with type filter...")
        result = search_pathways('TP53', entity_type='protein', size=5)
        self.assertIsNotNone(result)
        print(f"Found {len(result)} protein entities for TP53")
    
    def test_get_pathway_details(self):
        """Test getting pathway details."""
        print("\nTesting get pathway details...")
        # Use a well-known pathway ID (Apoptosis)
        details = get_pathway_details('R-HSA-109581')
        self.assertIsNotNone(details)
        self.assertIn('basicInfo', details)
        print(f"Retrieved details for pathway: {details['basicInfo'].get('displayName', 'Unknown')}")
    
    def test_get_pathway_hierarchy(self):
        """Test getting pathway hierarchy."""
        print("\nTesting get pathway hierarchy...")
        hierarchy = get_pathway_hierarchy('R-HSA-109581')
        self.assertIsNotNone(hierarchy)
        self.assertIn('basicInfo', hierarchy)
        print(f"Pathway: {hierarchy['basicInfo']['name']}")
        if isinstance(hierarchy.get('children'), list):
            print(f"Children: {len(hierarchy['children'])}")
    
    def test_get_pathway_reactions(self):
        """Test getting pathway reactions."""
        print("\nTesting get pathway reactions...")
        reactions = get_pathway_reactions('R-HSA-109581')
        self.assertIsNotNone(reactions)
        print(f"Found {len(reactions)} reactions")
        if len(reactions) > 0:
            print(reactions[['id', 'name', 'type']].head())
    
    def test_get_pathway_participants(self):
        """Test getting pathway participants."""
        print("\nTesting get pathway participants...")
        participants = get_pathway_participants('R-HSA-109581', max_results=10)
        self.assertIsNotNone(participants)
        print(f"Found {len(participants)} participants")
        if len(participants) > 0:
            print(participants[['id', 'name', 'type']].head())
    
    def test_find_pathways_by_gene(self):
        """Test finding pathways by gene."""
        print("\nTesting find pathways by gene...")
        # Use a less popular gene to avoid timeout (INS - insulin)
        result = find_pathways_by_gene('INS')
        self.assertIsNotNone(result)
        self.assertIn('pathwayCount', result)
        print(f"Found {result['pathwayCount']} pathways for INS")
        if result.get('pathways'):
            print(f"First pathway: {result['pathways'][0]['name']}")
        elif 'error' in result:
            print(f"Note: {result.get('note', result['error'])}")
    
    def test_get_gene_pathways_dataframe(self):
        """Test getting gene pathways as DataFrame."""
        print("\nTesting get gene pathways dataframe...")
        # Use a less popular gene to avoid timeout (GCG - glucagon)
        df = get_gene_pathways_dataframe('GCG')
        self.assertIsNotNone(df)
        print(f"Found {len(df)} pathways for GCG")
        if len(df) > 0:
            print(df[['id', 'name']].head())
        else:
            print("No pathways found or API timeout")
    
    def test_get_protein_interactions(self):
        """Test getting protein interactions."""
        print("\nTesting get protein interactions...")
        interactions = get_protein_interactions('R-HSA-109581')
        self.assertIsNotNone(interactions)
        self.assertIn('proteinCount', interactions)
        print(f"Found {interactions['proteinCount']} proteins")
        print(f"Found {interactions['reactionCount']} reactions")
    
    def test_find_pathways_by_disease(self):
        """Test finding pathways by disease."""
        print("\nTesting find pathways by disease...")
        result = find_pathways_by_disease('cancer', size=5)
        self.assertIsNotNone(result)
        print(f"Found {len(result)} cancer-related pathways")
        if len(result) > 0:
            print(result[['id', 'name']].head())
    
    def test_pathway_id_resolution(self):
        """Test pathway ID resolution."""
        print("\nTesting pathway ID resolution...")
        # Test with pathway name
        details = get_pathway_details('Apoptosis')
        self.assertIsNotNone(details)
        if 'basicInfo' in details:
            print(f"Resolved 'Apoptosis' to: {details.get('id')}")


def run_tests():
    """Run all tests."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestReactomeClient)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())

