"""Benchmark deep evidence agent in the clinical trial development benchmark tasks.
"""
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
    model_kwargs={
        "max_completion_tokens": 5000,
        "reasoning_effort": "minimal",
    },
    subagent_action_rounds_budget=5, # the number of action rounds for the sub research agents to run
    main_search_rounds_budget=2, # the number of search rounds for the main orchestrator agent to run
    main_action_rounds_budget=15, # the number of action rounds for the main orchestrator agent to run
    light_mode=False, # a light mode agent that does not use the memory graph
    llm_timeout=120,
)

# run the agent
execution_results = agent.go(
    "Summarizing the cutting-edge immunotherapy drugs in late clinical trial phase or have been approved for NSCLC?",
    knowledge_bases=["pubmed_papers", "clinical_trials", "drug", "disease"], # select the knowledge bases to use
)
print(execution_results.to_json())
execution_results.to_pdf(output_dir="test_artifacts")
agent.clear_workspace()
print("Done!")
