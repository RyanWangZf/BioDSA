#!/usr/bin/env python3
"""Basic tests for Open Targets Platform tools.

This script runs basic tests to verify the Open Targets tools are working correctly.
"""

import sys


def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from biodsa.tools.opentargets import (
            OpenTargetsClient,
            search_targets,
            search_diseases,
            get_target_details,
            get_disease_details,
            get_target_associated_diseases,
            get_disease_associated_targets,
            get_disease_targets_summary,
            get_target_disease_evidence,
            analyze_association_evidence,
            search_drugs,
            get_drug_details,
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
        from biodsa.tools.opentargets import OpenTargetsClient
        client = OpenTargetsClient()
        print("✓ Client initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Client initialization failed: {e}")
        return False


def test_target_search():
    """Test target search functionality."""
    print("\nTesting target search...")
    try:
        from biodsa.tools.opentargets import search_targets
        df, output = search_targets("BRCA2", size=3)
        
        if df.empty:
            print("✗ No results returned")
            return False
        
        if 'id' not in df.columns or 'name' not in df.columns:
            print("✗ Expected columns not found")
            return False
        
        print(f"✓ Target search successful, found {len(df)} results")
        print(f"  First result: {df.iloc[0]['name']} ({df.iloc[0]['id']})")
        return True
    except Exception as e:
        print(f"✗ Target search failed: {e}")
        return False


def test_disease_search():
    """Test disease search functionality."""
    print("\nTesting disease search...")
    try:
        from biodsa.tools.opentargets import search_diseases
        df, output = search_diseases("breast cancer", size=3)
        
        if df.empty:
            print("✗ No results returned")
            return False
        
        if 'id' not in df.columns or 'name' not in df.columns:
            print("✗ Expected columns not found")
            return False
        
        print(f"✓ Disease search successful, found {len(df)} results")
        print(f"  First result: {df.iloc[0]['name']} ({df.iloc[0]['id']})")
        return True
    except Exception as e:
        print(f"✗ Disease search failed: {e}")
        return False


def test_target_details():
    """Test getting target details."""
    print("\nTesting target details...")
    try:
        from biodsa.tools.opentargets import get_target_details
        # ENSG00000139618 is BRCA2
        details, output = get_target_details("ENSG00000139618")
        
        if not details or 'data' not in details:
            print("✗ No details returned")
            return False
        
        target = details.get('data', {}).get('target', {})
        if not target:
            print("✗ Target data not found")
            return False
        
        print(f"✓ Target details retrieved successfully")
        print(f"  Symbol: {target.get('approvedSymbol', 'N/A')}")
        print(f"  Name: {target.get('approvedName', 'N/A')}")
        return True
    except Exception as e:
        print(f"✗ Target details failed: {e}")
        return False


def test_disease_associated_targets():
    """Test getting targets associated with a disease."""
    print("\nTesting disease-target associations...")
    try:
        from biodsa.tools.opentargets import get_disease_associated_targets
        # EFO_0000305 is breast carcinoma
        df, output = get_disease_associated_targets("EFO_0000305", size=5)
        
        if df.empty:
            print("✗ No associations returned")
            return False
        
        required_cols = ['target_id', 'target_symbol', 'score']
        if not all(col in df.columns for col in required_cols):
            print("✗ Expected columns not found")
            return False
        
        print(f"✓ Disease-target associations retrieved successfully")
        print(f"  Found {len(df)} associations")
        print(f"  Top target: {df.iloc[0]['target_symbol']} (score: {df.iloc[0]['score']:.4f})")
        return True
    except Exception as e:
        print(f"✗ Disease-target associations failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("Open Targets Platform Tools - Basic Tests")
    print("=" * 80)
    
    tests = [
        ("Imports", test_imports),
        ("Client Initialization", test_client_initialization),
        ("Target Search", test_target_search),
        ("Disease Search", test_disease_search),
        ("Target Details", test_target_details),
        ("Disease-Target Associations", test_disease_associated_targets),
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

