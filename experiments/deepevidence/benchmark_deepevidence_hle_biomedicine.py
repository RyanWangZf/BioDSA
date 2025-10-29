import os
import sys
import json
REPO_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))

from tqdm import tqdm
import pandas as pd
from biodsa.agents import DeepEvidenceAgent
agent = DeepEvidenceAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)
# register a workspace for the agent to use
agent.register_workspace()

question_template = """
{question}

# Rules
Make sure to answer the question by exploring the given knowledge bases.
If necessary, you should also try to write code to do data analysis or meta-analysis to answer the question.
If the quesiton is open-ended, e.g., each option itself is an independent question, you should explore and try to check the correctness of each option separately.

# Output format
Your final output should provide the final answer wrapped in <Answer> </Answer> tag, e.g., <Answer> <the letter of the correct answer> </Answer>, which will be used to extract the answer for evaluation.
"""


# load the benchmark questions
df = pd.read_csv(os.path.join(REPO_BASE_DIR, "benchmarks/HLE-biomedicine/hle_biomedicine_40.csv"))

# correct ones
# 2, 3, 6, 8, 12, 21, 25, 31, 37

# biomni: gets 9 qustions out of 52 done, 17.3% accuracy

RESULTS_DIR = os.path.join(REPO_BASE_DIR, "experiments/deepevidence/results/deepevidence/hle_biomedicine_40")
os.makedirs(RESULTS_DIR, exist_ok=True)

to_process_indices = [
    i for i in range(11, len(df))
]

for index, row in tqdm(df.iterrows(), desc="Processing questions", total=len(df)):
    if index not in to_process_indices:
        continue
    row = row.to_dict()
    question = row['question']
    question_prompt = question_template.format(question=question)
    execution_results = agent.go(question_prompt, knowledge_bases=["pubmed_papers", "gene_set"])
    outputs = execution_results.to_json()
    outputs = {
        "outputs": outputs,
    }
    outputs.update(row)
    with open(os.path.join(RESULTS_DIR, f"hle_biomedicine_40_{index}.json"), 'w') as f:
        json.dump(outputs, f, indent=4)
    print(outputs["answer"])
    print(outputs["outputs"]["final_response"])
    print("-" * 100)