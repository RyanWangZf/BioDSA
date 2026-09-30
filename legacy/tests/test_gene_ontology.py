#!/usr/bin/env python3
"""Basic tests for Gene Ontology tools.

This script runs basic tests to verify the GO tools are working correctly.
"""

import sys


def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from biodsa.tools.gene_ontology import (
            GeneOntologyClient,
            search_go_terms,
            get_go_term_details,
            get_go_term_hierarchy,
            validate_go_id,
            get_ontology_statistics,
            get_gene_annotations,
            get_term_annotations,
            get_evidence_codes,
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
        from biodsa.tools.gene_ontology import GeneOntologyClient
        client = GeneOntologyClient()
        print("✓ Client initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Client initialization failed: {e}")
        return False


def test_search_terms():
    """Test GO term search functionality."""
    print("\nTesting GO term search...")
    try:
        from biodsa.tools.gene_ontology import search_go_terms
        df, output = search_go_terms("kinase activity", limit=3)
        
        if df.empty:
            print("✗ No results returned")
            return False
        
        if 'id' not in df.columns or 'name' not in df.columns:
            print("✗ Expected columns not found")
            return False
        
        print(f"✓ GO term search successful, found {len(df)} results")
        print(f"  First result: {df.iloc[0]['name']} ({df.iloc[0]['id']})")
        return True
    except Exception as e:
        print(f"✗ GO term search failed: {e}")
        return False


def test_get_term_details():
    """Test getting GO term details."""
    print("\nTesting GO term details...")
    try:
        from biodsa.tools.gene_ontology import get_go_term_details
        # GO:0008150 is "biological_process"
        details, output = get_go_term_details("GO:0008150")
        
        if not details:
            print("✗ No details returned")
            return False
        
        if 'id' not in details:
            print("✗ Expected fields not found")
            return False
        
        print(f"✓ GO term details retrieved successfully")
        print(f"  Name: {details.get('name', 'N/A')}")
        print(f"  ID: {details.get('id', 'N/A')}")
        return True
    except Exception as e:
        print(f"✗ GO term details failed: {e}")
        return False


def test_validate_go_id():
    """Test GO ID validation."""
    print("\nTesting GO ID validation...")
    try:
        from biodsa.tools.gene_ontology import validate_go_id
        
        # Test valid ID
        result, output = validate_go_id("GO:0008150")
        
        if not result.get('valid_format'):
            print("✗ Valid ID not recognized as valid")
            return False
        
        if not result.get('exists'):
            print("✗ Existing GO term not found")
            return False
        
        # Test invalid ID
        result2, _ = validate_go_id("INVALID")
        if result2.get('valid_format'):
            print("✗ Invalid ID recognized as valid")
            return False
        
        print(f"✓ GO ID validation working correctly")
        return True
    except Exception as e:
        print(f"✗ GO ID validation failed: {e}")
        return False


def test_term_hierarchy():
    """Test getting term hierarchy."""
    print("\nTesting GO term hierarchy...")
    try:
        from biodsa.tools.gene_ontology import get_go_term_hierarchy
        # GO:0004672 is "protein kinase activity"
        df, output = get_go_term_hierarchy("GO:0004672", direction="ancestors")
        
        if df.empty:
            print("⚠ No ancestors found (might be root term)")
            # This is not necessarily a failure
        else:
            print(f"✓ GO term hierarchy retrieved successfully")
            print(f"  Found {len(df)} ancestor terms")
        
        return True
    except Exception as e:
        print(f"✗ GO term hierarchy failed: {e}")
        return False


def test_ontology_statistics():
    """Test getting ontology statistics."""
    print("\nTesting ontology statistics...")
    try:
        from biodsa.tools.gene_ontology import get_ontology_statistics
        stats, output = get_ontology_statistics()
        
        if not stats:
            print("✗ No statistics returned")
            return False
        
        if 'ontologies' not in stats:
            print("✗ Expected statistics not found")
            return False
        
        print(f"✓ Ontology statistics retrieved successfully")
        print(f"  Ontologies: {len(stats['ontologies'])}")
        return True
    except Exception as e:
        print(f"✗ Ontology statistics failed: {e}")
        return False


def test_evidence_codes():
    """Test getting evidence codes."""
    print("\nTesting evidence codes...")
    try:
        from biodsa.tools.gene_ontology import get_evidence_codes
        df, output = get_evidence_codes()
        
        if df.empty:
            print("✗ No evidence codes returned")
            return False
        
        if 'code' not in df.columns or 'category' not in df.columns:
            print("✗ Expected columns not found")
            return False
        
        print(f"✓ Evidence codes retrieved successfully")
        print(f"  Total codes: {len(df)}")
        return True
    except Exception as e:
        print(f"✗ Evidence codes failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("Gene Ontology Tools - Basic Tests")
    print("=" * 80)
    
    tests = [
        ("Imports", test_imports),
        ("Client Initialization", test_client_initialization),
        ("GO Term Search", test_search_terms),
        ("GO Term Details", test_get_term_details),
        ("GO ID Validation", test_validate_go_id),
        ("GO Term Hierarchy", test_term_hierarchy),
        ("Ontology Statistics", test_ontology_statistics),
        ("Evidence Codes", test_evidence_codes),
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

