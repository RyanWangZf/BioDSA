import sys
import os
REPO_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))

from biodsa.agents import CoderAgent
agent = CoderAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)
agent.register_workspace(
    os.path.join(REPO_BASE_DIR, "biomedical_data/cBioPortal/datasets/acbc_mskcc_2015")
)
execution_results = agent.go("Make bar plot showing the distribution samples per table and save it to a png file")

# Display execution results
print(execution_results)

# Download artifacts separately
artifacts = execution_results.download_artifacts(output_dir="test_artifacts")
print(f"\nDownloaded {len(artifacts)} artifacts: {artifacts}")

# Generate PDF report following the structured format:
# 1. User query
# 2. Agent exploration trajectories (messages only, no code)
# 3. Final response with embedded artifacts
# 4. Supplementary materials with code blocks and execution results
pdf_path = execution_results.to_pdf(output_dir="test_artifacts")
print(f"\nPDF report generated: {pdf_path}")

# Cleanup
agent.clear_workspace()
