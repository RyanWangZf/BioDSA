import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from biodsa.tools.pubmed.pubtator_api import pubtator_api_fetch_paper_annotations, pubtator_api_search_papers

def test_pubtator_api_fetch_paper_annotations():
    pmids = ['34895069', '37608202', '35757715']
    results = pubtator_api_fetch_paper_annotations(pmids)
    print(results)

def test_pubtator_api_search_papers():
    # Test with a relation query
    text = "relations:treat|@CHEMICAL_Doxorubicin|@DISEASE_Neoplasms"
    results = pubtator_api_search_papers(text=text, page=1)
    print(results)

if __name__ == '__main__':
    print("Testing pubtator_api_fetch_paper_annotations...")
    # test_pubtator_api_fetch_paper_annotations()
    # print("\n" + "="*50 + "\n")
    # print("Testing pubtator_api_search_papers...")
    test_pubtator_api_search_papers()