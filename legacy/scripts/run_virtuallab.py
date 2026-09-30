import sys
import os
current_dir = os.getcwd()
REPO_BASE_DIR = os.path.dirname(os.path.abspath(current_dir))
sys.path.append(REPO_BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_BASE_DIR, ".env"))

from biodsa.agents.virtuallab import VirtualLabAgent, CODING_RULES

# Initialize agent
agent = VirtualLabAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    num_rounds=1,
)

# Create participants
pi = agent.create_participant(
    title="Principal Investigator",
    expertise="bioinformatics and computational biology",
    goal="develop useful tools for biological data analysis",
    role="lead the discussion and make decisions",
)

ml_specialist = agent.create_participant(
    title="Bioinformatics Developer",
    expertise="Python programming and sequence analysis",
    goal="write clean, efficient code for biological applications",
    role="implement computational solutions",
)

# Round 1: Discuss requirements for a simple utility function
res1 = agent.go(
    """
    We need a simple Python function to calculate GC content of a DNA sequence.

    Please discuss:
    1. What should the function be named?
    2. What input validation should it include?
    3. Should it handle both uppercase and lowercase sequences?
    4. What should it return (percentage or fraction)?
    """,
    None,
    meeting_type="individual",
    team_member=pi,
)

# Round 2: Implement based on Round 1's specification
res2 = agent.go(
    """
    Based on the discussion, write the Python function for calculating GC content.
    Include docstring and type hints.
    """,
    res1,
    meeting_type="individual",
    team_member=ml_specialist,
    agenda_rules=list(CODING_RULES),
    num_rounds=1,
)

# Print results
print("\n" + "=" * 70)
print("ROUND 1 - Requirements Discussion:")
print("=" * 70)
print(res1.final_response)

print("\n" + "=" * 70)
print("ROUND 2 - Implementation:")
print("=" * 70)
print(res2.final_response)
