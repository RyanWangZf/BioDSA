"""
Virtual Lab: Multi-agent meeting system for scientific research.

Virtual Lab enables AI-powered scientific discussions through team meetings
and individual meetings with automatic critic feedback. It implements the
Virtual Lab framework for collaborative AI research.

Based on the Virtual Lab framework:
@article{swanson2024virtual,
  title={Virtual Lab: AI Agents Design New SARS-CoV-2 Nanobodies with Experimental Validation},
  author={Swanson, Kyle and others},
  year={2024}
}

Reference: https://github.com/zou-group/virtual-lab

Example usage:
    ```python
    from biodsa.agents.virtuallab import VirtualLabAgent, Participant
    
    # Create agent
    agent = VirtualLabAgent(
        model_name="gpt-4o",
        api_type="azure",
        api_key=api_key,
        endpoint=endpoint
    )
    
    # Create participants
    pi = agent.create_participant(
        title="Principal Investigator",
        expertise="AI for biomedicine",
        goal="maximize scientific impact",
        role="lead the team"
    )
    
    # Run meeting
    results = agent.run_individual_meeting(
        team_member=pi,
        agenda="Design a protein optimization strategy"
    )
    ```
"""

from biodsa.agents.virtuallab.agent import (
    VirtualLabAgent,
    CONSISTENT_TEMPERATURE,
    CREATIVE_TEMPERATURE,
)
from biodsa.agents.virtuallab.participant import (
    Participant,
    PRINCIPAL_INVESTIGATOR,
    SCIENTIFIC_CRITIC,
    MACHINE_LEARNING_SPECIALIST,
    COMPUTATIONAL_BIOLOGIST,
    IMMUNOLOGIST,
)
from biodsa.agents.virtuallab.state import (
    VirtualLabState,
    MeetingMessage,
    MeetingContext,
    TeamMeetingInput,
    IndividualMeetingInput,
)
from biodsa.agents.virtuallab.prompt import (
    CODING_RULES,
    create_merge_prompt,
)
from biodsa.agents.virtuallab.tools import (
    PubMedSearchTool,
    get_virtuallab_tools,
)

__all__ = [
    # Main agent
    "VirtualLabAgent",
    # Participant
    "Participant",
    "PRINCIPAL_INVESTIGATOR",
    "SCIENTIFIC_CRITIC",
    "MACHINE_LEARNING_SPECIALIST",
    "COMPUTATIONAL_BIOLOGIST",
    "IMMUNOLOGIST",
    # State
    "VirtualLabState",
    "MeetingMessage",
    "MeetingContext",
    "TeamMeetingInput",
    "IndividualMeetingInput",
    # Prompts
    "CODING_RULES",
    "create_merge_prompt",
    # Tools
    "PubMedSearchTool",
    "get_virtuallab_tools",
    # Constants
    "CONSISTENT_TEMPERATURE",
    "CREATIVE_TEMPERATURE",
]
