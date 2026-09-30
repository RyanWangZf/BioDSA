import sys
import os
current_dir = os.getcwd()
REPO_BASE_DIR = os.path.dirname(os.path.abspath(current_dir))
sys.path.append(REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))


from biodsa.agents.geneagent import GeneAgent

agent = GeneAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    # Quick demo settings (comment out for full verification)
    max_claims_per_stage=2,      # Limit to 2 claims per stage (default: None = all)
    max_verification_rounds=3,   # Limit tool calls per claim (default: 20)
)

# Example gene set from the original GeneAgent paper (MAPK signaling pathway genes)
gene_set = "ERBB2,ERBB4,FGFR2,FGFR4,HRAS,KRAS"

results = agent.go(gene_set)
print(results.final_response)
