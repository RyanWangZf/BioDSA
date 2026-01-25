"""
Participant class for Virtual Lab multi-agent meetings.

A Participant represents an AI research agent with a specific title, expertise,
goal, and role. Participants engage in team or individual meetings to discuss
research agendas and solve scientific problems.

Based on the Virtual Lab framework:
@article{swanson2025virtual,
  title={The Virtual Lab of AI agents designs new SARS-CoV-2 nanobodies},
  author={Swanson, Kyle and Wu, Wesley and Bulaong, Nash L. and Pak, John E. and Zou, James},
  journal={Nature},
  volume={646},
  pages={716--723},
  year={2025}
}

Reference: https://github.com/zou-group/virtual-lab
"""
from typing import Optional
from pydantic import BaseModel, Field


class Participant(BaseModel):
    """
    An AI research agent participant in Virtual Lab meetings.
    
    Each participant has a specific expertise and role that guides their
    contributions to the discussion. The participant's system prompt is
    automatically generated from these attributes.
    
    Attributes:
        title: The professional title (e.g., "Principal Investigator")
        expertise: Area of expertise (e.g., "applying AI to biomedical research")
        goal: The participant's goal (e.g., "maximize scientific impact")
        role: The participant's role in the team (e.g., "lead the team")
        model_name: Optional LLM model override for this participant
        
    Example:
        ```python
        pi = Participant(
            title="Principal Investigator",
            expertise="applying artificial intelligence to biomedical research",
            goal="perform research that maximizes scientific impact",
            role="lead a team of experts to solve important problems"
        )
        print(pi.system_prompt)
        ```
    """
    
    title: str = Field(
        description="The professional title of the participant"
    )
    expertise: str = Field(
        description="The participant's area of expertise"
    )
    goal: str = Field(
        description="The participant's goal in the research project"
    )
    role: str = Field(
        description="The participant's role in the team"
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Optional LLM model override for this participant"
    )
    
    @property
    def system_prompt(self) -> str:
        """
        Generate the system prompt for this participant.
        
        Returns:
            A formatted system prompt describing the participant's role.
        """
        return (
            f"You are a {self.title}. "
            f"Your expertise is in {self.expertise}. "
            f"Your goal is to {self.goal}. "
            f"Your role is to {self.role}."
        )
    
    def __hash__(self) -> int:
        """Return hash based on title for set operations."""
        return hash(self.title)
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on all attributes."""
        if not isinstance(other, Participant):
            return False
        return (
            self.title == other.title
            and self.expertise == other.expertise
            and self.goal == other.goal
            and self.role == other.role
            and self.model_name == other.model_name
        )
    
    def __str__(self) -> str:
        """Return the participant's title."""
        return self.title
    
    def __repr__(self) -> str:
        """Return a detailed string representation."""
        return f"Participant(title='{self.title}', expertise='{self.expertise[:30]}...')"


# Pre-defined participants commonly used in Virtual Lab
PRINCIPAL_INVESTIGATOR = Participant(
    title="Principal Investigator",
    expertise="running a science research lab",
    goal="perform research in your area of expertise that maximizes the scientific impact of the work",
    role="lead a team of experts to solve an important scientific problem, make key decisions about the project direction based on team member input, and manage the project timeline and resources",
)

SCIENTIFIC_CRITIC = Participant(
    title="Scientific Critic",
    expertise="providing critical feedback for scientific research",
    goal="ensure that proposed research projects and implementations are rigorous, detailed, feasible, and scientifically sound",
    role="provide critical feedback to identify and correct all errors and demand that scientific answers are maximally complete and detailed but simple and not overly complex",
)

MACHINE_LEARNING_SPECIALIST = Participant(
    title="Machine Learning Specialist",
    expertise="machine learning and deep learning for scientific applications",
    goal="develop and apply state-of-the-art machine learning methods to solve scientific problems",
    role="provide expertise on machine learning approaches, model selection, and implementation strategies",
)

COMPUTATIONAL_BIOLOGIST = Participant(
    title="Computational Biologist",
    expertise="computational biology and bioinformatics",
    goal="apply computational methods to understand biological systems",
    role="provide expertise on biological data analysis, molecular modeling, and computational pipelines",
)

IMMUNOLOGIST = Participant(
    title="Immunologist",
    expertise="immunology and antibody engineering",
    goal="develop effective therapeutic antibodies and understand immune responses",
    role="provide expertise on antibody design, immune mechanisms, and therapeutic applications",
)
