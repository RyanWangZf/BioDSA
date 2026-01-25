"""
VirtualLabAgent: Multi-agent meeting system for scientific research.

VirtualLabAgent enables AI-powered scientific discussions through team meetings
and individual meetings with automatic critic feedback. It implements the Virtual Lab
framework for collaborative AI research.

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

The agent implements two meeting types:
1. Team Meeting: Multiple agents discuss an agenda over multiple rounds
2. Individual Meeting: Single agent + Scientific Critic iterate on a solution
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal, Union
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from biodsa.agents.base_agent import BaseAgent, run_with_retry
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
)
from biodsa.agents.virtuallab.prompt import (
    team_meeting_start_prompt,
    team_meeting_team_lead_initial_prompt,
    team_meeting_team_member_prompt,
    team_meeting_team_lead_intermediate_prompt,
    team_meeting_team_lead_final_prompt,
    individual_meeting_start_prompt,
    individual_meeting_critic_prompt,
    individual_meeting_agent_prompt,
    create_merge_prompt,
    CODING_RULES,
)
from biodsa.agents.virtuallab.tools import get_virtuallab_tools, PubMedSearchTool
from biodsa.sandbox.execution import ExecutionResults


# Temperature constants
CONSISTENT_TEMPERATURE = 0.2
CREATIVE_TEMPERATURE = 0.8

# Reasoning models that only support temperature=1
REASONING_MODELS = ["gpt-5", "o1", "o3", "o1-mini", "o1-preview", "o3-mini", "o3-preview"]


def is_reasoning_model(model_name: str) -> bool:
    """Check if the model is a reasoning model that only supports temperature=1."""
    model_lower = model_name.lower()
    for rm in REASONING_MODELS:
        if rm in model_lower:
            return True
    return False


def get_safe_temperature(model_name: str, requested_temperature: float) -> float:
    """Get a safe temperature value for the given model."""
    if is_reasoning_model(model_name):
        return 1.0  # Reasoning models only support temperature=1
    return requested_temperature


class VirtualLabAgent(BaseAgent):
    """
    VirtualLabAgent: Multi-agent meeting system for scientific research.
    
    This agent orchestrates team and individual meetings between AI participants
    to discuss research agendas and solve scientific problems.
    
    Example usage:
    ```python
    agent = VirtualLabAgent(
        model_name="gpt-4o",
        api_type="azure",
        api_key="your-api-key",
        endpoint="your-endpoint",
        num_rounds=2
    )
    
    # Create participants
    pi = agent.create_participant(
        title="Principal Investigator",
        expertise="AI for biomedicine",
        goal="maximize scientific impact",
        role="lead the team"
    )
    
    ml_specialist = agent.create_participant(
        title="ML Specialist",
        expertise="deep learning",
        goal="develop novel methods",
        role="provide ML expertise"
    )
    
    # Run team meeting
    results = agent.run_team_meeting(
        team_lead=pi,
        team_members=[ml_specialist],
        agenda="Design a protein optimization pipeline"
    )
    ```
    """
    
    name = "virtuallab"
    
    def __init__(
        self,
        model_name: str,
        api_type: str,
        api_key: str,
        endpoint: str,
        container_id: str = None,
        num_rounds: int = 2,
        temperature: float = CREATIVE_TEMPERATURE,
        use_pubmed: bool = False,
        **kwargs
    ):
        """
        Initialize the VirtualLabAgent.
        
        Args:
            model_name: Name of the LLM model to use
            api_type: API provider type (openai, azure, anthropic, google)
            api_key: API key for the provider
            endpoint: API endpoint
            container_id: Optional Docker container ID (not used by VirtualLabAgent)
            num_rounds: Default number of discussion rounds (default: 2)
            temperature: Default sampling temperature (default: 0.8 for creative)
            use_pubmed: Whether to enable PubMed search tool by default
            **kwargs: Additional arguments passed to the base agent
        """
        super().__init__(
            model_name=model_name,
            api_type=api_type,
            api_key=api_key,
            endpoint=endpoint,
            container_id=container_id,
        )
        
        self.num_rounds = num_rounds
        self.temperature = temperature
        self.use_pubmed = use_pubmed
        
        # Build agent graphs
        self._team_meeting_graph = self._create_team_meeting_graph()
        self._individual_meeting_graph = self._create_individual_meeting_graph()
    
    # =========================================================================
    # Participant Creation
    # =========================================================================
    
    def create_participant(
        self,
        title: str,
        expertise: str,
        goal: str,
        role: str,
        model_name: Optional[str] = None
    ) -> Participant:
        """
        Create a new participant for meetings.
        
        Args:
            title: The participant's title (e.g., "Principal Investigator")
            expertise: Area of expertise
            goal: The participant's goal
            role: The participant's role in the team
            model_name: Optional model override for this participant
            
        Returns:
            A new Participant instance
        """
        return Participant(
            title=title,
            expertise=expertise,
            goal=goal,
            role=role,
            model_name=model_name or self.model_name
        )
    
    @staticmethod
    def get_predefined_participant(name: str) -> Participant:
        """
        Get a predefined participant by name.
        
        Args:
            name: One of "pi", "critic", "ml", "bio", "immunologist"
            
        Returns:
            The predefined Participant
        """
        participants = {
            "pi": PRINCIPAL_INVESTIGATOR,
            "critic": SCIENTIFIC_CRITIC,
            "ml": MACHINE_LEARNING_SPECIALIST,
            "bio": COMPUTATIONAL_BIOLOGIST,
            "immunologist": IMMUNOLOGIST,
        }
        if name.lower() not in participants:
            raise ValueError(f"Unknown predefined participant: {name}. "
                           f"Available: {list(participants.keys())}")
        return participants[name.lower()]
    
    # =========================================================================
    # Team Meeting Graph Nodes
    # =========================================================================
    
    def _get_participant_model(self, participant: Participant, config: RunnableConfig):
        """Get the LLM for a specific participant."""
        model_name = participant.model_name or self.model_name
        model_kwargs = config.get("configurable", {}).get("model_kwargs", {})
        
        return self._get_model(
            api=self.api_type,
            model_name=model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            **model_kwargs
        )
    
    def _initialize_team_meeting_node(
        self,
        state: VirtualLabState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Initialize the team meeting with the start prompt."""
        team_lead = state.get_team_lead()
        team_members = state.get_team_members()
        
        print("=" * 60)
        print("Virtual Lab Team Meeting")
        print("=" * 60)
        print(f"Team Lead: {team_lead.title}")
        print(f"Team Members: {', '.join(m.title for m in team_members)}")
        print(f"Rounds: {state.num_rounds}")
        print("=" * 60)
        
        # Generate start prompt
        start_prompt = team_meeting_start_prompt(
            team_lead=team_lead,
            team_members=team_members,
            agenda=state.agenda,
            agenda_questions=state.agenda_questions,
            agenda_rules=state.agenda_rules,
            summaries=state.meeting_context.summaries,
            contexts=state.meeting_context.contexts,
            num_rounds=state.num_rounds,
        )
        
        return {
            "messages": [HumanMessage(content=start_prompt)],
            "discussion": [MeetingMessage(agent="User", message=start_prompt)],
            "phase": "team_lead_initial",
            "current_round": 1,
            "current_member_index": 0,
        }
    
    def _team_lead_initial_node(
        self,
        state: VirtualLabState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Team lead provides initial thoughts."""
        team_lead = state.get_team_lead()
        
        print(f"\n[{team_lead.title}] Initial thoughts...")
        
        # Add prompt
        prompt = team_meeting_team_lead_initial_prompt(team_lead)
        messages = list(state.messages) + [HumanMessage(content=prompt)]
        discussion = list(state.discussion) + [MeetingMessage(agent="User", message=prompt)]
        
        # Get response
        llm = self._get_participant_model(team_lead, config)
        agent_messages = [SystemMessage(content=team_lead.system_prompt)] + messages
        
        response = run_with_retry(llm.invoke, arg=agent_messages)
        response_content = response.content if isinstance(response.content, str) else str(response.content)
        
        print(f"[{team_lead.title}] Response: {response_content[:200]}...")
        
        return {
            "messages": messages + [AIMessage(content=response_content)],
            "discussion": discussion + [MeetingMessage(agent=team_lead.title, message=response_content)],
            "phase": "team_member_response",
        }
    
    def _team_member_response_node(
        self,
        state: VirtualLabState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """A team member provides their response."""
        team_members = state.get_team_members()
        current_member = team_members[state.current_member_index]
        
        print(f"\n[{current_member.title}] Round {state.current_round}/{state.num_rounds}...")
        
        # Add prompt
        prompt = team_meeting_team_member_prompt(
            team_member=current_member,
            round_num=state.current_round,
            num_rounds=state.num_rounds
        )
        messages = list(state.messages) + [HumanMessage(content=prompt)]
        discussion = list(state.discussion) + [MeetingMessage(agent="User", message=prompt)]
        
        # Get response with optional tools
        llm = self._get_participant_model(current_member, config)
        tools = get_virtuallab_tools(use_pubmed=state.use_pubmed) if state.use_pubmed else []
        
        agent_messages = [SystemMessage(content=current_member.system_prompt)] + messages
        
        if tools:
            llm_with_tools = llm.bind_tools(tools)
            response = run_with_retry(llm_with_tools.invoke, arg=agent_messages)
            
            # Handle tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                messages = messages + [response]
                for tool_call in response.tool_calls:
                    tool = PubMedSearchTool()
                    tool_result = tool._run(**tool_call["args"])
                    messages.append(ToolMessage(
                        content=tool_result,
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"]
                    ))
                    discussion.append(MeetingMessage(agent="Tool", message=tool_result))
                
                # Get final response after tool use
                agent_messages = [SystemMessage(content=current_member.system_prompt)] + messages
                response = run_with_retry(llm.invoke, arg=agent_messages)
        else:
            response = run_with_retry(llm.invoke, arg=agent_messages)
        
        response_content = response.content if isinstance(response.content, str) else str(response.content)
        
        print(f"[{current_member.title}] Response: {response_content[:200]}...")
        
        # Advance to next member or synthesize
        next_member_index = state.current_member_index + 1
        
        return {
            "messages": messages + [AIMessage(content=response_content)],
            "discussion": discussion + [MeetingMessage(agent=current_member.title, message=response_content)],
            "current_member_index": next_member_index,
        }
    
    def _check_members_done(self, state: VirtualLabState) -> Literal["team_member_response", "team_lead_synthesize"]:
        """Check if all team members have responded in this round."""
        team_members = state.get_team_members()
        if state.current_member_index < len(team_members):
            return "team_member_response"
        return "team_lead_synthesize"
    
    def _team_lead_synthesize_node(
        self,
        state: VirtualLabState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Team lead synthesizes the round's discussion."""
        team_lead = state.get_team_lead()
        
        print(f"\n[{team_lead.title}] Synthesizing round {state.current_round}...")
        
        # Add prompt
        prompt = team_meeting_team_lead_intermediate_prompt(
            team_lead=team_lead,
            round_num=state.current_round,
            num_rounds=state.num_rounds
        )
        messages = list(state.messages) + [HumanMessage(content=prompt)]
        discussion = list(state.discussion) + [MeetingMessage(agent="User", message=prompt)]
        
        # Get response
        llm = self._get_participant_model(team_lead, config)
        agent_messages = [SystemMessage(content=team_lead.system_prompt)] + messages
        
        response = run_with_retry(llm.invoke, arg=agent_messages)
        response_content = response.content if isinstance(response.content, str) else str(response.content)
        
        print(f"[{team_lead.title}] Synthesis: {response_content[:200]}...")
        
        return {
            "messages": messages + [AIMessage(content=response_content)],
            "discussion": discussion + [MeetingMessage(agent=team_lead.title, message=response_content)],
            "current_round": state.current_round + 1,
            "current_member_index": 0,
        }
    
    def _check_rounds_done(self, state: VirtualLabState) -> Literal["team_member_response", "team_lead_final"]:
        """Check if all rounds are complete."""
        if state.current_round <= state.num_rounds:
            return "team_member_response"
        return "team_lead_final"
    
    def _team_lead_final_node(
        self,
        state: VirtualLabState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Team lead provides final summary."""
        team_lead = state.get_team_lead()
        
        print(f"\n[{team_lead.title}] Final summary...")
        
        # Add prompt
        prompt = team_meeting_team_lead_final_prompt(
            team_lead=team_lead,
            agenda=state.agenda,
            agenda_questions=state.agenda_questions,
            agenda_rules=state.agenda_rules
        )
        messages = list(state.messages) + [HumanMessage(content=prompt)]
        discussion = list(state.discussion) + [MeetingMessage(agent="User", message=prompt)]
        
        # Get response with consistent temperature for summary
        model_name = team_lead.model_name or self.model_name
        llm = self._get_model(
            api=self.api_type,
            model_name=model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            temperature=get_safe_temperature(model_name, CONSISTENT_TEMPERATURE),
        )
        agent_messages = [SystemMessage(content=team_lead.system_prompt)] + messages
        
        response = run_with_retry(llm.invoke, arg=agent_messages)
        response_content = response.content if isinstance(response.content, str) else str(response.content)
        
        print(f"\n{'=' * 60}")
        print("MEETING SUMMARY")
        print("=" * 60)
        print(response_content[:1000])
        if len(response_content) > 1000:
            print("...")
        
        return {
            "messages": messages + [AIMessage(content=response_content)],
            "discussion": discussion + [MeetingMessage(agent=team_lead.title, message=response_content)],
            "summary": response_content,
            "phase": "complete",
        }
    
    def _create_team_meeting_graph(self):
        """Create the LangGraph workflow for team meetings."""
        workflow = StateGraph(VirtualLabState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_team_meeting_node)
        workflow.add_node("team_lead_initial", self._team_lead_initial_node)
        workflow.add_node("team_member_response", self._team_member_response_node)
        workflow.add_node("team_lead_synthesize", self._team_lead_synthesize_node)
        workflow.add_node("team_lead_final", self._team_lead_final_node)
        
        # Add edges
        workflow.add_edge("initialize", "team_lead_initial")
        workflow.add_edge("team_lead_initial", "team_member_response")
        
        workflow.add_conditional_edges(
            "team_member_response",
            self._check_members_done,
            {
                "team_member_response": "team_member_response",
                "team_lead_synthesize": "team_lead_synthesize",
            }
        )
        
        workflow.add_conditional_edges(
            "team_lead_synthesize",
            self._check_rounds_done,
            {
                "team_member_response": "team_member_response",
                "team_lead_final": "team_lead_final",
            }
        )
        
        workflow.add_edge("team_lead_final", END)
        
        workflow.set_entry_point("initialize")
        
        return workflow.compile(name="team_meeting")
    
    # =========================================================================
    # Individual Meeting Graph Nodes
    # =========================================================================
    
    def _initialize_individual_meeting_node(
        self,
        state: VirtualLabState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Initialize the individual meeting."""
        team_member = state.get_team_member()
        
        print("=" * 60)
        print("Virtual Lab Individual Meeting")
        print("=" * 60)
        print(f"Participant: {team_member.title}")
        print(f"Critic Rounds: {state.num_rounds}")
        print("=" * 60)
        
        # Generate start prompt
        start_prompt = individual_meeting_start_prompt(
            team_member=team_member,
            agenda=state.agenda,
            agenda_questions=state.agenda_questions,
            agenda_rules=state.agenda_rules,
            summaries=state.meeting_context.summaries,
            contexts=state.meeting_context.contexts,
        )
        
        return {
            "messages": [HumanMessage(content=start_prompt)],
            "discussion": [MeetingMessage(agent="User", message=start_prompt)],
            "phase": "individual_agent",
            "current_round": 1,
        }
    
    def _individual_agent_node(
        self,
        state: VirtualLabState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """The individual agent provides their response."""
        team_member = state.get_team_member()
        
        is_initial = state.current_round == 1 and state.phase == "individual_agent"
        action = "Initial response" if is_initial else f"Revision {state.current_round}"
        print(f"\n[{team_member.title}] {action}...")
        
        messages = list(state.messages)
        discussion = list(state.discussion)
        
        # Get response with optional tools
        llm = self._get_participant_model(team_member, config)
        tools = get_virtuallab_tools(use_pubmed=state.use_pubmed) if state.use_pubmed else []
        
        agent_messages = [SystemMessage(content=team_member.system_prompt)] + messages
        
        if tools:
            llm_with_tools = llm.bind_tools(tools)
            response = run_with_retry(llm_with_tools.invoke, arg=agent_messages)
            
            # Handle tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                messages = messages + [response]
                for tool_call in response.tool_calls:
                    tool = PubMedSearchTool()
                    tool_result = tool._run(**tool_call["args"])
                    messages.append(ToolMessage(
                        content=tool_result,
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"]
                    ))
                    discussion.append(MeetingMessage(agent="Tool", message=tool_result))
                
                agent_messages = [SystemMessage(content=team_member.system_prompt)] + messages
                response = run_with_retry(llm.invoke, arg=agent_messages)
        else:
            response = run_with_retry(llm.invoke, arg=agent_messages)
        
        response_content = response.content if isinstance(response.content, str) else str(response.content)
        
        print(f"[{team_member.title}] Response: {response_content[:200]}...")
        
        return {
            "messages": messages + [AIMessage(content=response_content)],
            "discussion": discussion + [MeetingMessage(agent=team_member.title, message=response_content)],
            "phase": "individual_critic",
        }
    
    def _individual_critic_node(
        self,
        state: VirtualLabState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """The scientific critic provides feedback."""
        team_member = state.get_team_member()
        critic = SCIENTIFIC_CRITIC
        
        print(f"\n[{critic.title}] Round {state.current_round}/{state.num_rounds}...")
        
        # Add prompt
        prompt = individual_meeting_critic_prompt(critic=critic, agent=team_member)
        messages = list(state.messages) + [HumanMessage(content=prompt)]
        discussion = list(state.discussion) + [MeetingMessage(agent="User", message=prompt)]
        
        # Get response
        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            temperature=get_safe_temperature(self.model_name, CONSISTENT_TEMPERATURE),
        )
        agent_messages = [SystemMessage(content=critic.system_prompt)] + messages
        
        response = run_with_retry(llm.invoke, arg=agent_messages)
        response_content = response.content if isinstance(response.content, str) else str(response.content)
        
        print(f"[{critic.title}] Feedback: {response_content[:200]}...")
        
        return {
            "messages": messages + [AIMessage(content=response_content)],
            "discussion": discussion + [MeetingMessage(agent=critic.title, message=response_content)],
            "current_round": state.current_round + 1,
        }
    
    def _check_individual_rounds_done(self, state: VirtualLabState) -> Literal["individual_revise", "individual_complete"]:
        """Check if all critic rounds are complete."""
        if state.current_round <= state.num_rounds:
            return "individual_revise"
        return "individual_complete"
    
    def _individual_revise_node(
        self,
        state: VirtualLabState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """The agent revises based on critic feedback."""
        team_member = state.get_team_member()
        critic = SCIENTIFIC_CRITIC
        
        # Add prompt
        prompt = individual_meeting_agent_prompt(critic=critic, agent=team_member)
        messages = list(state.messages) + [HumanMessage(content=prompt)]
        discussion = list(state.discussion) + [MeetingMessage(agent="User", message=prompt)]
        
        return {
            "messages": messages,
            "discussion": discussion,
            "phase": "individual_agent",
        }
    
    def _individual_complete_node(
        self,
        state: VirtualLabState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Complete the individual meeting."""
        # The last agent response is the summary
        last_agent_msg = None
        for msg in reversed(state.discussion):
            if msg.agent != "User" and msg.agent != "Tool" and msg.agent != SCIENTIFIC_CRITIC.title:
                last_agent_msg = msg.message
                break
        
        summary = last_agent_msg or ""
        
        print(f"\n{'=' * 60}")
        print("MEETING COMPLETE")
        print("=" * 60)
        print(summary[:1000])
        if len(summary) > 1000:
            print("...")
        
        return {
            "summary": summary,
            "phase": "complete",
        }
    
    def _create_individual_meeting_graph(self):
        """Create the LangGraph workflow for individual meetings."""
        workflow = StateGraph(VirtualLabState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_individual_meeting_node)
        workflow.add_node("individual_agent", self._individual_agent_node)
        workflow.add_node("individual_critic", self._individual_critic_node)
        workflow.add_node("individual_revise", self._individual_revise_node)
        workflow.add_node("individual_complete", self._individual_complete_node)
        
        # Add edges
        workflow.add_edge("initialize", "individual_agent")
        workflow.add_edge("individual_agent", "individual_critic")
        
        workflow.add_conditional_edges(
            "individual_critic",
            self._check_individual_rounds_done,
            {
                "individual_revise": "individual_revise",
                "individual_complete": "individual_complete",
            }
        )
        
        workflow.add_edge("individual_revise", "individual_agent")
        workflow.add_edge("individual_complete", END)
        
        workflow.set_entry_point("initialize")
        
        return workflow.compile(name="individual_meeting")
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    def run_team_meeting(
        self,
        team_lead: Participant,
        team_members: List[Participant],
        agenda: str,
        agenda_questions: List[str] = None,
        agenda_rules: List[str] = None,
        num_rounds: int = None,
        temperature: float = None,
        summaries: List[str] = None,
        contexts: List[str] = None,
        use_pubmed: bool = None,
    ) -> ExecutionResults:
        """
        Run a team meeting with multiple AI participants.
        
        Args:
            team_lead: The team lead participant
            team_members: List of team member participants
            agenda: The meeting agenda/topic
            agenda_questions: Specific questions to answer
            agenda_rules: Rules to follow (e.g., coding standards)
            num_rounds: Number of discussion rounds (default: self.num_rounds)
            temperature: Sampling temperature (default: self.temperature)
            summaries: Summaries from previous meetings
            contexts: Additional context documents
            use_pubmed: Enable PubMed search tool
            
        Returns:
            ExecutionResults with the meeting summary
        """
        # Validate inputs
        if team_lead in team_members:
            raise ValueError("Team lead must not be in team members list")
        if len(set(m.title for m in team_members)) != len(team_members):
            raise ValueError("Team members must have unique titles")
        
        # Build initial state
        initial_state = VirtualLabState(
            meeting_type="team",
            agenda=agenda,
            agenda_questions=agenda_questions or [],
            agenda_rules=agenda_rules or [],
            team_lead=team_lead.model_dump(),
            team_members=[m.model_dump() for m in team_members],
            num_rounds=num_rounds or self.num_rounds,
            temperature=temperature or self.temperature,
            use_pubmed=use_pubmed if use_pubmed is not None else self.use_pubmed,
            meeting_context=MeetingContext(
                summaries=summaries or [],
                contexts=contexts or []
            ),
        )
        
        # Run the graph
        final_state = self._team_meeting_graph.invoke(
            initial_state,
            config={
                "configurable": {
                    "model_kwargs": {
                        "temperature": get_safe_temperature(self.model_name, initial_state.temperature),
                    }
                },
                "recursion_limit": 100,
            }
        )
        
        # Format results
        message_history = [
            {"role": "system" if msg.agent == "User" else "assistant", "content": msg.message}
            for msg in final_state.get("discussion", [])
        ]
        
        return ExecutionResults(
            sandbox=None,
            message_history=message_history,
            code_execution_results=[],
            final_response=final_state.get("summary", "")
        )
    
    def run_individual_meeting(
        self,
        team_member: Participant,
        agenda: str,
        agenda_questions: List[str] = None,
        agenda_rules: List[str] = None,
        num_rounds: int = None,
        temperature: float = None,
        summaries: List[str] = None,
        contexts: List[str] = None,
        use_pubmed: bool = None,
    ) -> ExecutionResults:
        """
        Run an individual meeting with a participant and Scientific Critic.
        
        The participant provides an initial response, then the Scientific Critic
        provides feedback. This iterates for the specified number of rounds.
        
        Args:
            team_member: The participant for the meeting
            agenda: The meeting agenda/topic
            agenda_questions: Specific questions to answer
            agenda_rules: Rules to follow (e.g., CODING_RULES for code tasks)
            num_rounds: Number of critic-revision rounds (default: self.num_rounds)
            temperature: Sampling temperature (default: self.temperature)
            summaries: Summaries from previous meetings
            contexts: Additional context documents
            use_pubmed: Enable PubMed search tool
            
        Returns:
            ExecutionResults with the final response
        """
        # Build initial state
        initial_state = VirtualLabState(
            meeting_type="individual",
            agenda=agenda,
            agenda_questions=agenda_questions or [],
            agenda_rules=agenda_rules or [],
            team_member=team_member.model_dump(),
            num_rounds=num_rounds or self.num_rounds,
            temperature=temperature or self.temperature,
            use_pubmed=use_pubmed if use_pubmed is not None else self.use_pubmed,
            meeting_context=MeetingContext(
                summaries=summaries or [],
                contexts=contexts or []
            ),
        )
        
        # Run the graph
        final_state = self._individual_meeting_graph.invoke(
            initial_state,
            config={
                "configurable": {
                    "model_kwargs": {
                        "temperature": get_safe_temperature(self.model_name, initial_state.temperature),
                    }
                },
                "recursion_limit": 100,
            }
        )
        
        # Format results
        message_history = [
            {"role": "system" if msg.agent == "User" else "assistant", "content": msg.message}
            for msg in final_state.get("discussion", [])
        ]
        
        return ExecutionResults(
            sandbox=None,
            message_history=message_history,
            code_execution_results=[],
            final_response=final_state.get("summary", "")
        )
    
    def merge_summaries(
        self,
        summaries: List[str],
        agenda: str,
        agenda_questions: List[str] = None,
        agenda_rules: List[str] = None,
        moderator: Participant = None,
    ) -> str:
        """
        Merge multiple meeting summaries into a single coherent summary.
        
        This is useful when running multiple parallel meetings and needing
        to combine the best components of each.
        
        Args:
            summaries: List of summaries to merge
            agenda: The original agenda
            agenda_questions: The original agenda questions
            agenda_rules: The original agenda rules
            moderator: The participant to moderate the merge (default: PI)
            
        Returns:
            The merged summary
        """
        if not summaries:
            return ""
        
        if len(summaries) == 1:
            return summaries[0]
        
        moderator = moderator or PRINCIPAL_INVESTIGATOR
        
        # Build merge prompt
        merge_prompt = create_merge_prompt(
            agenda=agenda,
            agenda_questions=agenda_questions or [],
            agenda_rules=agenda_rules or []
        )
        
        # Format summaries
        from biodsa.agents.virtuallab.prompt import format_references
        formatted_summaries = format_references(
            references=summaries,
            reference_type="summary",
            intro="Here are the summaries from separate meetings:"
        )
        
        full_prompt = f"{formatted_summaries}\n\n{merge_prompt}"
        
        # Get merged summary
        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            temperature=get_safe_temperature(self.model_name, CONSISTENT_TEMPERATURE),
        )
        
        messages = [
            SystemMessage(content=moderator.system_prompt),
            HumanMessage(content=full_prompt)
        ]
        
        response = run_with_retry(llm.invoke, arg=messages)
        return response.content if isinstance(response.content, str) else str(response.content)
    
    def save_meeting(
        self,
        results: ExecutionResults,
        save_dir: Union[str, Path],
        save_name: str = "discussion"
    ) -> None:
        """
        Save meeting results to JSON and Markdown files.
        
        Args:
            results: The ExecutionResults from a meeting
            save_dir: Directory to save the files
            save_name: Base name for the files (without extension)
        """
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert message history to discussion format
        discussion = []
        for msg in results.message_history:
            discussion.append({
                "agent": "User" if msg.get("role") == "system" else "Agent",
                "message": msg.get("content", "")
            })
        
        # Save as JSON
        with open(save_dir / f"{save_name}.json", "w") as f:
            json.dump(discussion, f, indent=4)
        
        # Save as Markdown
        with open(save_dir / f"{save_name}.md", "w", encoding="utf-8") as f:
            for turn in discussion:
                f.write(f"## {turn['agent']}\n\n{turn['message']}\n\n")
        
        print(f"Saved meeting to {save_dir / save_name}.json and {save_dir / save_name}.md")
    
    def go(
        self,
        input_query: str,
        previous_results: Optional[Union[ExecutionResults, List[ExecutionResults]]] = None,
        meeting_type: Literal["team", "individual"] = "individual",
        **kwargs
    ) -> ExecutionResults:
        """
        Run a meeting based on a query, optionally using previous meeting results.
        
        This enables chaining meetings where each builds on the previous:
        
        ```python
        res1 = agent.go("Define the project approach", None)
        res2 = agent.go("Implement the solution", res1)
        res3 = agent.go("Review and refine", res2)
        ```
        
        Args:
            input_query: The agenda/topic for the meeting
            previous_results: Previous meeting results to use as context.
                Can be None, a single ExecutionResults, or a list of ExecutionResults.
            meeting_type: Type of meeting ("team" or "individual")
            **kwargs: Additional arguments for the meeting
            
        Returns:
            ExecutionResults with the meeting outcome
        """
        # Convert previous_results to summaries list
        summaries = kwargs.pop("summaries", [])
        if previous_results is not None:
            if isinstance(previous_results, list):
                summaries.extend([r.final_response for r in previous_results])
            else:
                summaries.append(previous_results.final_response)
        
        if meeting_type == "team":
            team_lead = kwargs.pop("team_lead", PRINCIPAL_INVESTIGATOR)
            team_members = kwargs.pop("team_members", [MACHINE_LEARNING_SPECIALIST, COMPUTATIONAL_BIOLOGIST])
            return self.run_team_meeting(
                team_lead=team_lead,
                team_members=team_members,
                agenda=input_query,
                summaries=summaries,
                **kwargs
            )
        else:
            team_member = kwargs.pop("team_member", MACHINE_LEARNING_SPECIALIST)
            return self.run_individual_meeting(
                team_member=team_member,
                agenda=input_query,
                summaries=summaries,
                **kwargs
            )
    
    def run_workflow(
        self,
        phases: List[Dict[str, Any]],
        save_dir: Optional[Union[str, Path]] = None,
        verbose: bool = True,
    ) -> Dict[str, ExecutionResults]:
        """
        Run a multi-phase workflow where each phase can use summaries from previous phases.
        
        This enables complex research workflows like the Virtual Lab nanobody design
        pipeline, where multiple meetings build on each other's outputs.
        
        Args:
            phases: List of phase configurations. Each phase is a dict with:
                - name: str - Name of the phase (used as key in results)
                - meeting_type: "team" or "individual"
                - agenda: str - The meeting agenda
                - team_lead: Participant (for team meetings)
                - team_members: List[Participant] (for team meetings)
                - team_member: Participant (for individual meetings)
                - agenda_questions: List[str] (optional)
                - agenda_rules: List[str] (optional)
                - use_summaries_from: List[str] (optional) - Phase names to use summaries from
                - num_rounds: int (optional)
                - temperature: float (optional)
            save_dir: Optional directory to save meeting results
            verbose: Whether to print progress
            
        Returns:
            Dict mapping phase names to ExecutionResults
            
        Example:
            ```python
            results = agent.run_workflow([
                {
                    "name": "team_selection",
                    "meeting_type": "individual",
                    "team_member": pi,
                    "agenda": "Select a team of 3 scientists for this project",
                },
                {
                    "name": "project_spec",
                    "meeting_type": "team",
                    "team_lead": pi,
                    "team_members": [ml_specialist, bio_expert],
                    "agenda": "Define the project approach",
                    "use_summaries_from": ["team_selection"],
                },
            ])
            ```
        """
        results: Dict[str, ExecutionResults] = {}
        
        for i, phase in enumerate(phases):
            phase_name = phase.get("name", f"phase_{i+1}")
            meeting_type = phase.get("meeting_type", "individual")
            agenda = phase.get("agenda", "")
            
            if verbose:
                print(f"\n{'#' * 70}")
                print(f"# PHASE {i+1}: {phase_name}")
                print(f"{'#' * 70}")
            
            # Collect summaries from previous phases
            summaries = []
            use_summaries_from = phase.get("use_summaries_from", [])
            for prev_phase in use_summaries_from:
                if prev_phase in results:
                    summaries.append(results[prev_phase].final_response)
                    if verbose:
                        print(f"  Using summary from: {prev_phase}")
            
            # Add any explicit summaries
            if "summaries" in phase:
                summaries.extend(phase["summaries"])
            
            # Run the meeting
            if meeting_type == "team":
                team_lead = phase.get("team_lead", PRINCIPAL_INVESTIGATOR)
                team_members = phase.get("team_members", [MACHINE_LEARNING_SPECIALIST])
                
                phase_results = self.run_team_meeting(
                    team_lead=team_lead,
                    team_members=team_members,
                    agenda=agenda,
                    agenda_questions=phase.get("agenda_questions", []),
                    agenda_rules=phase.get("agenda_rules", []),
                    summaries=summaries,
                    contexts=phase.get("contexts", []),
                    num_rounds=phase.get("num_rounds"),
                    temperature=phase.get("temperature"),
                    use_pubmed=phase.get("use_pubmed"),
                )
            else:
                team_member = phase.get("team_member", MACHINE_LEARNING_SPECIALIST)
                
                phase_results = self.run_individual_meeting(
                    team_member=team_member,
                    agenda=agenda,
                    agenda_questions=phase.get("agenda_questions", []),
                    agenda_rules=phase.get("agenda_rules", []),
                    summaries=summaries,
                    contexts=phase.get("contexts", []),
                    num_rounds=phase.get("num_rounds"),
                    temperature=phase.get("temperature"),
                    use_pubmed=phase.get("use_pubmed"),
                )
            
            results[phase_name] = phase_results
            
            # Save if directory specified
            if save_dir:
                self.save_meeting(
                    results=phase_results,
                    save_dir=Path(save_dir) / phase_name,
                    save_name="discussion"
                )
            
            if verbose:
                print(f"\n{'=' * 50}")
                print(f"Phase '{phase_name}' complete")
                print(f"Summary preview: {phase_results.final_response[:300]}...")
                print(f"{'=' * 50}")
        
        return results
    
    def run_interactive_workflow(
        self,
        initial_agenda: str,
        meeting_type: Literal["team", "individual"] = "individual",
        max_rounds: int = 10,
        **kwargs
    ) -> List[ExecutionResults]:
        """
        Run an interactive workflow where the user provides input between meetings.
        
        After each meeting, the user is prompted to provide the next agenda or
        type 'done' to finish. Previous meeting summaries are automatically
        passed to subsequent meetings.
        
        Args:
            initial_agenda: The agenda for the first meeting
            meeting_type: Type of meeting ("team" or "individual")
            max_rounds: Maximum number of rounds (default: 10)
            **kwargs: Additional arguments for the meetings
            
        Returns:
            List of ExecutionResults from all meetings
        """
        all_results: List[ExecutionResults] = []
        summaries: List[str] = []
        current_agenda = initial_agenda
        
        for round_num in range(1, max_rounds + 1):
            print(f"\n{'#' * 70}")
            print(f"# ROUND {round_num}")
            print(f"{'#' * 70}")
            print(f"Agenda: {current_agenda[:200]}...")
            
            # Run the meeting
            results = self.go(
                input_query=current_agenda,
                meeting_type=meeting_type,
                summaries=summaries,
                **kwargs
            )
            
            all_results.append(results)
            summaries.append(results.final_response)
            
            print(f"\n{'=' * 50}")
            print("MEETING COMPLETE")
            print(f"{'=' * 50}")
            print(f"\nSummary:\n{results.final_response[:1000]}...")
            
            # Prompt for next agenda
            print("\n" + "-" * 50)
            print("Enter the next agenda (or 'done' to finish):")
            print("-" * 50)
            
            try:
                next_agenda = input("> ").strip()
            except EOFError:
                # Non-interactive mode
                break
            
            if next_agenda.lower() == 'done' or not next_agenda:
                print("Workflow complete!")
                break
            
            current_agenda = next_agenda
        
        return all_results
