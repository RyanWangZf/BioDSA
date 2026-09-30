import sys
import os
current_dir = os.getcwd()
REPO_BASE_DIR = os.path.dirname(os.path.abspath(current_dir))
sys.path.append(REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))


from biodsa.agents.trialgpt import TrialGPTAgent

agent = TrialGPTAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

patient_note = """
58-year-old female with metastatic NSCLC (adenocarcinoma).
EGFR mutation positive (exon 19 deletion).
Previously treated with erlotinib with progression after 14 months.
ECOG PS 1. No brain metastases.
"""

results = agent.go(patient_note)
print(results["full_response"])
