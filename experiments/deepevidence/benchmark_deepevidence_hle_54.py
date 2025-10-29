import os
import sys
import json
REPO_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(REPO_BASE_DIR)
RESULTS_DIR = os.path.join(REPO_BASE_DIR, "experiments/deepevidence/results/deepevidence")
os.makedirs(RESULTS_DIR, exist_ok=True)
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

Make sure to answer the question by exploring the given knowledge bases.
If necessary, you should also try to write code to do data analysis or meta-analysis to answer the question.
Make sure provide your final answer in the format of <Answer> <letter of the correct answer> </Answer>, which will be used to extract the answer for evaluation.
"""

# load the benchmark questions
df = pd.read_csv(os.path.join(REPO_BASE_DIR, "benchmarks/HLE-biomedicine/hle_biomedicine_54.csv"))
for index, row in tqdm(df.iterrows(), desc="Processing questions", total=len(df)):
    row = row.to_dict()
    question = row['question']
    question_prompt = question_template.format(question=question)
    execution_results = agent.go(question_prompt, knowledge_bases=["pubmed_papers"])
    outputs = execution_results.to_json()
    outputs = {
        "outputs": outputs,
    }
    outputs.update(row)
    with open(os.path.join(RESULTS_DIR, f"hle_biomedicine_54_{index}.json"), 'w') as f:
        json.dump(outputs, f)
    print(outputs["answer"])
    print(outputs["outputs"]["final_response"])
    print("-" * 100)