#!/usr/bin/env python3
"""Basic tests for ChEMBL Database tools.

This script runs basic tests to verify the ChEMBL tools are working correctly.
"""

import sys


def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from biodsa.tools.chembl import (
            ChEMBLClient,
            search_compounds,
            get_compound_details,
            search_similar_compounds,
            search_substructure,
            batch_compound_lookup,
        )
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_client_initialization():
    """Test that the client can be initialized."""
    print("\nTesting client initialization...")
    try:
        from biodsa.tools.chembl import ChEMBLClient
        client = ChEMBLClient()
        print("✓ Client initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Client initialization failed: {e}")
        return False


def test_compound_search():
    """Test compound search functionality."""
    print("\nTesting compound search...")
    try:
        from biodsa.tools.chembl import search_compounds
        df, output = search_compounds("aspirin", limit=3)
        
        if df.empty:
            print("✗ No results returned")
            return False
        
        if 'molecule_chembl_id' not in df.columns:
            print("✗ Expected columns not found")
            return False
        
        print(f"✓ Compound search successful, found {len(df)} results")
        print(f"  First result: {df.iloc[0].get('pref_name', 'N/A')} ({df.iloc[0]['molecule_chembl_id']})")
        return True
    except Exception as e:
        print(f"✗ Compound search failed: {e}")
        return False


def test_compound_details():
    """Test getting compound details."""
    print("\nTesting compound details...")
    try:
        from biodsa.tools.chembl import get_compound_details
        # CHEMBL25 is aspirin
        details, output = get_compound_details("CHEMBL25")
        
        if not details:
            print("✗ No details returned")
            return False
        
        if 'molecule_chembl_id' not in details:
            print("✗ Expected fields not found")
            return False
        
        print(f"✓ Compound details retrieved successfully")
        print(f"  Name: {details.get('pref_name', 'N/A')}")
        print(f"  ID: {details.get('molecule_chembl_id', 'N/A')}")
        
        # Check molecular properties
        props = details.get('molecule_properties', {})
        if props:
            print(f"  MW: {props.get('full_mwt', props.get('molecular_weight', 'N/A'))} Da")
        
        return True
    except Exception as e:
        print(f"✗ Compound details failed: {e}")
        return False


def test_similar_compounds():
    """Test similarity search."""
    print("\nTesting similarity search...")
    try:
        from biodsa.tools.chembl import search_similar_compounds
        # Aspirin SMILES
        smiles = "CC(=O)Oc1ccccc1C(=O)O"
        df, output = search_similar_compounds(smiles, similarity=70, limit=5)
        
        if df.empty:
            print("✗ No similar compounds found")
            return False
        
        print(f"✓ Similarity search successful, found {len(df)} similar compounds")
        if not df.empty:
            print(f"  First result: {df.iloc[0].get('pref_name', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"✗ Similarity search failed: {e}")
        return False


def test_substructure_search():
    """Test substructure search."""
    print("\nTesting substructure search...")
    try:
        from biodsa.tools.chembl import search_substructure
        # Benzene ring
        smiles = "c1ccccc1"
        df, output = search_substructure(smiles, limit=5)
        
        if df.empty:
            print("✗ No compounds with substructure found")
            return False
        
        print(f"✓ Substructure search successful, found {len(df)} compounds")
        return True
    except Exception as e:
        print(f"✗ Substructure search failed: {e}")
        return False


def test_batch_lookup():
    """Test batch compound lookup."""
    print("\nTesting batch compound lookup...")
    try:
        from biodsa.tools.chembl import batch_compound_lookup
        df, output = batch_compound_lookup(["CHEMBL25", "CHEMBL59"])
        
        if df.empty:
            print("✗ No results returned")
            return False
        
        successful = df[df['success'] == True]
        print(f"✓ Batch lookup successful: {len(successful)}/{len(df)} compounds retrieved")
        
        return True
    except Exception as e:
        print(f"✗ Batch lookup failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("ChEMBL Database Tools - Basic Tests")
    print("=" * 80)
    
    tests = [
        ("Imports", test_imports),
        ("Client Initialization", test_client_initialization),
        ("Compound Search", test_compound_search),
        ("Compound Details", test_compound_details),
        ("Similar Compounds", test_similar_compounds),
        ("Substructure Search", test_substructure_search),
        ("Batch Lookup", test_batch_lookup),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            results.append((name, test_func()))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

