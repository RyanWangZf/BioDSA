# Virtual Lab Agent

Virtual Lab is a multi-agent meeting system for AI-powered scientific research discussions. It enables structured conversations between AI participants with different expertise to solve complex research problems.

## Overview

Based on the [Virtual Lab framework](https://github.com/zou-group/virtual-lab) from Zou Group:

> Swanson, K., Wu, W., Bulaong, N.L., Pak, J.E. & Zou, J. The Virtual Lab of AI agents designs new SARS-CoV-2 nanobodies. *Nature* 646, 716–723 (2025). [https://doi.org/10.1038/s41586-025-09442-9](https://www.nature.com/articles/s41586-025-09442-9)

Virtual Lab implements two types of meetings:

1. **Team Meetings**: Multiple AI agents with different expertise discuss a research agenda over multiple rounds, with a team lead synthesizing the discussion and providing a final summary.

2. **Individual Meetings**: A single AI agent works on a task with iterative feedback from a Scientific Critic, refining their response until it meets quality standards.

## Quick Start

```python
from biodsa.agents.virtuallab import VirtualLabAgent

# Initialize the agent
agent = VirtualLabAgent(
    model_name="gpt-4o",
    api_type="azure",
    api_key="your-api-key",
    endpoint="your-endpoint",
    num_rounds=1
)

# Run a simple meeting
results = agent.go(
    "Explain how protein language models can be used for mutation effect prediction.",
    None  # No previous context
)

print(results.final_response)
```

## Multi-Round Conversations

The key feature of Virtual Lab is chaining meetings where each builds on previous results:

```python
# Round 1: Discuss requirements
res1 = agent.go(
    "We need a function to calculate GC content. What should it include?",
    None,  # No previous context
    meeting_type="individual",
    team_member=pi,
)

# Round 2: Implementation based on Round 1
res2 = agent.go(
    "Based on the discussion, write the Python function.",
    res1,  # Use Round 1's results as context
    meeting_type="individual",
    team_member=ml_specialist,
)

# Round 3: Can chain multiple previous results
res3 = agent.go(
    "Review and improve the implementation.",
    [res1, res2],  # Use multiple previous results
    meeting_type="individual",
    team_member=bio_expert,
)
```

## Creating Participants

Participants are AI agents with specific roles and expertise:

```python
# Create custom participants
pi = agent.create_participant(
    title="Principal Investigator",
    expertise="AI for biomedical research",
    goal="maximize scientific impact of the work",
    role="lead the team and make key decisions"
)

ml_specialist = agent.create_participant(
    title="Machine Learning Specialist",
    expertise="deep learning and protein language models",
    goal="develop ML methods for protein design",
    role="provide ML expertise and implementation"
)

bio_expert = agent.create_participant(
    title="Computational Biologist",
    expertise="protein structure and molecular dynamics",
    goal="ensure biological validity",
    role="provide expertise on protein biology"
)
```

### Pre-defined Participants

Virtual Lab includes commonly used participants:

```python
from biodsa.agents.virtuallab import (
    PRINCIPAL_INVESTIGATOR,
    SCIENTIFIC_CRITIC,
    MACHINE_LEARNING_SPECIALIST,
    COMPUTATIONAL_BIOLOGIST,
    IMMUNOLOGIST,
)

# Or get by name
pi = agent.get_predefined_participant("pi")
critic = agent.get_predefined_participant("critic")
```

## Team Meetings

Team meetings involve multiple participants discussing an agenda:

```python
results = agent.go(
    "Design a nanobody optimization pipeline for SARS-CoV-2",
    None,
    meeting_type="team",
    team_lead=pi,
    team_members=[ml_specialist, bio_expert],
    agenda_questions=[
        "What computational tools should we use?",
        "How should we validate the designs?",
    ],
    num_rounds=2
)
```

Or use the explicit method:

```python
results = agent.run_team_meeting(
    team_lead=pi,
    team_members=[ml_specialist, bio_expert],
    agenda="Design a nanobody optimization pipeline",
    agenda_questions=["What tools?", "How to validate?"],
    num_rounds=2
)
```

### Team Meeting Flow

1. **Start**: Meeting context and agenda are presented
2. **Team Lead Initial**: Team lead provides initial thoughts and questions
3. **Team Member Responses** (per round): Each member provides their perspective
4. **Team Lead Synthesis** (per round): Team lead synthesizes and asks follow-ups
5. **Final Summary**: Team lead provides comprehensive summary with recommendations

## Individual Meetings

Individual meetings pair a participant with a Scientific Critic:

```python
from biodsa.agents.virtuallab import CODING_RULES

results = agent.go(
    "Write a Python script that uses ESM to score protein mutations",
    None,
    meeting_type="individual",
    team_member=ml_specialist,
    agenda_rules=list(CODING_RULES),
    num_rounds=2
)
```

### Individual Meeting Flow

1. **Initial Response**: Participant provides their answer
2. **Critic Feedback**: Scientific Critic reviews and suggests improvements
3. **Revision**: Participant addresses feedback
4. Repeat steps 2-3 for specified rounds
5. **Final Answer**: Last participant response is the result

## Complete Example: Two-Round Workflow

```python
from biodsa.agents.virtuallab import VirtualLabAgent, CODING_RULES

agent = VirtualLabAgent(
    model_name="gpt-4o",
    api_type="azure",
    api_key=api_key,
    endpoint=endpoint,
    num_rounds=1,
)

# Create participants
pi = agent.create_participant(
    title="Principal Investigator",
    expertise="bioinformatics",
    goal="develop useful tools",
    role="lead the discussion",
)

developer = agent.create_participant(
    title="Bioinformatics Developer",
    expertise="Python and sequence analysis",
    goal="write clean code",
    role="implement solutions",
)

# Round 1: Discuss requirements
res1 = agent.go(
    """
    We need a Python function to calculate GC content of a DNA sequence.
    Please discuss:
    1. What should the function be named?
    2. What input validation should it include?
    3. Should it return percentage or fraction?
    """,
    None,
    meeting_type="individual",
    team_member=pi,
)

# Round 2: Implement based on Round 1
res2 = agent.go(
    """
    Based on the discussion, write the Python function.
    Include docstring and type hints.
    """,
    res1,  # Uses Round 1's output as context
    meeting_type="individual",
    team_member=developer,
    agenda_rules=list(CODING_RULES),
)

print("Requirements:", res1.final_response)
print("Implementation:", res2.final_response)
```

## Merging Multiple Meeting Results

```python
# Merge summaries from multiple meetings
merged = agent.merge_summaries(
    summaries=[res1.final_response, res2.final_response],
    agenda="GC content calculator development"
)
```

## PubMed Integration

Enable literature search during meetings:

```python
results = agent.go(
    "Review the latest advances in nanobody engineering",
    None,
    team_member=bio_expert,
    use_pubmed=True
)
```

## Saving Meeting Results

```python
agent.save_meeting(
    results=results,
    save_dir="meetings/project",
    save_name="discussion_1"
)
# Creates: discussion_1.json and discussion_1.md
```

## Reasoning Model Support

Virtual Lab automatically handles reasoning models (gpt-5, o1, o3, etc.) that only support `temperature=1`:

```python
# Works with any model - temperature is automatically adjusted
agent = VirtualLabAgent(
    model_name="gpt-5",  # Reasoning model
    api_type="azure",
    api_key=api_key,
    endpoint=endpoint,
)
```

## API Reference

### VirtualLabAgent

| Method | Description |
|--------|-------------|
| `go(query, previous_results, ...)` | Main interface - run a meeting with optional previous context |
| `create_participant(...)` | Create a new Participant |
| `run_team_meeting(...)` | Run a team meeting (explicit interface) |
| `run_individual_meeting(...)` | Run an individual meeting (explicit interface) |
| `merge_summaries(...)` | Merge multiple meeting summaries |
| `save_meeting(...)` | Save meeting to JSON/Markdown files |

### go() Method

```python
agent.go(
    input_query,           # The agenda/topic
    previous_results,      # None, ExecutionResults, or List[ExecutionResults]
    meeting_type="individual",  # "team" or "individual"
    team_member=...,       # For individual meetings
    team_lead=...,         # For team meetings
    team_members=[...],    # For team meetings
    agenda_questions=[...],
    agenda_rules=[...],
    num_rounds=2,
    use_pubmed=False,
)
```

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `previous_results` | Previous meeting results to use as context | None |
| `num_rounds` | Discussion/critic rounds | 2 |
| `use_pubmed` | Enable PubMed search | False |
| `agenda_questions` | Specific questions to answer | [] |
| `agenda_rules` | Rules to follow (e.g., CODING_RULES) | [] |
