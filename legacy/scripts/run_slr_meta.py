"""
Run script for the SLR-Meta agent (systematic literature review + meta-analysis
using PubMed and ClinicalTrials.gov).
"""
import sys
import os

REPO_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))

from biodsa.agents.slr_meta import SLRMetaAgent

agent = SLRMetaAgent(
    model_name="gpt-4o",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    max_search_results=10,   # Keep low for quick demo
    max_ctgov_results=10,
)

research_question = """
What is the efficacy and safety of CAR-T cell therapy
in patients with relapsed/refractory B-cell lymphoma?
"""

target_outcomes = [
    "overall_response_rate",
    "complete_response_rate",
    "overall_survival",
    "cytokine_release_syndrome",
]

result = agent.go(
    research_question=research_question,
    target_outcomes=target_outcomes,
)

print(result.final_report)
print("\n--- Summary ---")
print(f"PubMed studies identified: {result.identified_pubmed}")
print(f"CT.gov trials identified: {result.identified_ctgov}")
print(f"Included for synthesis: {result.included_studies}")
