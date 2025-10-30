import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from biodsa.tools.pubmed.pubtator_api import (
    pubtator_api_fetch_paper_annotations,
    pubtator_api_search_papers,
    pubtator_api_find_entities
)

def test_pubtator_api_fetch_paper_annotations():
    pmids = ['34895069', '37608202', '35757715']
    results = pubtator_api_fetch_paper_annotations(pmids)
    print(results)

def test_pubtator_api_search_papers():
    # Test with a boolean query
    boolean_query_text = "@CHEMICAL_Doxorubicin AND @DISEASE_Neoplasms"
    results = pubtator_api_search_papers(boolean_query_text=boolean_query_text, page=1)
    print("Boolean query results:")
    print(results)
    print("="*70)

    results = pubtator_api_search_papers(relation_query={
        'relation_type': 'TREAT',
        'entity1': '@CHEMICAL_Doxorubicin',
        'entity2': 'DISEASE'
    }, page=1)
    print("Relation query results:")
    print(results)

def test_pubtator_api_find_entities():
    query_text = "Doxorubicin"
    results = pubtator_api_find_entities(query_text=query_text, concept_type=None, limit=10)
    print("Find entities results:")
    print(results)

if __name__ == '__main__':
    print("Testing pubtator_api_fetch_paper_annotations...")
    test_pubtator_api_fetch_paper_annotations()
    print("\n" + "="*50 + "\n")
    print("Testing pubtator_api_search_papers...")
    test_pubtator_api_search_papers()
    print("\n" + "="*50 + "\n")
    print("Testing pubtator_api_find_entities...")
    test_pubtator_api_find_entities()
    print("\n" + "="*50 + "\n")
    print("All tests completed!")
    print("="*50)