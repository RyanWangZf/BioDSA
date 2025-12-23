"""
Test script for pubtator_api_search_papers function.

This script tests the PubTator3 API search functionality with various query types.
"""

import sys
import os
import pandas as pd

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from biodsa.tools.pubmed.pubtator_api import pubtator_api_search_papers


def test_simple_entity_query():
    """Test a simple single entity query."""
    print("\n" + "="*80)
    print("TEST 1: Simple Entity Query")
    print("="*80)
    
    query = "@CHEMICAL_remdesivir"
    print(f"Query: {query}")
    
    results = pubtator_api_search_papers(
        boolean_query_text=query,
        page=1,
        max_retries=3,
        max_requests_per_second=3.0
    )
    
    if results is not None and isinstance(results, pd.DataFrame):
        print(f"✓ Found {len(results)} papers")
        print(f"Columns: {list(results.columns)}")
        print("\nFirst result:")
        if len(results) > 0:
            print(f"  PMID: {results.iloc[0]['PMID']}")
            print(f"  Title: {results.iloc[0]['Title'][:100]}...")
    else:
        print("✗ No results found")
    
    return results


def test_boolean_and_query():
    """Test boolean query with AND operator."""
    print("\n" + "="*80)
    print("TEST 2: Boolean AND Query")
    print("="*80)
    
    query = "@CHEMICAL_Doxorubicin AND @DISEASE_Neoplasms"
    print(f"Query: {query}")
    
    results = pubtator_api_search_papers(
        boolean_query_text=query,
        page=1,
        max_retries=3,
        max_requests_per_second=3.0
    )
    
    if results is not None and isinstance(results, pd.DataFrame):
        print(f"✓ Found {len(results)} papers")
        print("\nSample titles:")
        for idx, row in results.head(3).iterrows():
            print(f"  {idx+1}. {row['Title'][:80]}...")
    else:
        print("✗ No results found")
    
    return results


def test_complex_boolean_query():
    """Test complex boolean query with OR and parentheses."""
    print("\n" + "="*80)
    print("TEST 3: Complex Boolean Query")
    print("="*80)
    
    query = "(@DISEASE_COVID_19 AND complications) OR @DISEASE_Post_Acute_COVID_19_Syndrome"
    print(f"Query: {query}")
    
    results = pubtator_api_search_papers(
        boolean_query_text=query,
        page=1,
        max_retries=3,
        max_requests_per_second=3.0
    )
    
    if results is not None and isinstance(results, pd.DataFrame):
        print(f"✓ Found {len(results)} papers")
        print(f"DataFrame shape: {results.shape}")
    else:
        print("✗ No results found")
    
    return results


def test_mixed_entity_keyword_query():
    """Test query mixing entities with free-text keywords."""
    print("\n" + "="*80)
    print("TEST 4: Mixed Entity and Keyword Query")
    print("="*80)
    
    query = "@CHEMICAL_remdesivir AND (efficacy OR effectiveness)"
    print(f"Query: {query}")
    
    results = pubtator_api_search_papers(
        boolean_query_text=query,
        page=1,
        max_retries=3,
        max_requests_per_second=3.0
    )
    
    if results is not None and isinstance(results, pd.DataFrame):
        print(f"✓ Found {len(results)} papers")
        print("\nSample highlighted text:")
        for idx, row in results.head(2).iterrows():
            highlight = row.get('Highlighted_Text', '')
            if highlight:
                print(f"  {idx+1}. {highlight[:100]}...")
    else:
        print("✗ No results found")
    
    return results


def test_relation_treat_query():
    """Test relation-based query: TREAT relationship."""
    print("\n" + "="*80)
    print("TEST 5: Relation Query - TREAT")
    print("="*80)
    
    relation_query = {
        'relation_type': 'TREAT',
        'entity1': '@CHEMICAL_Doxorubicin',
        'entity2': '@DISEASE_Neoplasms'
    }
    print(f"Relation Query: {relation_query}")
    
    results = pubtator_api_search_papers(
        relation_query=relation_query,
        page=1,
        max_retries=3,
        max_requests_per_second=3.0
    )
    
    if results is not None and isinstance(results, pd.DataFrame):
        print(f"✓ Found {len(results)} papers")
        print("\nSample results:")
        for idx, row in results.head(3).iterrows():
            print(f"  {idx+1}. PMID: {row['PMID']} - {row['Title'][:60]}...")
    else:
        print("✗ No results found")
    
    return results


def test_relation_with_entity_type():
    """Test relation query with entity ID and entity type."""
    print("\n" + "="*80)
    print("TEST 6: Relation Query - Entity ID + Entity Type")
    print("="*80)
    
    relation_query = {
        'relation_type': 'ANY',
        'entity1': '@CHEMICAL_remdesivir',
        'entity2': 'DISEASE'
    }
    print(f"Relation Query: {relation_query}")
    
    results = pubtator_api_search_papers(
        relation_query=relation_query,
        page=1,
        max_retries=3,
        max_requests_per_second=3.0
    )
    
    if results is not None and isinstance(results, pd.DataFrame):
        print(f"✓ Found {len(results)} papers")
        print(f"Unique diseases mentioned: {len(results)} papers found")
    else:
        print("✗ No results found")
    
    return results


