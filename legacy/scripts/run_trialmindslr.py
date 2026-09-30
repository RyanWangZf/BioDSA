import sys
import os
current_dir = os.getcwd()
REPO_BASE_DIR = os.path.dirname(os.path.abspath(current_dir))
sys.path.append(REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))

from biodsa.agents.trialmind_slr import TrialMindSLRAgent

agent = TrialMindSLRAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    max_search_results=10,  # Limit search results for quick demo
)

research_question = """
What is the efficacy and safety of CAR-T cell therapy
in patients with relapsed/refractory B-cell lymphoma?
"""

target_outcomes = [
    "overall_response_rate",
    "complete_response_rate",
    "overall_survival",
    "cytokine_release_syndrome"
]

result = agent.go(
    research_question=research_question,
    target_outcomes=target_outcomes
)

print(result.final_report)
