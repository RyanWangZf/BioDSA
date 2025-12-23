"""Test suite for unified compound search and fetch functions.

Tests the compound unified functions from:
- biodsa.tools.compound.unified
"""

import os
import sys
import json
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from biodsa.tools.compound import search_compounds_unified, fetch_compound_details_unified


def test_search_compounds_kegg():
    """Test compound search with KEGG only."""
    print("\n=== Test: KEGG Compound Search ===")
    
    results, output = search_compounds_unified(
        search_term="glucose",
        search_type="name",
        limit_per_source=5,
        sources=['kegg']
    )
    
    print(output[:1000])
    
    assert 'kegg' in results, "Should have KEGG results"
    kegg_results = results['kegg']
    assert isinstance(kegg_results, list), "KEGG results should be a list"
    print(f"✓ Found {len(kegg_results)} KEGG compounds")


def test_search_compounds_pubchem():
    """Test compound search with PubChem only."""
    print("\n=== Test: PubChem Compound Search ===")
    
    results, output = search_compounds_unified(
        search_term="aspirin",
        search_type="name",
        limit_per_source=5,
        sources=['pubchem']
    )
    
    print(output[:1000])
    
    assert 'pubchem' in results, "Should have PubChem results"
    pubchem_results = results['pubchem']
    assert 'cids' in pubchem_results, "PubChem results should have CIDs"
    print(f"✓ Found {len(pubchem_results.get('cids', []))} PubChem compounds")


def test_search_compounds_both():
    """Test compound search with both KEGG and PubChem."""
    print("\n=== Test: Both Sources Compound Search ===")
    
    results, output = search_compounds_unified(
        search_term="caffeine",
        search_type="name",
        limit_per_source=3,
        sources=['kegg', 'pubchem']
    )
    
    print(output[:1500])
    
    assert 'kegg' in results or 'pubchem' in results, "Should have results from at least one source"
    print("✓ Integrated compound search works!")


def test_search_compounds_formula():
    """Test compound search by formula."""
    print("\n=== Test: Formula Compound Search ===")
    
    results, output = search_compounds_unified(
        search_term="C6H12O6",  # Glucose formula
        search_type="formula",
        limit_per_source=5,
        sources=['kegg']
    )
    
    print(output[:1000])
    
    assert 'kegg' in results, "Should have KEGG results"
    print("✓ Formula search works!")


def test_search_compounds_save_results():
    """Test that compound search saves results to file."""
    print("\n=== Test: Save Results to File ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = os.path.join(tmpdir, "test_compound_search.json")
        
        results, output = search_compounds_unified(
            search_term="acetaminophen",
            limit_per_source=3,
            sources=['kegg'],
            save_path=save_path
        )
        
        assert os.path.exists(save_path), f"File should be created at {save_path}"
        
        with open(save_path, 'r') as f:
            saved_data = json.load(f)
        
        assert 'search_term' in saved_data, "Saved data should have search_term"
        assert 'results' in saved_data, "Saved data should have results"
        print(f"✓ Results saved successfully to {save_path}")


def test_fetch_compound_kegg():
    """Test fetching compound details from KEGG."""
    print("\n=== Test: Fetch KEGG Compound Details ===")
    
    # ATP compound ID in KEGG
    details, output = fetch_compound_details_unified(
        compound_id="C00002",
        id_type="kegg",
        sources=['kegg']
    )
    
    print(output[:1500])
    
    assert 'kegg' in details, "Should have KEGG details"
    kegg_data = details['kegg']
    assert 'compound_info' in kegg_data, "Should have compound_info"
    print("✓ KEGG compound fetch works!")


def test_fetch_compound_pubchem():
    """Test fetching compound details from PubChem."""
    print("\n=== Test: Fetch PubChem Compound Details ===")
    
    # Aspirin CID
    details, output = fetch_compound_details_unified(
        compound_id="2244",
        id_type="pubchem",
        sources=['pubchem']
    )
    
    print(output[:1500])
    
    assert 'pubchem' in details, "Should have PubChem details"
    pubchem_data = details['pubchem']
    assert 'properties' in pubchem_data, "Should have properties"
    print("✓ PubChem compound fetch works!")


def test_fetch_compound_auto_detect():
    """Test auto-detection of compound ID type."""
    print("\n=== Test: Auto-Detect Compound ID Type ===")
    
    # KEGG ID (starts with C)
    details1, _ = fetch_compound_details_unified(
        compound_id="C00031",  # D-Glucose
        id_type=None  # Auto-detect
    )
    assert 'kegg' in details1, "Should detect KEGG ID"
    print("✓ Auto-detected KEGG ID")
    
    # PubChem CID (numeric)
    details2, _ = fetch_compound_details_unified(
        compound_id="5793",  # Glucose
        id_type=None  # Auto-detect
    )
    assert 'pubchem' in details2, "Should detect PubChem CID"
    print("✓ Auto-detected PubChem CID")


def test_fetch_compound_save_results():
    """Test that compound fetch saves results to file."""
    print("\n=== Test: Fetch and Save Results ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = os.path.join(tmpdir, "test_compound_details.json")
        
        details, output = fetch_compound_details_unified(
            compound_id="C00002",
            sources=['kegg'],
            save_path=save_path
        )
        
        assert os.path.exists(save_path), f"File should be created at {save_path}"
        
        with open(save_path, 'r') as f:
            saved_data = json.load(f)
        
        assert 'compound_id' in saved_data, "Saved data should have compound_id"
        assert 'details' in saved_data, "Saved data should have details"
        print(f"✓ Details saved successfully to {save_path}")


if __name__ == "__main__":
    print("Running unified compound function tests...\n")
    print("="*80)
    
    try:
        test_search_compounds_kegg()
        print("\n" + "="*80)
        
        test_search_compounds_pubchem()
        print("\n" + "="*80)
        
        test_search_compounds_both()
        print("\n" + "="*80)
        
        test_search_compounds_formula()
        print("\n" + "="*80)
        
        test_search_compounds_save_results()
        print("\n" + "="*80)
        
        test_fetch_compound_kegg()
        print("\n" + "="*80)
        
        test_fetch_compound_pubchem()
        print("\n" + "="*80)
        
        test_fetch_compound_auto_detect()
        print("\n" + "="*80)
        
        test_fetch_compound_save_results()
        print("\n" + "="*80)
        
        print("\n\n✅ All compound unified function tests passed successfully!")
        
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

