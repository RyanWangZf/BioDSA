"""
TrialGPT Agent for patient-to-clinical-trial matching.

Based on the TrialGPT framework:

@article{jin2024matching,
  title={Matching Patients to Clinical Trials with Large Language Models},
  author={Jin, Qiao and Wang, Zifeng and Floudas, Charalampos S and Chen, Fangyuan and 
          Gong, Changlin and Bracken-Clarke, Dara and Xue, Elisabetta and Yang, Yifan and 
          Sun, Jimeng and Lu, Zhiyong},
  journal={Nature Communications},
  year={2024}
}

The agent implements a two-stage workflow:
1. Retrieval Stage: Extract patient information and search for candidate trials
2. Matching/Ranking Stage: Evaluate eligibility and rank trials with rationales
"""
from typing import Literal, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from biodsa.agents.base_agent import BaseAgent, run_with_retry
from biodsa.agents.trialgpt.state import (
    TrialGPTAgentState,
    PatientInfo,
    TrialCandidate,
    TrialMatchResult,
    RankedTrial,
)
from biodsa.agents.trialgpt.prompt import (
    RETRIEVAL_AGENT_SYSTEM_PROMPT,
    MATCHING_AGENT_SYSTEM_PROMPT,
)
from biodsa.agents.trialgpt.tools import (
    ClinicalTrialSearchTool,
    TrialDetailsTool,
    PatientTrialMatchTool,
    get_trialgpt_tools,
)
from biodsa.sandbox.execution import ExecutionResults


