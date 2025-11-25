#!/usr/bin/env python3
"""Test script for unified biological target search functionality."""

import sys
sys.path.insert(0, '/Users/zifeng/Documents/github/BioDSA-dev')

from biodsa.tools.targets import search_targets_unified, fetch_target_details_unified

def test_target_search():
    """Test unified target search with different search types."""
    print("=" * 80)
    print("TEST 1: Search for BRCA1 target across all sources")
    print("=" * 80)
    results, output = search_targets_unified(
        "BRCA1",
        limit_per_source=5
    )
    print(output)
    print("\n")
    
    print("=" * 80)
    print("TEST 2: Search for apoptosis pathways")
    print("=" * 80)
    results, output = search_targets_unified(
        "apoptosis",
        search_type='pathway',
        limit_per_source=5
    )
    print(output)
    print("\n")
    
    print("=" * 80)
    print("TEST 3: Search for protein kinase activity (GO term)")
    print("=" * 80)
    results, output = search_targets_unified(
        "protein kinase activity",
        search_type='go_term',
        limit_per_source=5
    )
    print(output)
    print("\n")


def test_target_fetch():
    """Test fetching target details with different ID types."""
    print("=" * 80)
    print("TEST 4: Fetch target details by gene symbol (TP53)")
    print("=" * 80)
    details, output = fetch_target_details_unified(
        "TP53",
        id_type='gene_symbol',
        include_associations=True
    )
    print(output)
    print("\n")
    
    print("=" * 80)
    print("TEST 5: Fetch pathway details (MAPK signaling)")
    print("=" * 80)
    details, output = fetch_target_details_unified(
        "hsa04010",  # MAPK signaling pathway
        id_type='pathway'
    )
    print(output)
    print("\n")
    
    print("=" * 80)
    print("TEST 6: Fetch GO term details (protein kinase activity)")
    print("=" * 80)
    details, output = fetch_target_details_unified(
        "GO:0004672",
        id_type='go_term'
    )
    print(output)
    print("\n")


def test_multi_source_search():
    """Test searching specific sources."""
    print("=" * 80)
    print("TEST 7: Search EGFR in Open Targets and KEGG pathways only")
    print("=" * 80)
    results, output = search_targets_unified(
        "EGFR",
        sources=['opentargets', 'kegg_pathways'],
        limit_per_source=3
    )
    print(output)
    print("\n")


def test_with_save():
    """Test saving results to file."""
    print("=" * 80)
    print("TEST 8: Search and save results to file")
    print("=" * 80)
    results, output = search_targets_unified(
        "kinase",
        limit_per_source=3,
        save_path="workdir/kinase_search.json"
    )
    print(output)
    print("\n")


def test_cancer_marker_search():
    """Test cancer marker search from Human Protein Atlas."""
    print("=" * 80)
    print("TEST 9: Search for breast cancer markers")
    print("=" * 80)
    results, output = search_targets_unified(
        "breast cancer",
        limit_per_source=5
    )
    print(output)
    print("\n")
    
    print("=" * 80)
    print("TEST 10: Search for proteins with proteinatlas only")
    print("=" * 80)
    results, output = search_targets_unified(
        "BRCA1",
        sources=['proteinatlas'],
        limit_per_source=5
    )
    print(output)
    print("\n")


def test_proteinatlas_fetch():
    """Test fetching protein details from Human Protein Atlas."""
    print("=" * 80)
    print("TEST 11: Fetch protein details including pathology (TP53)")
    print("=" * 80)
    details, output = fetch_target_details_unified(
        "TP53",
        id_type='gene_symbol',
        sources=['proteinatlas']
    )
    print(output)
    print("\n")


if __name__ == "__main__":
    print("\n")
    print("*" * 80)
    print("UNIFIED BIOLOGICAL TARGET SEARCH - TEST SUITE")
    print("*" * 80)
    print("\n")
    
    try:
        # Run target search tests
        test_target_search()
        
        # Run target fetch tests
        test_target_fetch()
        
        # Run multi-source search test
        test_multi_source_search()
        
        # Run save test
        test_with_save()
        
        # Run cancer marker search tests
        test_cancer_marker_search()
        
        # Run proteinatlas fetch test
        test_proteinatlas_fetch()
        
        print("\n")
        print("*" * 80)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("*" * 80)
        print("\n")
        
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

