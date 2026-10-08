import os
import sys
from datetime import datetime
from pathlib import Path


REPO_BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(REPO_BASE_DIR))

from dotenv import load_dotenv
from biodsa.agents import DeepEvidenceAgent


def main() -> None:
    load_dotenv(REPO_BASE_DIR / ".env")
    agent = DeepEvidenceAgent(
        model_name="gpt-5",
        api_type="openai",
        api_key=os.environ.get("OPENAI_API_KEY"),
        model_kwargs={
            "max_completion_tokens": 5000,
            "reasoning_effort": "minimal",
        },
        subagent_action_rounds_budget=2,    # 大幅降低
        main_search_rounds_budget=1,        # 只搜索1轮
        main_action_rounds_budget=5,        # 行动轮次减半
        light_mode=False,
        llm_timeout=120,
    )


    execution_results = agent.go(
        "Summarizing the cutting-edge immunotherapy drugs in late clinical trial phase or have been approved for NSCLC?",
        knowledge_bases=["pubmed_papers", "clinical_trials", "drug", "disease"],
    )

    print(execution_results)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = REPO_BASE_DIR / "tutorials" / f"deepevidence-results-{timestamp}"
    pdf_path = execution_results.to_pdf(output_dir=str(output_dir))
    print(f"PDF saved to: {pdf_path}")

    agent.clear_workspace()


if __name__ == "__main__":
    main()
