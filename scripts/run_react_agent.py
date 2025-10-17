import sys
import os
REPO_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))

from biodsa.agents import ReactAgent
agent = ReactAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)
agent.register_dataset(
    os.path.join(REPO_BASE_DIR, "biomedical_data/cBioPortal/datasets/acbc_mskcc_2015")
)
execution_results = agent.go("Make bar plot showing the distribution samples per table and save it to a png file")
print(execution_results)
print(execution_results.download_artifacts(output_dir="test_artifacts"))
agent.clear_workspace()

