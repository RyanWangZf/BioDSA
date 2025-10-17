import os
import sys
REPO_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))

from biodsa.agents import DSWizardAgent
agent = DSWizardAgent(
    model_name="gpt-5",
    small_model_name="gpt-5-mini",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)
agent.register_dataset(
    os.path.join(REPO_BASE_DIR, "biomedical_data/cBioPortal/datasets/acbc_mskcc_2015")
)
execution_results = agent.go("Make a clustering of the patients based on their genomic mutation data to maximize the separation of the prognostic survival outcomes.")
print(execution_results)
print(execution_results.download_artifacts(output_dir="test_artifacts"))
print(execution_results.to_pdf(output_dir="test_artifacts"))
agent.clear_workspace()