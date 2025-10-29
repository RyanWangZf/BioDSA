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

question_template = """
{question}

Make sure to answer the question by exploring the given knowledge bases.
If necessary, you should also try to write code to do data analysis or meta-analysis to answer the question.
Make sure provide your final answer in the format of <Answer> <letter of the correct answer> </Answer>, which will be used to extract the answer for evaluation.
"""

def evidence_synthesis():
    df = pd.read_csv(os.path.join(REPO_BASE_DIR, "benchmarks/TrialPanoramaBench/evidence_synthesis_50.csv"))
    agent = DeepEvidenceAgent(
        model_name="gpt-5",
        api_type="azure",
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    )
    # register a workspace for the agent to use
    agent.register_workspace()

    # specify the indices of the questions to answer
    to_process_indices = [
        49
    ]

    for index, row in tqdm(df.iterrows(), desc="Processing questions", total=len(df)):
        if index not in to_process_indices:
            continue
        row = row.to_dict()
        question = row['question']
        question_prompt = question_template.format(question=question)
        execution_results = agent.go(question_prompt, knowledge_bases=["pubmed_papers"])
        outputs = execution_results.to_json()
        outputs = {
            "outputs": outputs,
        }
        outputs.update(row)
        with open(os.path.join(RESULTS_DIR, f"evidence_synthesis_{index}.json"), 'w') as f:
            json.dump(outputs, f, indent=4)
        print(outputs["answer"])
        print(outputs["outputs"]["final_response"])
        print("-" * 100)

if __name__ == "__main__":
    evidence_synthesis()