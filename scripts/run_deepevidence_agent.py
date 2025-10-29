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
# execution_results = agent.go(
# """
# Can you evaluate the effectiveness and safety of Palazestrant (OP-1250) for treating ER+/HER2- Metastatic Breast Cancer?
# What is the success rate of this drug will pass clinical trials and get approved by the FDA?
# """,
#     knowledge_bases=["pubmed_papers"],
# )
# execution_results = agent.go(
# """
# Your task is to identify the most promising variant associated wtih a given GWAS phenotype for futher examination. \nFrom the list, prioritize the top associated variant (matching one of the given variant). \nGWAS phenotype: Bradykinin\nVariants: rs7700133, rs1280, rs7651090, rs4253311, rs3738934, rs7385804, rs1367117, rs4808136, rs10087900, rs855791, rs12678919\n'
# """,
#     knowledge_bases=["pubmed_papers"],
# )

execution_results = agent.go(
"""
The following is a multiple choice question about biology.
Please answer by responding with the letter of the correct answer.

Question: Which of the following genes is most likely contained in the gene set CAHOY_NEURONAL, which contains genes up-regulated in neurons. This gene set is a part of the C6 collection: oncogenic signature gene sets.
A.RASL10A
B.Insufficient information to answer the question.
C.EVI2B
D.TCAF1
E.KIR3DL3
""",
    knowledge_bases=["gene_set"],
)
print(execution_results)
execution_results.to_pdf(output_dir="test_artifacts")