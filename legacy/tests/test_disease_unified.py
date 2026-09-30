"""Test suite for unified disease search and fetch functions.

Tests the disease unified functions from:
- biodsa.tools.diseases.unified_disease_search
"""

import os
import sys
import json
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from biodsa.tools.diseases import (
    search_diseases_unified,
    fetch_disease_details_unified,
    aggregate_disease_names,
    aggregate_disease_identifiers
)


def test_search_diseases_biothings():
    """Test disease search with BioThings only."""
    print("\n=== Test: BioThings Disease Search ===")
    
    results, output = search_diseases_unified(
        search_term="diabetes",
        limit_per_source=5,
        sources=['biothings']
    )
    
    print(output[:1500])
    
    assert 'biothings' in results, "Should have BioThings results"
    print("✓ BioThings disease search works!")


def test_search_diseases_kegg():
    """Test disease search with KEGG only."""
    print("\n=== Test: KEGG Disease Search ===")
    
    results, output = search_diseases_unified(
        search_term='non-small cell lung cancer',
        limit_per_source=10,
        sources=['biothings', 'kegg', 'opentargets'],
        save_path='/workdir/NSCLC_search.json',
    )
    
    print(output[:1500])
    
    assert 'kegg' in results, "Should have KEGG results"
    kegg_results = results['kegg']
    assert isinstance(kegg_results, list), "KEGG results should be a list"
    print(f"✓ Found {len(kegg_results)} KEGG diseases")


def test_search_diseases_opentargets():
    """Test disease search with Open Targets only."""
    print("\n=== Test: Open Targets Disease Search ===")
    
    results, output = search_diseases_unified(
        search_term="alzheimer",
        limit_per_source=5,
        sources=['opentargets']
    )
    
    print(output[:1500])
    
    assert 'opentargets' in results, "Should have Open Targets results"
    print("✓ Open Targets disease search works!")


def test_search_diseases_multiple_sources():
    """Test disease search with multiple sources."""
    print("\n=== Test: Multiple Sources Disease Search ===")
    
    results, output = search_diseases_unified(
        search_term="breast cancer",
        limit_per_source=3,
        sources=['biothings', 'kegg', 'opentargets']
    )
    
    print(output[:2000])
    
    # At least one source should have results
    import pandas as pd
    total_sources = 0
    for k, v in results.items():
        if isinstance(v, pd.DataFrame):
            if not v.empty:
                total_sources += 1
        elif isinstance(v, list):
            if len(v) > 0:
                total_sources += 1
        elif v:
            total_sources += 1
    assert total_sources > 0, "Should find results from at least one source"
    print(f"✓ Found results from {total_sources} sources")


def test_search_diseases_all_sources():
    """Test disease search with all sources (default)."""
    print("\n=== Test: All Sources Disease Search ===")
    
    results, output = search_diseases_unified(
        search_term="heart failure",
        limit_per_source=3
        # sources=None means all sources
    )
    
    print(output[:2000])
    
    print("✓ All sources disease search works!")


