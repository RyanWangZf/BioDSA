import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from biodsa.tools.pubmed.pubmed_api import pubmed_api_get_paper_references

def test_pubmed_api_get_paper_references():
    pmids = ['35757715', '37608202']
    results = pubmed_api_get_paper_references(pmids)
    print(results)

if __name__ == '__main__':
    test_pubmed_api_get_paper_references()