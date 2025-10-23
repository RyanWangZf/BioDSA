import os
import sys
REPO_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))

from biodsa.agents import DeepEvidenceAgent
agent = DeepEvidenceAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)
# register a workspace for the agent to use
agent.register_workspace()
execution_results = agent.go(
    """
Can you evaluate the effectiveness and safety of Palazestrant (OP-1250) for treating ER+/HER2- Metastatic Breast Cancer?
What is the success rate of this drug will pass clinical trials and get approved by the FDA?
""",
    knowledge_bases=["pubmed_papers"],
)
print(execution_results)
execution_results.to_pdf(output_dir="test_artifacts")