def test_relation_interact_query():
    """Test relation query with INTERACT relationship."""
    print("\n" + "="*80)
    print("TEST 7: Relation Query - INTERACT (Gene-Chemical)")
    print("="*80)
    
    relation_query = {
        'relation_type': 'INTERACT',
        'entity1': 'GENE',
        'entity2': 'CHEMICAL'
    }
    print(f"Relation Query: {relation_query}")
    
    results = pubtator_api_search_papers(
        relation_query=relation_query,
        page=1,
        max_retries=3,
        max_requests_per_second=3.0
    )
    
    if results is not None and isinstance(results, pd.DataFrame):
        print(f"✓ Found {len(results)} papers")
        print("\nColumns in result:")
        for col in results.columns:
            print(f"  - {col}")
    else:
        print("✗ No results found")
    
    return results


def test_pagination():
    """Test pagination functionality."""
    print("\n" + "="*80)
    print("TEST 8: Pagination Test")
    print("="*80)
    
    query = "@DISEASE_COVID_19"
    print(f"Query: {query}")
    print("Fetching page 1 and page 2...")
    
    page1 = pubtator_api_search_papers(
        boolean_query_text=query,
        page=1,
        max_retries=3,
        max_requests_per_second=3.0
    )
    
    page2 = pubtator_api_search_papers(
        boolean_query_text=query,
        page=2,
        max_retries=3,
        max_requests_per_second=3.0
    )
    
    if page1 is not None and page2 is not None:
        print(f"✓ Page 1: {len(page1)} papers")
        print(f"✓ Page 2: {len(page2)} papers")
        
        # Check if pages are different
        if len(page1) > 0 and len(page2) > 0:
            page1_pmids = set(page1['PMID'].tolist())
            page2_pmids = set(page2['PMID'].tolist())
            overlap = page1_pmids.intersection(page2_pmids)
            if len(overlap) == 0:
                print("✓ No overlap between pages (correct pagination)")
            else:
                print(f"⚠ {len(overlap)} PMIDs overlap between pages")
    else:
        print("✗ Failed to fetch pages")
    
    return page1, page2


def test_multiple_drugs_query():
    """Test query with multiple drugs."""
    print("\n" + "="*80)
    print("TEST 9: Multiple Drugs Query")
    print("="*80)
    
    query = "(@CHEMICAL_Doxorubicin OR @CHEMICAL_Cisplatin) AND @DISEASE_Neoplasms"
    print(f"Query: {query}")
    
    results = pubtator_api_search_papers(
        boolean_query_text=query,
        page=1,
        max_retries=3,
        max_requests_per_second=3.0
    )
    
    if results is not None and isinstance(results, pd.DataFrame):
        print(f"✓ Found {len(results)} papers")
        print("\nJournals represented:")
        if 'Journal' in results.columns:
            journals = results['Journal'].value_counts().head(5)
            for journal, count in journals.items():
                print(f"  - {journal}: {count} papers")
    else:
        print("✗ No results found")
    
    return results


def test_error_handling():
    """Test error handling with invalid queries."""
    print("\n" + "="*80)
    print("TEST 10: Error Handling")
    print("="*80)
    
    # Test 1: Both boolean and relation query (should fail)
    print("\nTest 10a: Both boolean and relation query...")
    try:
        results = pubtator_api_search_papers(
            boolean_query_text="@CHEMICAL_remdesivir",
            relation_query={'relation_type': 'TREAT', 'entity1': '@CHEMICAL_remdesivir', 'entity2': 'DISEASE'},
            page=1
        )
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {str(e)[:80]}")
    
    # Test 2: Neither boolean nor relation query (should fail)
    print("\nTest 10b: Neither boolean nor relation query...")
    try:
        results = pubtator_api_search_papers(page=1)
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {str(e)[:80]}")
    
    # Test 3: Invalid relation type
    print("\nTest 10c: Invalid relation type...")
    try:
        results = pubtator_api_search_papers(
            relation_query={'relation_type': 'INVALID', 'entity1': 'GENE', 'entity2': 'DISEASE'},
            page=1
        )
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {str(e)[:80]}")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("PUBTATOR API SEARCH PAPERS - TEST SUITE")
    print("="*80)
    
    tests = [
        ("Simple Entity Query", test_simple_entity_query),
        ("Boolean AND Query", test_boolean_and_query),
        ("Complex Boolean Query", test_complex_boolean_query),
        ("Mixed Entity/Keyword Query", test_mixed_entity_keyword_query),
        ("Relation TREAT Query", test_relation_treat_query),
        ("Relation with Entity Type", test_relation_with_entity_type),
        ("Relation INTERACT Query", test_relation_interact_query),
        ("Pagination", test_pagination),
        ("Multiple Drugs Query", test_multiple_drugs_query),
        ("Error Handling", test_error_handling),
    ]
    
    results = {}
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            passed += 1
        except Exception as e:
            print(f"\n✗ TEST FAILED: {test_name}")
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✓ All tests passed!")
    else:
        print(f"\n⚠ {failed} test(s) failed")
    
    return results


if __name__ == "__main__":
    results = main()

