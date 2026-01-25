"""
Prompts for Virtual Lab multi-agent meetings.

This module contains all the prompt templates used for team meetings and
individual meetings in the Virtual Lab framework.

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
from typing import List, Tuple

from biodsa.agents.virtuallab.participant import Participant


# =============================================================================
# Constants
# =============================================================================

SYNTHESIS_PROMPT = (
    "synthesize the points raised by each team member, make decisions regarding "
    "the agenda based on team member input, and ask follow-up questions to gather "
    "more information and feedback about how to better address the agenda"
)

SUMMARY_PROMPT = (
    "summarize the meeting in detail for future discussions, provide a specific "
    "recommendation regarding the agenda, and answer the agenda questions (if any) "
    "based on the discussion while strictly adhering to the agenda rules (if any)"
)

MERGE_PROMPT = (
    "Please read the summaries of multiple separate meetings about the same agenda. "
    "Based on the summaries, provide a single answer that merges the best components "
    "of each individual answer. Please use the same format as the individual answers. "
    "Additionally, please explain what components of your answer came from each "
    "individual answer and why you chose to include them in your answer."
)

REWRITE_PROMPT = (
    "This script needs to be improved. Please rewrite the script to make the "
    "following improvements without changing anything else."
)

CODING_RULES: Tuple[str, ...] = (
    "Your code must be self-contained (with appropriate imports) and complete.",
    "Your code may not include any undefined or unimplemented variables or functions.",
    "Your code may not include any pseudocode; it must be fully functioning code.",
    "Your code may not include any hard-coded examples.",
    "If your code needs user-provided values, write code to parse those values from the command line.",
    "Your code must be high quality, well-engineered, efficient, and well-documented "
    "(including docstrings, comments, and Python type hints if using Python).",
)


# =============================================================================
# Formatting Helpers
# =============================================================================

def format_prompt_list(prompts: List[str]) -> str:
    """Format prompts as a numbered list."""
    return "\n\n".join(f"{i + 1}. {prompt}" for i, prompt in enumerate(prompts))


def format_agenda(agenda: str, intro: str = "Here is the agenda for the meeting:") -> str:
    """Format the agenda for the prompt."""
    return f"{intro}\n\n{agenda}\n\n"


def format_agenda_questions(
    agenda_questions: List[str],
    intro: str = "Here are the agenda questions that must be answered:",
) -> str:
    """Format the agenda questions for the prompt as a numbered list."""
    if not agenda_questions:
        return ""
    return f"{intro}\n\n{format_prompt_list(agenda_questions)}\n\n"


def format_agenda_rules(
    agenda_rules: List[str],
    intro: str = "Here are the agenda rules that must be followed:",
) -> str:
    """Format the agenda rules for the prompt as a numbered list."""
    if not agenda_rules:
        return ""
    return f"{intro}\n\n{format_prompt_list(agenda_rules)}\n\n"


def format_references(
    references: List[str],
    reference_type: str,
    intro: str
) -> str:
    """Format references (e.g., contexts, summaries) for the prompt."""
    if not references:
        return ""
    
    formatted_references = [
        f"[begin {reference_type} {i + 1}]\n\n{ref}\n\n[end {reference_type} {i + 1}]"
        for i, ref in enumerate(references)
    ]
    
    return f"{intro}\n\n{chr(10).join(formatted_references)}\n\n"


def summary_structure_prompt(has_agenda_questions: bool) -> str:
    """Format the structure of a summary prompt."""
    if has_agenda_questions:
        agenda_questions_structure = [
            "### Answers",
            "For each agenda question, please provide the following:",
            "Answer: A specific answer to the question based on your recommendation above.",
            "Justification: A brief explanation of why you provided that answer.",
        ]
    else:
        agenda_questions_structure = []
    
    sections = [
        "### Agenda",
        "Restate the agenda in your own words.",
        "### Team Member Input",
        "Summarize all of the important points raised by each team member. "
        "This is to ensure that key details are preserved for future meetings.",
        "### Recommendation",
        "Provide your expert recommendation regarding the agenda. You should consider "
        "the input from each team member, but you must also use your expertise to make "
        "a final decision and choose one option among several that may have been discussed. "
        "This decision can conflict with the input of some team members as long as it is "
        "well justified. It is essential that you provide a clear, specific, and actionable "
        "recommendation. Please justify your recommendation as well.",
    ] + agenda_questions_structure + [
        "### Next Steps",
        "Outline the next steps that the team should take based on the discussion.",
    ]
    
    return "\n\n".join(sections)


# =============================================================================
# Team Meeting Prompts
# =============================================================================

def team_meeting_start_prompt(
    team_lead: Participant,
    team_members: List[Participant],
    agenda: str,
    agenda_questions: List[str] = None,
    agenda_rules: List[str] = None,
    summaries: List[str] = None,
    contexts: List[str] = None,
    num_rounds: int = 1,
) -> str:
    """
    Generate the start prompt for a team meeting.
    
    Args:
        team_lead: The team lead participant
        team_members: List of team member participants
        agenda: The agenda for the meeting
        agenda_questions: Questions to answer by the end of the meeting
        agenda_rules: Rules for the agenda
        summaries: Summaries of previous meetings
        contexts: Additional context for the meeting
        num_rounds: Number of discussion rounds
        
    Returns:
        The start prompt for the team meeting
    """
    agenda_questions = agenda_questions or []
    agenda_rules = agenda_rules or []
    summaries = summaries or []
    contexts = contexts or []
    
    member_titles = ", ".join(m.title for m in team_members)
    
    return (
        f"This is the beginning of a team meeting to discuss your research project. "
        f"This is a meeting with the team lead, {team_lead.title}, and the following team members: "
        f"{member_titles}.\n\n"
        f"{format_references(contexts, reference_type='context', intro='Here is context for this meeting:')}"
        f"{format_references(summaries, reference_type='summary', intro='Here are summaries of the previous meetings:')}"
        f"{format_agenda(agenda)}"
        f"{format_agenda_questions(agenda_questions)}"
        f"{format_agenda_rules(agenda_rules)}"
        f"{team_lead} will convene the meeting. "
        f"Then, each team member will provide their thoughts on the discussion one-by-one in the order above. "
        f"After all team members have given their input, {team_lead} will {SYNTHESIS_PROMPT}. "
        f"This will continue for {num_rounds} round{'s' if num_rounds > 1 else ''}. "
        f"Once the discussion is complete, {team_lead} will {SUMMARY_PROMPT}."
    )


def team_meeting_team_lead_initial_prompt(team_lead: Participant) -> str:
    """Generate the initial prompt for the team lead in a team meeting."""
    return (
        f"{team_lead}, please provide your initial thoughts on the agenda as well as "
        f"any questions you have to guide the discussion among the team members."
    )


def team_meeting_team_member_prompt(
    team_member: Participant,
    round_num: int,
    num_rounds: int
) -> str:
    """Generate the prompt for a team member in a team meeting."""
    return (
        f"{team_member}, please provide your thoughts on the discussion "
        f"(round {round_num} of {num_rounds}). "
        f'If you do not have anything new or relevant to add, you may say "pass". '
        f"Remember that you can and should (politely) disagree with other team members "
        f"if you have a different perspective."
    )


def team_meeting_team_lead_intermediate_prompt(
    team_lead: Participant,
    round_num: int,
    num_rounds: int
) -> str:
    """Generate the intermediate prompt for the team lead at the end of a round."""
    return (
        f"This concludes round {round_num} of {num_rounds} of discussion. "
        f"{team_lead}, please {SYNTHESIS_PROMPT}."
    )


def team_meeting_team_lead_final_prompt(
    team_lead: Participant,
    agenda: str,
    agenda_questions: List[str] = None,
    agenda_rules: List[str] = None,
) -> str:
    """Generate the final prompt for the team lead to summarize the discussion."""
    agenda_questions = agenda_questions or []
    agenda_rules = agenda_rules or []
    
    return (
        f"{team_lead}, please {SUMMARY_PROMPT}.\n\n"
        f"{format_agenda(agenda, intro='As a reminder, here is the agenda for the meeting:')}"
        f"{format_agenda_questions(agenda_questions, intro='As a reminder, here are the agenda questions that must be answered:')}"
        f"{format_agenda_rules(agenda_rules, intro='As a reminder, here are the agenda rules that must be followed:')}"
        f"Your summary should take the following form.\n\n"
        f"{summary_structure_prompt(has_agenda_questions=len(agenda_questions) > 0)}"
    )


# =============================================================================
# Individual Meeting Prompts
# =============================================================================

def individual_meeting_start_prompt(
    team_member: Participant,
    agenda: str,
    agenda_questions: List[str] = None,
    agenda_rules: List[str] = None,
    summaries: List[str] = None,
    contexts: List[str] = None,
) -> str:
    """
    Generate the start prompt for an individual meeting.
    
    Args:
        team_member: The participant for the meeting
        agenda: The agenda for the meeting
        agenda_questions: Questions to answer
        agenda_rules: Rules for the agenda
        summaries: Summaries of previous meetings
        contexts: Additional context
        
    Returns:
        The start prompt for the individual meeting
    """
    agenda_questions = agenda_questions or []
    agenda_rules = agenda_rules or []
    summaries = summaries or []
    contexts = contexts or []
    
    return (
        f"This is the beginning of an individual meeting with {team_member} to discuss your research project.\n\n"
        f"{format_references(contexts, reference_type='context', intro='Here is context for this meeting:')}"
        f"{format_references(summaries, reference_type='summary', intro='Here are summaries of the previous meetings:')}"
        f"{format_agenda(agenda)}"
        f"{format_agenda_questions(agenda_questions)}"
        f"{format_agenda_rules(agenda_rules)}"
        f"{team_member}, please provide your response to the agenda."
    )


def individual_meeting_critic_prompt(
    critic: Participant,
    agent: Participant,
) -> str:
    """Generate the prompt for the critic in an individual meeting."""
    return (
        f"{critic.title}, please critique {agent.title}'s most recent answer. "
        "In your critique, suggest improvements that directly address the agenda and any agenda questions. "
        "Prioritize simple solutions over unnecessarily complex ones, but demand more detail where detail is lacking. "
        "Additionally, validate whether the answer strictly adheres to the agenda and any agenda questions "
        "and provide corrective feedback if it does not. "
        "Only provide feedback; do not implement the answer yourself."
    )


def individual_meeting_agent_prompt(
    critic: Participant,
    agent: Participant,
) -> str:
    """Generate the prompt for the agent to address critic's feedback."""
    return (
        f"{agent.title}, please modify your answer to address {critic.title}'s most recent feedback. "
        "Remember that your ultimate goal is to make improvements that better address the agenda."
    )


# =============================================================================
# Merge Prompts
# =============================================================================

def create_merge_prompt(
    agenda: str,
    agenda_questions: List[str] = None,
    agenda_rules: List[str] = None,
) -> str:
    """
    Create a merge prompt for merging the best components of multiple meeting answers.
    
    Args:
        agenda: The original agenda for the separate meetings
        agenda_questions: The original agenda questions
        agenda_rules: The original agenda rules
        
    Returns:
        The merge prompt
    """
    agenda_questions = agenda_questions or []
    agenda_rules = agenda_rules or []
    
    return (
        f"{MERGE_PROMPT}\n\n"
        f"{format_agenda(agenda, intro='As a reference, here is the agenda from those meetings, which must be addressed here as well:')}"
        f"{format_agenda_questions(agenda_questions, intro='As a reference, here are the agenda questions from those meetings, which must be answered here as well:')}"
        f"{format_agenda_rules(agenda_rules, intro='As a reference, here are the agenda rules from those meetings, which must be followed here as well:')}"
    )
