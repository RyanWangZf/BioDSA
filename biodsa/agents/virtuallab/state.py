"""
State definitions for Virtual Lab multi-agent meetings.

This module defines the state classes used by the VirtualLabAgent's LangGraph
workflows for team and individual meetings.

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
from typing import List, Optional, Literal, Annotated, Sequence, Any
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages, BaseMessage

from biodsa.agents.virtuallab.participant import Participant


class MeetingMessage(BaseModel):
    """
    A single message in a meeting discussion.
    
    Attributes:
        agent: The participant title, "User" for prompts, or "Tool" for tool outputs
        message: The content of the message
    """
    agent: str = Field(description="The agent/participant who sent this message")
    message: str = Field(description="The content of the message")


class MeetingContext(BaseModel):
    """
    Context information for a meeting.
    
    Attributes:
        summaries: Summaries from previous meetings
        contexts: Additional context documents
    """
    summaries: List[str] = Field(
        default_factory=list,
        description="Summaries from previous meetings"
    )
    contexts: List[str] = Field(
        default_factory=list,
        description="Additional context documents"
    )


class VirtualLabState(BaseModel):
    """
    State for Virtual Lab meeting workflows.
    
    This state is used by both team meetings and individual meetings,
    with different fields being relevant for each meeting type.
    
    Attributes:
        meeting_type: Either "team" or "individual"
        agenda: The main agenda/topic for the meeting
        agenda_questions: Specific questions to answer during the meeting
        agenda_rules: Rules that must be followed (e.g., coding standards)
        team_lead: The team lead for team meetings
        team_members: List of team member participants
        team_member: The single participant for individual meetings
        discussion: List of all messages in the discussion
        messages: LangGraph message history for LLM context
        current_round: Current discussion round (1-indexed)
        num_rounds: Total number of discussion rounds
        current_member_index: Index of current team member in round
        phase: Current phase of the meeting
        summary: Final meeting summary
        temperature: Sampling temperature for generation
        use_pubmed: Whether to enable PubMed search tool
        meeting_context: Previous summaries and contexts
    """
    
    # Meeting configuration
    meeting_type: Literal["team", "individual"] = Field(
        default="individual",
        description="Type of meeting"
    )
    agenda: str = Field(
        default="",
        description="The main agenda/topic for the meeting"
    )
    agenda_questions: List[str] = Field(
        default_factory=list,
        description="Specific questions to answer during the meeting"
    )
    agenda_rules: List[str] = Field(
        default_factory=list,
        description="Rules that must be followed"
    )
    
    # Participants (stored as dicts for serialization, converted back to Participant when needed)
    team_lead: Optional[dict] = Field(
        default=None,
        description="The team lead participant (for team meetings)"
    )
    team_members: List[dict] = Field(
        default_factory=list,
        description="List of team member participants"
    )
    team_member: Optional[dict] = Field(
        default=None,
        description="The single participant (for individual meetings)"
    )
    
    # Discussion state
    discussion: List[MeetingMessage] = Field(
        default_factory=list,
        description="List of all messages in the discussion"
    )
    messages: Annotated[Sequence[BaseMessage], add_messages] = Field(
        default_factory=list,
        description="LangGraph message history"
    )
    
    # Round tracking
    current_round: int = Field(
        default=1,
        description="Current discussion round (1-indexed)"
    )
    num_rounds: int = Field(
        default=2,
        description="Total number of discussion rounds"
    )
    current_member_index: int = Field(
        default=0,
        description="Index of current team member in round"
    )
    
    # Meeting phase tracking
    phase: Literal[
        "start",
        "team_lead_initial",
        "team_member_response",
        "team_lead_synthesize",
        "team_lead_final",
        "individual_agent",
        "individual_critic",
        "complete"
    ] = Field(
        default="start",
        description="Current phase of the meeting"
    )
    
    # Output
    summary: str = Field(
        default="",
        description="Final meeting summary"
    )
    
    # Generation settings
    temperature: float = Field(
        default=0.8,
        description="Sampling temperature for generation"
    )
    use_pubmed: bool = Field(
        default=False,
        description="Whether to enable PubMed search tool"
    )
    
    # Context from previous meetings
    meeting_context: MeetingContext = Field(
        default_factory=MeetingContext,
        description="Previous summaries and contexts"
    )
    
    class Config:
        arbitrary_types_allowed = True
    
    def get_team_lead(self) -> Optional[Participant]:
        """Get team lead as Participant object."""
        if self.team_lead is None:
            return None
        return Participant(**self.team_lead)
    
    def get_team_members(self) -> List[Participant]:
        """Get team members as list of Participant objects."""
        return [Participant(**m) for m in self.team_members]
    
    def get_team_member(self) -> Optional[Participant]:
        """Get team member as Participant object (for individual meetings)."""
        if self.team_member is None:
            return None
        return Participant(**self.team_member)
    
    def get_current_participant(self) -> Optional[Participant]:
        """Get the current participant based on meeting phase."""
        if self.meeting_type == "team":
            if self.phase in ["team_lead_initial", "team_lead_synthesize", "team_lead_final"]:
                return self.get_team_lead()
            elif self.phase == "team_member_response":
                members = self.get_team_members()
                if 0 <= self.current_member_index < len(members):
                    return members[self.current_member_index]
        else:
            return self.get_team_member()
        return None
    
    def add_message(self, agent: str, message: str) -> None:
        """Add a message to the discussion."""
        self.discussion.append(MeetingMessage(agent=agent, message=message))
    
    def get_discussion_text(self) -> str:
        """Get the full discussion as formatted text."""
        lines = []
        for msg in self.discussion:
            lines.append(f"## {msg.agent}\n\n{msg.message}\n")
        return "\n".join(lines)


class TeamMeetingInput(BaseModel):
    """Input schema for running a team meeting."""
    
    team_lead: Participant = Field(
        description="The team lead participant"
    )
    team_members: List[Participant] = Field(
        description="List of team member participants"
    )
    agenda: str = Field(
        description="The meeting agenda"
    )
    agenda_questions: List[str] = Field(
        default_factory=list,
        description="Questions to answer"
    )
    agenda_rules: List[str] = Field(
        default_factory=list,
        description="Rules to follow"
    )
    num_rounds: int = Field(
        default=2,
        description="Number of discussion rounds"
    )
    temperature: float = Field(
        default=0.8,
        description="Sampling temperature"
    )
    summaries: List[str] = Field(
        default_factory=list,
        description="Summaries from previous meetings"
    )
    contexts: List[str] = Field(
        default_factory=list,
        description="Additional context"
    )
    use_pubmed: bool = Field(
        default=False,
        description="Enable PubMed search"
    )


class IndividualMeetingInput(BaseModel):
    """Input schema for running an individual meeting."""
    
    team_member: Participant = Field(
        description="The participant for the meeting"
    )
    agenda: str = Field(
        description="The meeting agenda"
    )
    agenda_questions: List[str] = Field(
        default_factory=list,
        description="Questions to answer"
    )
    agenda_rules: List[str] = Field(
        default_factory=list,
        description="Rules to follow"
    )
    num_rounds: int = Field(
        default=2,
        description="Number of critic-revision rounds"
    )
    temperature: float = Field(
        default=0.8,
        description="Sampling temperature"
    )
    summaries: List[str] = Field(
        default_factory=list,
        description="Summaries from previous meetings"
    )
    contexts: List[str] = Field(
        default_factory=list,
        description="Additional context"
    )
    use_pubmed: bool = Field(
        default=False,
        description="Enable PubMed search"
    )