def test_search_diseases_save_results():
    """Test that disease search saves results to file."""
    print("\n=== Test: Save Search Results to File ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = os.path.join(tmpdir, "test_disease_search.json")
        
        results, output = search_diseases_unified(
            search_term="parkinson",
            limit_per_source=3,
            sources=['kegg'],
            save_path=save_path
        )
        
        assert os.path.exists(save_path), f"File should be created at {save_path}"
        
        with open(save_path, 'r') as f:
            saved_data = json.load(f)
        
        assert 'search_term' in saved_data, "Saved data should have search_term"
        assert 'results' in saved_data, "Saved data should have results"
        print(f"✓ Search results saved successfully to {save_path}")


def test_fetch_disease_kegg():
    """Test fetching disease details from KEGG."""
    print("\n=== Test: Fetch KEGG Disease Details ===")
    
    # KEGG Disease ID for Type 2 diabetes
    details, output = fetch_disease_details_unified(
        disease_id="H00409",
        id_type="kegg",
        sources=['kegg']
    )
    
    print(output[:2000])
    
    assert 'kegg' in details, "Should have KEGG details"
    print("✓ KEGG disease fetch works!")


def test_fetch_disease_opentargets():
    """Test fetching disease details from Open Targets."""
    print("\n=== Test: Fetch Open Targets Disease Details ===")
    
    details, output = fetch_disease_details_unified(
        disease_id="type 2 diabetes",
        id_type="name",
        sources=['opentargets']
    )
    
    print(output[:2000])
    
    # May or may not find results depending on search
    print("✓ Open Targets disease fetch completed!")


def test_fetch_disease_by_name():
    """Test fetching disease details by name."""
    print("\n=== Test: Fetch Disease by Name ===")
    
    details, output = fetch_disease_details_unified(
        disease_id="lung cancer",
        id_type="name",
        sources=['kegg', 'opentargets']
    )
    
    print(output[:2000])
    
    print("✓ Disease fetch by name works!")


def test_fetch_disease_mondo_id():
    """Test fetching disease details by MONDO ID."""
    print("\n=== Test: Fetch Disease by MONDO ID ===")
    
    # MONDO ID for diabetes mellitus
    details, output = fetch_disease_details_unified(
        disease_id="MONDO:0005015",
        id_type="mondo",
        sources=['biothings']
    )
    
    print(output[:2000])
    
    print("✓ MONDO ID fetch works!")


def test_fetch_disease_auto_detect():
    """Test auto-detection of disease ID type."""
    print("\n=== Test: Auto-Detect Disease ID Type ===")
    
    # KEGG ID (starts with H)
    details1, _ = fetch_disease_details_unified(
        disease_id="H00001",
        id_type=None,  # Auto-detect
        sources=['kegg']
    )
    print("✓ Auto-detected KEGG disease ID")
    
    # MONDO ID
    details2, _ = fetch_disease_details_unified(
        disease_id="MONDO:0005148",
        id_type=None,  # Auto-detect
        sources=['biothings']
    )
    print("✓ Auto-detected MONDO ID")


def test_fetch_disease_save_results():
    """Test that disease fetch saves results to file."""
    print("\n=== Test: Fetch and Save Results ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = os.path.join(tmpdir, "test_disease_details.json")
        
        details, output = fetch_disease_details_unified(
            disease_id="H00409",
            id_type="kegg",
            sources=['kegg'],
            save_path=save_path
        )
        
        assert os.path.exists(save_path), f"File should be created at {save_path}"
        
        with open(save_path, 'r') as f:
            saved_data = json.load(f)
        
        assert 'disease_id' in saved_data, "Saved data should have disease_id"
        assert 'details' in saved_data, "Saved data should have details"
        print(f"✓ Details saved successfully to {save_path}")


def test_aggregate_disease_names():
    """Test aggregating disease names from results."""
    print("\n=== Test: Aggregate Disease Names ===")
    
    results, _ = search_diseases_unified(
        search_term="hypertension",
        limit_per_source=5,
        sources=['kegg', 'opentargets']
    )
    
    names = aggregate_disease_names(results)
    
    print(f"Aggregated names ({len(names)}): {names[:5]}")
    
    assert isinstance(names, list), "Should return a list"
    print("✓ Aggregate disease names works!")


def test_aggregate_disease_identifiers():
    """Test aggregating disease identifiers from results."""
    print("\n=== Test: Aggregate Disease Identifiers ===")
    
    results, _ = search_diseases_unified(
        search_term="asthma",
        limit_per_source=3,
        sources=['kegg', 'opentargets']
    )
    
    identifiers = aggregate_disease_identifiers(results)
    
    print(f"Aggregated identifiers: {identifiers}")
    
    assert isinstance(identifiers, dict), "Should return a dict"
    print("✓ Aggregate disease identifiers works!")


def test_search_diseases_with_drugs():
    """Test disease search including ChEMBL drugs."""
    print("\n=== Test: Disease Search with ChEMBL Drugs ===")
    
    results, output = search_diseases_unified(
        search_term="rheumatoid arthritis",
        limit_per_source=3,
        sources=['kegg', 'chembl_drugs']
    )
    
    print(output[:2000])
    
    # ChEMBL drugs source may or may not return results
    print("✓ Disease search with drugs completed!")


if __name__ == "__main__":
    print("Running unified disease function tests...\n")
    print("="*80)
    
    try:
        test_search_diseases_kegg()
        print("\n" + "="*80)
        
        test_search_diseases_opentargets()
        print("\n" + "="*80)
        
        test_search_diseases_multiple_sources()
        print("\n" + "="*80)
        
        test_search_diseases_save_results()
        print("\n" + "="*80)
        
        test_fetch_disease_kegg()
        print("\n" + "="*80)
        
        test_fetch_disease_by_name()
        print("\n" + "="*80)
        
        test_fetch_disease_auto_detect()
        print("\n" + "="*80)
        
        test_fetch_disease_save_results()
        print("\n" + "="*80)
        
        test_aggregate_disease_names()
        print("\n" + "="*80)
        
        test_aggregate_disease_identifiers()
        print("\n" + "="*80)
        
        print("\n\n✅ All disease unified function tests passed successfully!")
        
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
