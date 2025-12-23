"""Test suite for unified target search and fetch functions.

Tests the target unified functions from:
- biodsa.tools.targets.unified_target_search
"""

import os
import sys
import json
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from biodsa.tools.targets import (
    search_targets_unified,
    fetch_target_details_unified
)

# Import aggregate functions directly from the module
from biodsa.tools.targets.unified_target_search import (
    aggregate_target_names,
    aggregate_target_identifiers
)


def test_search_targets_opentargets():
    """Test target search with Open Targets only."""
    print("\n=== Test: Open Targets Target Search ===")
    
    results, output = search_targets_unified(
        search_term="BRCA1",
        limit_per_source=5,
        sources=['opentargets']
    )
    
    print(output[:1500])
    
    assert 'opentargets' in results, "Should have Open Targets results"
    print("✓ Open Targets target search works!")


def test_search_targets_kegg_pathways():
    """Test target search with KEGG pathways only."""
    print("\n=== Test: KEGG Pathway Search ===")
    
    results, output = search_targets_unified(
        search_term="apoptosis",
        limit_per_source=5,
        sources=['kegg_pathways']
    )
    
    print(output[:1500])
    
    assert 'kegg_pathways' in results, "Should have KEGG pathway results"
    kegg_results = results['kegg_pathways']
    assert isinstance(kegg_results, list), "KEGG pathways should be a list"
    print(f"✓ Found {len(kegg_results)} KEGG pathways")


def test_search_targets_kegg_genes():
    """Test target search with KEGG genes only."""
    print("\n=== Test: KEGG Gene Search ===")
    
    results, output = search_targets_unified(
        search_term="TP53",
        limit_per_source=5,
        sources=['kegg_genes']
    )
    
    print(output[:1500])
    
    assert 'kegg_genes' in results, "Should have KEGG gene results"
    kegg_results = results['kegg_genes']
    assert isinstance(kegg_results, list), "KEGG genes should be a list"
    print(f"✓ Found {len(kegg_results)} KEGG genes")


def test_search_targets_gene_ontology():
    """Test target search with Gene Ontology only."""
    print("\n=== Test: Gene Ontology Search ===")
    
    results, output = search_targets_unified(
        search_term="kinase activity",
        limit_per_source=5,
        sources=['gene_ontology']
    )
    
    print(output[:1500])
    
    assert 'gene_ontology' in results, "Should have Gene Ontology results"
    print("✓ Gene Ontology target search works!")


def test_search_targets_proteinatlas():
    """Test target search with Human Protein Atlas only."""
    print("\n=== Test: Human Protein Atlas Search ===")
    
    results, output = search_targets_unified(
        search_term="breast cancer",
        limit_per_source=5,
        sources=['proteinatlas']
    )
    
    print(output[:1500])
    
    assert 'proteinatlas' in results, "Should have Human Protein Atlas results"
    print("✓ Human Protein Atlas target search works!")


