"""
Simple test to verify Reactome API is working.
This test runs faster by testing only basic functionality.
"""

import sys
from biodsa.tools.reactome import ReactomeClient, search_pathways, get_pathway_details

def test_reactome_basic():
    """Test basic Reactome functionality."""
    print("Testing Reactome API client...")
    print("Note: Reactome API can be slow (5-30 seconds per request)")
    
    # Test 1: Client initialization
    print("\n1. Testing client initialization...")
    client = ReactomeClient()
    print(f"✓ Client initialized with base URL: {client.base_url}")
    print(f"  Timeout: {client.timeout} seconds")
    
    # Test 2: Simple search (this may take 5-15 seconds)
    print("\n2. Testing pathway search (may take 5-15 seconds)...")
    print("   Searching for 'insulin signaling'...")
    try:
        result = search_pathways('insulin signaling', size=3)
        print(f"✓ Found {len(result)} pathways")
        if len(result) > 0:
            print(f"  First result: {result.iloc[0]['name']}")
    except Exception as e:
        print(f"✗ Search failed: {e}")
        return False
    
    # Test 3: Get pathway details (using a known pathway ID)
    print("\n3. Testing pathway details retrieval...")
    print("   Getting details for Apoptosis pathway (R-HSA-109581)...")
    try:
        details = get_pathway_details('R-HSA-109581')
        if 'basicInfo' in details:
            print(f"✓ Retrieved pathway: {details['basicInfo'].get('displayName', 'Unknown')}")
        else:
            print(f"✗ Unexpected response format")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    print("\n✓ All basic tests passed!")
    print("\nNote: For full test suite, run: python test_reactome.py")
    print("Warning: Full tests may take 2-5 minutes due to slow API responses")
    return True

if __name__ == '__main__':
    success = test_reactome_basic()
    sys.exit(0 if success else 1)