class TrialGPTAgent(BaseAgent):
    """
    TrialGPT Agent for matching patients to clinical trials.
    
    This agent implements a two-stage workflow:
    1. **Retrieval Stage**: Analyzes patient clinical notes, extracts key medical information,
       and searches ClinicalTrials.gov for potentially relevant actively recruiting trials.
    2. **Matching/Ranking Stage**: Evaluates patient eligibility for each candidate trial
       and produces a ranked list with detailed rationales.
    
    Example usage:
    ```python
    agent = TrialGPTAgent(
        model_name="gpt-4o",
        api_type="openai",
        api_key="your-api-key",
        endpoint="your-endpoint"
    )
    
    patient_note = '''
    58-year-old female with metastatic non-small cell lung cancer (adenocarcinoma).
    EGFR mutation positive (exon 19 deletion). Previously treated with erlotinib
    with progression after 14 months. ECOG PS 1. No brain metastases.
    '''
    
    results = agent.go(patient_note)
    print(results.final_response)
    ```
    """
    
    name = "trialgpt"
    
    def __init__(
        self,
        model_name: str,
        api_type: str,
        api_key: str,
        endpoint: str,
        container_id: str = None,
        max_retrieval_rounds: int = 5,
        max_matching_rounds: int = 10,
        **kwargs
    ):
        """
        Initialize the TrialGPT agent.
        
        Args:
            model_name: Name of the LLM model to use
            api_type: API provider type (openai, azure, anthropic, google)
            api_key: API key for the provider
            endpoint: API endpoint
            container_id: Optional Docker container ID for sandbox execution
            max_retrieval_rounds: Maximum rounds for the retrieval stage (default: 5)
            max_matching_rounds: Maximum rounds for the matching stage (default: 10)
            **kwargs: Additional arguments passed to the base agent
        """
        # Don't use sandbox for TrialGPT (it uses API tools, not code execution)
        super().__init__(
            model_name=model_name,
            api_type=api_type,
            api_key=api_key,
            endpoint=endpoint,
            container_id=container_id,
        )
        
        self.max_retrieval_rounds = max_retrieval_rounds
        self.max_matching_rounds = max_matching_rounds
        
        # Build the agent graph
        self.agent_graph = self._create_agent_graph()
    
    def _get_retrieval_tools(self) -> List:
        """Get tools for the retrieval stage."""
        return [
            ClinicalTrialSearchTool(),
            TrialDetailsTool(),
        ]
    
    def _get_matching_tools(self) -> List:
        """Get tools for the matching stage."""
        return [
            TrialDetailsTool(),
            PatientTrialMatchTool(),
        ]
    
    def _get_all_tools(self) -> List:
        """Get all tools used by the agent."""
        return get_trialgpt_tools()
    
    def _retrieval_agent_node(
        self,
        state: TrialGPTAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """
        Retrieval stage node: Extract patient info and search for trials.
        """
        messages = state.messages
        patient_note = state.patient_note
        
        # Build system prompt with patient context
        system_content = RETRIEVAL_AGENT_SYSTEM_PROMPT + f"""

# PATIENT CLINICAL NOTE:
{patient_note}

# YOUR TASK:
1. Extract key patient information from the clinical note above
2. Use the clinical_trial_search tool to find relevant actively recruiting trials
3. If needed, use get_trial_details to get more information about promising trials
4. Compile a list of 10-30 candidate trials for the matching stage
5. When done, summarize the extracted patient information and list of candidate trials

Remember: Focus on finding trials the patient might be eligible for. Cast a wide net initially.
"""
        
        full_messages = [
            SystemMessage(content=system_content),
        ] + list(messages)
        
        # Get tools and bind to model
        tools = self._get_retrieval_tools()
        model_kwargs = config.get("configurable", {}).get("model_kwargs", {})
        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            **model_kwargs
        )
        llm_with_tools = llm.bind_tools(tools)
        
        # Generate response
        response = run_with_retry(llm_with_tools.invoke, arg=full_messages)
        
        return {
            "messages": [response],
        }
    
    def _matching_agent_node(
        self,
        state: TrialGPTAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """
        Matching/Ranking stage node: Evaluate eligibility and rank trials.
        """
        messages = state.messages
        patient_note = state.patient_note
        retrieval_summary = state.retrieval_summary
        
        # Build system prompt with context from retrieval stage
        system_content = MATCHING_AGENT_SYSTEM_PROMPT + f"""

# PATIENT CLINICAL NOTE:
{patient_note}

# RETRIEVAL STAGE SUMMARY:
{retrieval_summary if retrieval_summary else "Please review the conversation history for retrieved trials."}

# YOUR TASK:
1. Review the candidate trials identified in the retrieval stage
2. For each promising trial, use get_trial_details to get the full eligibility criteria
3. Systematically evaluate the patient against each trial's eligibility criteria
4. Provide a ranked list of the most suitable trials with detailed rationales
5. For each trial, explain:
   - Key inclusion criteria met
   - Any concerns or potential exclusion issues
   - Overall eligibility assessment (ELIGIBLE/LIKELY_ELIGIBLE/UNCERTAIN/LIKELY_INELIGIBLE/INELIGIBLE)
   - Why this trial could benefit the patient

End with a clear recommendation of the top 3-5 trials the patient should discuss with their physician.
"""
        
        full_messages = [
            SystemMessage(content=system_content),
        ] + list(messages)
        
        # Get tools and bind to model
        tools = self._get_matching_tools()
        model_kwargs = config.get("configurable", {}).get("model_kwargs", {})
        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            **model_kwargs
        )
        llm_with_tools = llm.bind_tools(tools)
        
        # Generate response
        response = run_with_retry(llm_with_tools.invoke, arg=full_messages)
        
        return {
            "messages": [response],
        }
    
    def _tool_node(
        self,
        state: TrialGPTAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """
        Execute tool calls from the agent.
        """
        tools = self._get_all_tools()
        tool_dict = {tool.name: tool for tool in tools}
        
        last_message = state.messages[-1]
        
        # Handle multiple tool calls if present
        tool_results = []
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_input = tool_call["args"]
            
            print(f"Executing tool: {tool_name}")
            
            if tool_name in tool_dict:
                tool = tool_dict[tool_name]
                try:
                    tool_output = tool._run(**tool_input)
                except Exception as e:
                    tool_output = f"Error executing {tool_name}: {str(e)}"
            else:
                tool_output = f"Unknown tool: {tool_name}"
            
            tool_results.append(
                ToolMessage(
                    content=tool_output,
                    name=tool_name,
                    tool_call_id=tool_call["id"]
                )
            )
        
        return {"messages": tool_results}
    
    def _should_continue_retrieval(
        self,
        state: TrialGPTAgentState
    ) -> Literal["tool_node", "end"]:
        """Determine if retrieval stage should continue or end."""
        last_message = state.messages[-1]
        
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return "end"
        
        return "tool_node"
    
    def _should_continue_matching(
        self,
        state: TrialGPTAgentState
    ) -> Literal["tool_node", "end"]:
        """Determine if matching stage should continue or end."""
        last_message = state.messages[-1]
        
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return "end"
        
        return "tool_node"
    
    def _extract_retrieval_summary(
        self,
        state: TrialGPTAgentState
    ) -> Dict[str, Any]:
        """Extract summary from retrieval stage for the matching stage."""
        # Get the last AI message content as the retrieval summary
        retrieval_summary = ""
        for msg in reversed(state.messages):
            if isinstance(msg, AIMessage) and msg.content:
                content = msg.content
                if isinstance(content, list):
                    content = " ".join([c.get("text", str(c)) if isinstance(c, dict) else str(c) for c in content])
                retrieval_summary = content
                break
        
        return {"retrieval_summary": retrieval_summary}
    
    def _create_agent_graph(self, debug: bool = False):
        """Create the two-stage agent workflow graph."""
        
        # Stage 1: Retrieval Agent Workflow
        retrieval_workflow = StateGraph(
            TrialGPTAgentState,
            input=TrialGPTAgentState,
            output=TrialGPTAgentState
        )
        retrieval_workflow.add_node("retrieval_agent_node", self._retrieval_agent_node)
        retrieval_workflow.add_node("tool_node", self._tool_node)
        retrieval_workflow.add_conditional_edges(
            "retrieval_agent_node",
            self._should_continue_retrieval,
            {
                "tool_node": "tool_node",
                "end": END
            }
        )
        retrieval_workflow.add_edge("tool_node", "retrieval_agent_node")
        retrieval_workflow.set_entry_point("retrieval_agent_node")
        retrieval_workflow = retrieval_workflow.compile(
            debug=debug,
            name="retrieval_workflow"
        )
        
        # Stage 2: Matching/Ranking Agent Workflow
        matching_workflow = StateGraph(
            TrialGPTAgentState,
            input=TrialGPTAgentState,
            output=TrialGPTAgentState
        )
        matching_workflow.add_node("matching_agent_node", self._matching_agent_node)
        matching_workflow.add_node("tool_node", self._tool_node)
        matching_workflow.add_conditional_edges(
            "matching_agent_node",
            self._should_continue_matching,
            {
                "tool_node": "tool_node",
                "end": END
            }
        )
        matching_workflow.add_edge("tool_node", "matching_agent_node")
        matching_workflow.set_entry_point("matching_agent_node")
        matching_workflow = matching_workflow.compile(
            debug=debug,
            name="matching_workflow"
        )
        
        # Main Workflow: Retrieval -> Extract Summary -> Matching
        main_workflow = StateGraph(
            TrialGPTAgentState,
            input=TrialGPTAgentState,
            output=TrialGPTAgentState
        )
        main_workflow.add_node("retrieval_stage", retrieval_workflow)
        main_workflow.add_node("extract_summary", self._extract_retrieval_summary)
        main_workflow.add_node("matching_stage", matching_workflow)
        
        main_workflow.add_edge("retrieval_stage", "extract_summary")
        main_workflow.add_edge("extract_summary", "matching_stage")
        main_workflow.add_edge("matching_stage", END)
        main_workflow.set_entry_point("retrieval_stage")
        
        main_workflow = main_workflow.compile(
            debug=debug,
            name=self.name
        )
        
        return main_workflow
    
    def generate(
        self,
        patient_note: str,
        verbose: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Run the TrialGPT agent on a patient note.
        
        Args:
            patient_note: The patient's clinical note
            verbose: Whether to print progress
            
        Returns:
            List of state snapshots from the agent execution
        """
        assert self.agent_graph is not None, "Agent graph is not set"
        
        if patient_note is None or patient_note.strip() == "":
            return [{"error": "patient_note is required"}]
        
        try:
            all_results = []
            inputs = {
                "messages": [HumanMessage(content=f"Please find clinical trials for this patient:\n\n{patient_note}")],
                "patient_note": patient_note,
            }
            
            # Stream the execution
            for stream_mode, chunk in self.agent_graph.stream(
                inputs,
                stream_mode=["values"],
                config={
                    "configurable": {
                        "model_kwargs": {
                            "max_completion_tokens": 8000,
                            "temperature": 1.0  # Low temperature for more consistent medical reasoning
                        }
                    },
                    "recursion_limit": 30  # Allow more rounds for thorough search and matching
                }
            ):
                if verbose:
                    last_message = chunk['messages'][-1]
                    msg_content = last_message.content
                    if isinstance(msg_content, list):
                        msg_content = " ".join([c.get("text", str(c)) if isinstance(c, dict) else str(c) for c in msg_content])
                    print("-" * 100)
                    print(f"{last_message.type}: \n\n{msg_content[:500]}...\n\n" if len(str(msg_content)) > 500 else f"{last_message.type}: \n\n{msg_content}\n\n")
                all_results.append(chunk)
            
            return all_results
            
        except Exception as e:
            print(f"Error during execution: {e}")
            raise e
    
    def go(
        self,
        patient_note: str,
        verbose: bool = True
    ) -> ExecutionResults:
        """
        Execute the TrialGPT agent and return structured results.
        
        Args:
            patient_note: The patient's clinical note
            verbose: Whether to print progress
            
        Returns:
            ExecutionResults containing the final response and execution history
        """
        results = self.generate(patient_note, verbose=verbose)
        
        if not results or "error" in results[0]:
            return ExecutionResults(
                sandbox=None,
                message_history=[],
                code_execution_results=[],
                final_response=str(results[0].get("error", "Unknown error"))
            )
        
        final_state = results[-1]
        message_history = self._format_messages(final_state['messages'])
        
        # Get the final response
        final_message = final_state['messages'][-1]
        final_response = final_message.content
        if isinstance(final_response, list):
            final_response = " ".join([
                c.get("text", str(c)) if isinstance(c, dict) else str(c) 
                for c in final_response
            ])
        
        return ExecutionResults(
            sandbox=None,
            message_history=message_history,
            code_execution_results=[],
            final_response=final_response
        )
    