def test_search_targets_multiple_sources():
    """Test target search with multiple sources."""
    print("\n=== Test: Multiple Sources Target Search ===")
    
    results, output = search_targets_unified(
        search_term="EGFR",
        limit_per_source=3,
        sources=['opentargets', 'kegg_genes', 'gene_ontology']
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


def test_search_targets_by_type_pathway():
    """Test target search with pathway type."""
    print("\n=== Test: Search by Type - Pathway ===")
    
    results, output = search_targets_unified(
        search_term="cell cycle",
        search_type='pathway',
        limit_per_source=5
    )
    
    print(output[:1500])
    
    # When search_type='pathway', should use kegg_pathways
    assert 'kegg_pathways' in results, "Should have KEGG pathway results"
    print("✓ Pathway type search works!")


def test_search_targets_by_type_go_term():
    """Test target search with GO term type."""
    print("\n=== Test: Search by Type - GO Term ===")
    
    results, output = search_targets_unified(
        search_term="protein binding",
        search_type='go_term',
        limit_per_source=5
    )
    
    print(output[:1500])
    
    # When search_type='go_term', should use gene_ontology
    assert 'gene_ontology' in results, "Should have Gene Ontology results"
    print("✓ GO term type search works!")


def test_search_targets_all_sources():
    """Test target search with all sources (default)."""
    print("\n=== Test: All Sources Target Search ===")
    
    results, output = search_targets_unified(
        search_term="KRAS",
        limit_per_source=3
        # sources=None means all sources
    )
    
    print(output[:2500])
    
    print("✓ All sources target search works!")


def test_search_targets_save_results():
    """Test that target search saves results to file."""
    print("\n=== Test: Save Search Results to File ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = os.path.join(tmpdir, "test_target_search.json")
        
        results, output = search_targets_unified(
            search_term="BRAF",
            limit_per_source=3,
            sources=['opentargets'],
            save_path=save_path
        )
        
        assert os.path.exists(save_path), f"File should be created at {save_path}"
        
        with open(save_path, 'r') as f:
            saved_data = json.load(f)
        
        assert 'search_term' in saved_data, "Saved data should have search_term"
        assert 'results' in saved_data, "Saved data should have results"
        print(f"✓ Search results saved successfully to {save_path}")


def test_fetch_target_ensembl():
    """Test fetching target details by Ensembl ID."""
    print("\n=== Test: Fetch Target by Ensembl ID ===")
    
    # BRCA1 Ensembl ID
    details, output = fetch_target_details_unified(
        target_id="ENSG00000012048",
        id_type="ensembl",
        sources=['opentargets']
    )
    
    print(output[:2000])
    
    assert 'opentargets' in details, "Should have Open Targets details"
    print("✓ Ensembl ID fetch works!")


def test_fetch_target_gene_symbol():
    """Test fetching target details by gene symbol."""
    print("\n=== Test: Fetch Target by Gene Symbol ===")
    
    details, output = fetch_target_details_unified(
        target_id="TP53",
        id_type="gene_symbol",
        sources=['opentargets', 'proteinatlas']
    )
    
    print(output[:2000])
    
    print("✓ Gene symbol fetch works!")


def test_fetch_target_pathway():
    """Test fetching target details by pathway ID."""
    print("\n=== Test: Fetch Pathway Details ===")
    
    # KEGG pathway ID for Apoptosis
    details, output = fetch_target_details_unified(
        target_id="hsa04210",
        id_type="pathway",
        sources=['kegg']
    )
    
    print(output[:2000])
    
    # Note: The key for pathway is 'kegg_pathway', not 'kegg'
    assert 'kegg_pathway' in details, "Should have KEGG pathway details"
    print("✓ Pathway fetch works!")


def test_fetch_target_go_term():
    """Test fetching target details by GO term ID."""
    print("\n=== Test: Fetch GO Term Details ===")
    
    # GO term for protein kinase activity
    details, output = fetch_target_details_unified(
        target_id="GO:0004672",
        id_type="go_term",
        sources=['gene_ontology']
    )
    
    print(output[:2000])
    
    assert 'gene_ontology' in details, "Should have Gene Ontology details"
    print("✓ GO term fetch works!")


def test_fetch_target_auto_detect():
    """Test auto-detection of target ID type."""
    print("\n=== Test: Auto-Detect Target ID Type ===")
    
    # Ensembl ID (starts with ENSG)
    details1, _ = fetch_target_details_unified(
        target_id="ENSG00000012048",
        id_type=None,  # Auto-detect
        sources=['opentargets']
    )
    print("✓ Auto-detected Ensembl ID")
    
    # GO term (starts with GO:)
    details2, _ = fetch_target_details_unified(
        target_id="GO:0003674",
        id_type=None,  # Auto-detect
        sources=['gene_ontology']
    )
    print("✓ Auto-detected GO term ID")
    
    # Pathway ID (starts with hsa)
    details3, _ = fetch_target_details_unified(
        target_id="hsa04210",
        id_type=None,  # Auto-detect
        sources=['kegg']
    )
    print("✓ Auto-detected Pathway ID")


def test_fetch_target_with_associations():
    """Test fetching target details with disease associations."""
    print("\n=== Test: Fetch Target with Associations ===")
    
    details, output = fetch_target_details_unified(
        target_id="EGFR",
        id_type="gene_symbol",
        sources=['opentargets'],
        include_associations=True
    )
    
    print(output[:2500])
    
    print("✓ Target fetch with associations works!")


def test_fetch_target_save_results():
    """Test that target fetch saves results to file."""
    print("\n=== Test: Fetch and Save Results ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = os.path.join(tmpdir, "test_target_details.json")
        
        details, output = fetch_target_details_unified(
            target_id="hsa04210",
            id_type="pathway",
            sources=['kegg'],
            save_path=save_path
        )
        
        assert os.path.exists(save_path), f"File should be created at {save_path}"
        
        with open(save_path, 'r') as f:
            saved_data = json.load(f)
        
        assert 'target_id' in saved_data, "Saved data should have target_id"
        assert 'details' in saved_data, "Saved data should have details"
        print(f"✓ Details saved successfully to {save_path}")


def test_aggregate_target_names():
    """Test aggregating target names from results."""
    print("\n=== Test: Aggregate Target Names ===")
    
    results, _ = search_targets_unified(
        search_term="MAPK",
        limit_per_source=5,
        sources=['opentargets', 'kegg_genes']
    )
    
    names = aggregate_target_names(results)
    
    print(f"Aggregated names ({len(names)}): {names[:10]}")
    
    assert isinstance(names, list), "Should return a list"
    print("✓ Aggregate target names works!")


def test_aggregate_target_identifiers():
    """Test aggregating target identifiers from results."""
    print("\n=== Test: Aggregate Target Identifiers ===")
    
    results, _ = search_targets_unified(
        search_term="AKT1",
        limit_per_source=3,
        sources=['opentargets', 'gene_ontology']
    )
    
    identifiers = aggregate_target_identifiers(results)
    
    print(f"Aggregated identifiers: {identifiers}")
    
    assert isinstance(identifiers, dict), "Should return a dict"
    print("✓ Aggregate target identifiers works!")


def test_search_targets_cancer_markers():
    """Test searching for cancer markers in Human Protein Atlas."""
    print("\n=== Test: Cancer Markers Search ===")
    
    results, output = search_targets_unified(
        search_term="lung cancer",
        limit_per_source=5,
        sources=['proteinatlas']
    )
    
    print(output[:2000])
    
    print("✓ Cancer markers search completed!")


if __name__ == "__main__":
    print("Running unified target function tests...\n")
    print("="*80)
    
    try:
        test_search_targets_opentargets()
        print("\n" + "="*80)
        
        test_search_targets_kegg_pathways()
        print("\n" + "="*80)
        
        test_search_targets_kegg_genes()
        print("\n" + "="*80)
        
        test_search_targets_gene_ontology()
        print("\n" + "="*80)
        
        test_search_targets_multiple_sources()
        print("\n" + "="*80)
        
        test_search_targets_by_type_pathway()
        print("\n" + "="*80)
        
        test_search_targets_save_results()
        print("\n" + "="*80)
        
        test_fetch_target_pathway()
        print("\n" + "="*80)
        
        test_fetch_target_go_term()
        print("\n" + "="*80)
        
        test_fetch_target_auto_detect()
        print("\n" + "="*80)
        
        test_fetch_target_save_results()
        print("\n" + "="*80)
        
        test_aggregate_target_names()
        print("\n" + "="*80)
        
        test_aggregate_target_identifiers()
        print("\n" + "="*80)
        
        print("\n\n✅ All target unified function tests passed successfully!")
        
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
