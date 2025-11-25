#!/usr/bin/env python3
"""Basic tests for HPO (Human Phenotype Ontology) tools.

This script runs basic tests to verify the HPO tools are working correctly.
"""

import sys


def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from biodsa.tools.hpo import (
            HPOClient,
            search_hpo_terms,
            get_hpo_term_details,
            get_hpo_term_hierarchy,
            validate_hpo_id,
            get_hpo_term_path,
            compare_hpo_terms,
            get_hpo_term_statistics,
            batch_get_hpo_terms,
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
        from biodsa.tools.hpo import HPOClient
        client = HPOClient()
        print("✓ Client initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Client initialization failed: {e}")
        return False


def test_search_terms():
    """Test HPO term search functionality."""
    print("\nTesting HPO term search...")
    try:
        from biodsa.tools.hpo import search_hpo_terms
        df, output = search_hpo_terms("seizure", max_results=3)
        
        if df.empty:
            print("✗ No results returned")
            return False
        
        if 'id' not in df.columns or 'name' not in df.columns:
            print("✗ Expected columns not found")
            return False
        
        print(f"✓ HPO term search successful, found {len(df)} results")
        print(f"  First result: {df.iloc[0]['name']} ({df.iloc[0]['id']})")
        return True
    except Exception as e:
        print(f"✗ HPO term search failed: {e}")
        return False


def test_get_term_details():
    """Test getting HPO term details."""
    print("\nTesting HPO term details...")
    try:
        from biodsa.tools.hpo import get_hpo_term_details
        # HP:0001250 is "Seizure"
        details, output = get_hpo_term_details("HP:0001250")
        
        if not details:
            print("✗ No details returned")
            return False
        
        if 'id' not in details:
            print("✗ Expected fields not found")
            return False
        
        print(f"✓ HPO term details retrieved successfully")
        print(f"  Name: {details.get('name', 'N/A')}")
        print(f"  ID: {details.get('id', 'N/A')}")
        return True
    except Exception as e:
        print(f"✗ HPO term details failed: {e}")
        return False


def test_validate_hpo_id():
    """Test HPO ID validation."""
    print("\nTesting HPO ID validation...")
    try:
        from biodsa.tools.hpo import validate_hpo_id
        
        # Test valid ID
        result, output = validate_hpo_id("HP:0001250")
        
        if not result.get('valid_format'):
            print("✗ Valid ID not recognized as valid")
            return False
        
        if not result.get('exists'):
            print("✗ Existing HPO term not found")
            return False
        
        # Test invalid ID
        result2, _ = validate_hpo_id("INVALID")
        if result2.get('valid_format'):
            print("✗ Invalid ID recognized as valid")
            return False
        
        print(f"✓ HPO ID validation working correctly")
        return True
    except Exception as e:
        print(f"✗ HPO ID validation failed: {e}")
        return False


def test_term_hierarchy():
    """Test getting term hierarchy."""
    print("\nTesting HPO term hierarchy...")
    try:
        from biodsa.tools.hpo import get_hpo_term_hierarchy
        # HP:0001250 is "Seizure"
        df, output = get_hpo_term_hierarchy("HP:0001250", direction="parents", max_results=5)
        
        # It's okay if there are no results for root-level terms
        print(f"✓ HPO term hierarchy retrieved successfully")
        print(f"  Found {len(df)} parent terms")
        return True
    except Exception as e:
        print(f"✗ HPO term hierarchy failed: {e}")
        return False


def test_term_path():
    """Test getting term path."""
    print("\nTesting HPO term path...")
    try:
        from biodsa.tools.hpo import get_hpo_term_path
        # HP:0001250 is "Seizure"
        path, output = get_hpo_term_path("HP:0001250")
        
        if not path:
            print("✗ No path returned")
            return False
        
        print(f"✓ HPO term path retrieved successfully")
        print(f"  Path depth: {len(path) - 1} levels")
        return True
    except Exception as e:
        print(f"✗ HPO term path failed: {e}")
        return False


def test_term_statistics():
    """Test getting term statistics."""
    print("\nTesting HPO term statistics...")
    try:
        from biodsa.tools.hpo import get_hpo_term_statistics
        # HP:0001250 is "Seizure"
        stats, output = get_hpo_term_statistics("HP:0001250")
        
        if not stats:
            print("✗ No statistics returned")
            return False
        
        if 'hierarchy' not in stats:
            print("✗ Expected statistics not found")
            return False
        
        print(f"✓ HPO term statistics retrieved successfully")
        print(f"  Depth: {stats['hierarchy']['depth_from_root']} levels")
        return True
    except Exception as e:
        print(f"✗ HPO term statistics failed: {e}")
        return False


def test_batch_get_terms():
    """Test batch term retrieval."""
    print("\nTesting batch HPO term retrieval...")
    try:
        from biodsa.tools.hpo import batch_get_hpo_terms
        df, output = batch_get_hpo_terms(["HP:0001250", "HP:0012469"])
        
        if df.empty:
            print("✗ No results returned")
            return False
        
        print(f"✓ Batch term retrieval successful")
        print(f"  Retrieved {len(df)} terms")
        return True
    except Exception as e:
        print(f"✗ Batch term retrieval failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("Human Phenotype Ontology Tools - Basic Tests")
    print("=" * 80)
    
    tests = [
        ("Imports", test_imports),
        ("Client Initialization", test_client_initialization),
        ("HPO Term Search", test_search_terms),
        ("HPO Term Details", test_get_term_details),
        ("HPO ID Validation", test_validate_hpo_id),
        ("HPO Term Hierarchy", test_term_hierarchy),
        ("HPO Term Path", test_term_path),
        ("HPO Term Statistics", test_term_statistics),
        ("Batch Term Retrieval", test_batch_get_terms),
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

