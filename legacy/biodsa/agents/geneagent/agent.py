"""
GeneAgent: Self-verification Language Agent for Gene Set Analysis.

GeneAgent is a language agent that autonomously interacts with domain-specific
databases to annotate functions for gene sets. It implements a cascade 
self-verification mechanism to reduce hallucination and provide evidence-based
insights into gene function.

Based on the GeneAgent framework:
@article{jin2024geneagent,
  title={GeneAgent: Self-verification Language Agent for Gene Set Analysis using Domain Databases},
  author={Jin, Qiao and others},
  year={2024}
}

Reference: https://github.com/ncbi-nlp/GeneAgent

The agent implements a multi-stage workflow:
1. Initial Analysis: Generate process name and summary for gene set
2. Topic Verification: Verify claims about the process name using domain databases
3. Topic Update: Refine process name based on verification evidence
4. Analysis Verification: Verify claims about gene functions
5. Final Summary: Generate refined summary based on all verification evidence
"""
import json
import re
import time
from typing import Literal, List, Dict, Any, Optional, Union
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from biodsa.agents.base_agent import BaseAgent, run_with_retry
from biodsa.agents.geneagent.state import (
    GeneAgentState,
    VerificationWorkerState,
    GeneSetAnalysis,
)
from biodsa.agents.geneagent.prompt import (
    BASELINE_SYSTEM_PROMPT,
    BASELINE_USER_PROMPT,
    TOPIC_VERIFICATION_SYSTEM_PROMPT,
    TOPIC_CLAIM_GENERATION_PROMPT,
    TOPIC_CLAIM_INSTRUCTION,
    TOPIC_MODIFICATION_PROMPT,
    TOPIC_MODIFICATION_INSTRUCTION,
    ANALYSIS_CLAIM_GENERATION_PROMPT,
    ANALYSIS_CLAIM_INSTRUCTION,
    ANALYSIS_SUMMARIZATION_PROMPT,
    ANALYSIS_SUMMARIZATION_INSTRUCTION,
    VERIFICATION_WORKER_SYSTEM_PROMPT,
    VERIFICATION_WORKER_USER_PROMPT,
    VERIFICATION_REPORT_REQUEST,
    format_baseline_prompt,
    format_topic_claim_prompt,
    format_topic_modification_prompt,
    format_analysis_claim_prompt,
    format_analysis_summarization_prompt,
    format_verification_prompt,
)
from biodsa.agents.geneagent.tools import get_geneagent_tools
from biodsa.sandbox.execution import ExecutionResults


class GeneAgent(BaseAgent):
    """
    GeneAgent: Self-verification Language Agent for Gene Set Analysis.
    
    This agent implements a cascade verification workflow to analyze gene sets
    and provide evidence-based biological process annotations.
    
    Example usage:
    ```python
    agent = GeneAgent(
        model_name="gpt-4o",
        api_type="azure",
        api_key="your-api-key",
        endpoint="your-endpoint"
    )
    
    gene_set = "ERBB2,ERBB4,FGFR2,FGFR4,HRAS,KRAS"
    
    results = agent.go(gene_set)
    print(results.final_response)
    ```
    """
    
    name = "geneagent"
    
    def __init__(
        self,
        model_name: str,
        api_type: str,
        api_key: str,
        endpoint: str,
        container_id: str = None,
        max_verification_rounds: int = 20,
        max_claims_per_stage: int = None,
        temperature: float = 1.0,
        include_verification_reports: bool = True,
        **kwargs
    ):
        """
        Initialize the GeneAgent.
        
        Args:
            model_name: Name of the LLM model to use (e.g., 'gpt-4o', 'gpt-4', 'claude-3-opus')
            api_type: API provider type (openai, azure, anthropic, google)
            api_key: API key for the provider
            endpoint: API endpoint
            container_id: Optional Docker container ID (not used by GeneAgent)
            max_verification_rounds: Maximum tool calls per claim verification (default: 20)
            max_claims_per_stage: Maximum claims to verify per stage (default: None = all claims).
                                  Set to 1-3 for quick demos.
            temperature: LLM temperature for generation (default: 1.0)
            include_verification_reports: Include verification reports in output (default: True)
            **kwargs: Additional arguments passed to the base agent
        """
        # Initialize base agent (sandbox not needed for GeneAgent)
        super().__init__(
            model_name=model_name,
            api_type=api_type,
            api_key=api_key,
            endpoint=endpoint,
            container_id=container_id,
        )
        
        self.max_verification_rounds = max_verification_rounds
        self.max_claims_per_stage = max_claims_per_stage
        self.temperature = temperature
        self.include_verification_reports = include_verification_reports
        
        # Build the agent graph
        self.agent_graph = self._create_agent_graph()
    
    def _get_tools(self) -> List:
        """Get all tools for GeneAgent verification."""
        return get_geneagent_tools()
    
    def _normalize_gene_set(self, gene_set: Union[str, List[str]]) -> str:
        """Normalize gene set input to comma-separated string without spaces."""
        if isinstance(gene_set, list):
            gene_set = ",".join(gene_set)
        # Clean up: remove spaces, handle various delimiters
        gene_set = gene_set.replace("/", ",").replace(" ", ",")
        gene_set = ",".join([g.strip() for g in gene_set.split(",") if g.strip()])
        return gene_set
    
    def _parse_claims(self, response_content: str) -> List[str]:
        """Parse claims from LLM response (expects JSON list format)."""
        try:
            # Try to extract JSON list from response
            # Handle cases where response might have extra text
            content = response_content.strip()
            
            # Find JSON list in response
            start_idx = content.find("[")
            end_idx = content.rfind("]") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                claims = json.loads(json_str)
                if isinstance(claims, list):
                    return [str(c) for c in claims]
            
            # Fallback: try to parse entire response as JSON
            claims = json.loads(content)
            if isinstance(claims, list):
                return [str(c) for c in claims]
                
        except json.JSONDecodeError:
            pass
        
        # Fallback: return empty list if parsing fails
        return []
    
    def _extract_process_name(self, summary: str) -> str:
        """Extract process name from summary (after 'Process: ')."""
        lines = summary.strip().split("\n")
        for line in lines:
            if line.startswith("Process:"):
                return line.split("Process:")[-1].strip()
        return ""
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text to remove non-ASCII characters (like original GeneAgent)."""
        pattern = re.compile(r'^[a-zA-Z0-9,.;?!*()_-]+$')
        if not re.match(pattern, text):
            return re.sub(r'[^a-zA-Z0-9,.;?!*()_ -]+', "_", text)
        return text
    
    # =========================================================================
    # Stage 1: Initial Analysis
    # =========================================================================
    
    def _generate_initial_analysis_node(
        self,
        state: GeneAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Generate initial process name and analysis for the gene set."""
        gene_set = state.gene_set
        
        print("=" * 50)
        print("Stage 1: Generating Initial Analysis")
        print("=" * 50)
        
        # Build prompt
        prompt = format_baseline_prompt(gene_set)
        
        messages = [
            SystemMessage(content=BASELINE_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        # Get model
        model_kwargs = config.get("configurable", {}).get("model_kwargs", {})
        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            temperature=self.temperature,
            **model_kwargs
        )
        
        # Generate response
        response = run_with_retry(llm.invoke, arg=messages)
        summary = response.content if isinstance(response.content, str) else str(response.content)
        
        # Extract process name
        process_name = self._extract_process_name(summary)
        
        print(f"\nInitial Process: {process_name}")
        print(f"\nInitial Summary:\n{summary[:500]}..." if len(summary) > 500 else f"\nInitial Summary:\n{summary}")
        
        initial_analysis = GeneSetAnalysis(
            process_name=process_name,
            summary=summary,
            raw_response=summary
        )
        
        # Store messages for conversation continuity
        return {
            "messages": messages + [response],
            "initial_analysis": initial_analysis,
        }
    
    # =========================================================================
    # Stage 2: Topic Verification
    # =========================================================================
    
    def _generate_topic_claims_node(
        self,
        state: GeneAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Generate claims about the process name to verify."""
        gene_set = state.gene_set
        process_name = state.initial_analysis.process_name
        
        print("=" * 50)
        print("Stage 2: Generating Topic Claims")
        print("=" * 50)
        
        # Build prompt
        prompt = format_topic_claim_prompt(gene_set, process_name)
        
        messages = [
            SystemMessage(content=TOPIC_VERIFICATION_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        model_kwargs = config.get("configurable", {}).get("model_kwargs", {})
        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            temperature=self.temperature,
            **model_kwargs
        )
        
        response = run_with_retry(llm.invoke, arg=messages)
        claims = self._parse_claims(response.content)
        
        # Limit claims for quick demos
        if self.max_claims_per_stage and len(claims) > self.max_claims_per_stage:
            print(f"\nLimiting claims from {len(claims)} to {self.max_claims_per_stage} (quick mode)")
            claims = claims[:self.max_claims_per_stage]
        
        print(f"\nTopic Claims to Verify: {claims}")
        
        return {
            "topic_claims": claims,
            "verification_stage": "topic",
            "current_claim_index": 0,
        }
    
    def _verify_claims_node(
        self,
        state: GeneAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Verify current claim using domain database tools."""
        # Determine which claims to verify based on stage
        if state.verification_stage == "topic":
            claims = state.topic_claims
            current_report = state.topic_verification_report
        else:  # analysis
            claims = state.analysis_claims
            current_report = state.analysis_verification_report
        
        claim_idx = state.current_claim_index
        
        if claim_idx >= len(claims):
            # All claims verified
            return {"current_claim_index": claim_idx}
        
        claim = claims[claim_idx]
        claim = self._sanitize_text(claim)
        
        print(f"\nVerifying claim {claim_idx + 1}/{len(claims)}: {claim[:100]}...")
        
        # Run verification worker
        verification_result = self._run_verification_worker(claim, state.gene_set, config)
        
        # Append to report
        new_report = current_report + f"Original_claim:{claim}\nVerified_claim:{verification_result}\n\n"
        
        print(f"Verification result: {verification_result[:200]}...")
        
        if state.verification_stage == "topic":
            return {
                "topic_verification_report": new_report,
                "current_claim_index": claim_idx + 1,
                "total_claims_verified": state.total_claims_verified + 1,
            }
        else:
            return {
                "analysis_verification_report": new_report,
                "current_claim_index": claim_idx + 1,
                "total_claims_verified": state.total_claims_verified + 1,
            }
    
    def _run_verification_worker(
        self,
        claim: str,
        gene_set: str,
        config: RunnableConfig
    ) -> str:
        """Run the verification worker sub-agent to verify a single claim."""
        tools = self._get_tools()
        tool_dict = {tool.name: tool for tool in tools}
        
        # Build prompt
        system_content = VERIFICATION_WORKER_SYSTEM_PROMPT
        user_content = format_verification_prompt(claim)
        
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=user_content)
        ]
        
        model_kwargs = config.get("configurable", {}).get("model_kwargs", {})
        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            temperature=self.temperature,
            **model_kwargs
        )
        llm_with_tools = llm.bind_tools(tools)
        
        # Verification loop (like original AgentPhD)
        for loop in range(self.max_verification_rounds):
            time.sleep(0.5)  # Rate limiting
            
            response = run_with_retry(llm_with_tools.invoke, arg=messages)
            messages.append(response)
            
            # Check if response contains tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    try:
                        function_name = tool_call["name"]
                        function_params = tool_call["args"]
                        
                        if function_name in tool_dict:
                            tool = tool_dict[function_name]
                            function_response = tool._run(**function_params)
                            function_response = f"Function has been called with params {function_params}, and returns {function_response}."
                        else:
                            function_response = f"Unknown function: {function_name}"
                        
                        messages.append(
                            ToolMessage(
                                content=function_response,
                                name=function_name,
                                tool_call_id=tool_call["id"]
                            )
                        )
                    except Exception as e:
                        messages.append(
                            ToolMessage(
                                content=f"Function call error: {str(e)}. Please try again.",
                                name=tool_call.get("name", "unknown"),
                                tool_call_id=tool_call.get("id", "unknown")
                            )
                        )
            else:
                # No tool calls - check for Report
                content = response.content if isinstance(response.content, str) else str(response.content)
                
                if "Report:" in content:
                    report = content.split("Report:")[-1].strip()
                    return self._sanitize_text(report)
                else:
                    # Ask for report
                    messages.append(
                        HumanMessage(content=VERIFICATION_REPORT_REQUEST)
                    )
        
        return "Failed to verify claim within maximum rounds."
    
    def _should_continue_verification(
        self,
        state: GeneAgentState
    ) -> Literal["verify_claims", "update_topic", "update_analysis", "end"]:
        """Determine if verification should continue or move to next stage."""
        if state.verification_stage == "topic":
            if state.current_claim_index < len(state.topic_claims):
                return "verify_claims"
            else:
                return "update_topic"
        elif state.verification_stage == "analysis":
            if state.current_claim_index < len(state.analysis_claims):
                return "verify_claims"
            else:
                return "update_analysis"
        else:
            return "end"
    
    # =========================================================================
    # Stage 3: Topic Update
    # =========================================================================
    
    def _update_topic_node(
        self,
        state: GeneAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Update process name based on topic verification results."""
        print("=" * 50)
        print("Stage 3: Updating Process Name")
        print("=" * 50)
        
        # Use the original conversation messages
        messages = list(state.messages)
        
        # Add modification prompt
        modification_prompt = format_topic_modification_prompt(state.topic_verification_report)
        messages.append(HumanMessage(content=modification_prompt))
        
        model_kwargs = config.get("configurable", {}).get("model_kwargs", {})
        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            temperature=self.temperature,
            **model_kwargs
        )
        
        response = run_with_retry(llm.invoke, arg=messages)
        updated_summary = response.content if isinstance(response.content, str) else str(response.content)
        updated_process = self._extract_process_name(updated_summary)
        
        print(f"\nUpdated Process: {updated_process}")
        print(f"\nUpdated Summary:\n{updated_summary[:500]}..." if len(updated_summary) > 500 else f"\nUpdated Summary:\n{updated_summary}")
        
        return {
            "messages": messages + [response],
            "updated_process_name": updated_process,
            "updated_summary": updated_summary,
        }
    
    # =========================================================================
    # Stage 4: Analysis Verification
    # =========================================================================
    
    def _generate_analysis_claims_node(
        self,
        state: GeneAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Generate claims about gene analysis to verify."""
        updated_summary = state.updated_summary
        
        print("=" * 50)
        print("Stage 4: Generating Analysis Claims")
        print("=" * 50)
        
        prompt = format_analysis_claim_prompt(updated_summary)
        
        messages = [
            SystemMessage(content=TOPIC_VERIFICATION_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        model_kwargs = config.get("configurable", {}).get("model_kwargs", {})
        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            temperature=self.temperature,
            **model_kwargs
        )
        
        response = run_with_retry(llm.invoke, arg=messages)
        claims = self._parse_claims(response.content)
        
        # Limit claims for quick demos
        if self.max_claims_per_stage and len(claims) > self.max_claims_per_stage:
            print(f"\nLimiting claims from {len(claims)} to {self.max_claims_per_stage} (quick mode)")
            claims = claims[:self.max_claims_per_stage]
        
        print(f"\nAnalysis Claims to Verify: {claims}")
        
        return {
            "analysis_claims": claims,
            "verification_stage": "analysis",
            "current_claim_index": 0,
        }
    
    # =========================================================================
    # Stage 5: Final Summary
    # =========================================================================
    
    def _update_analysis_node(
        self,
        state: GeneAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Generate final summary based on analysis verification."""
        print("=" * 50)
        print("Stage 5: Generating Final Summary")
        print("=" * 50)
        
        # Use the messages from topic update stage
        messages = list(state.messages)
        
        # Add summarization prompt
        summarization_prompt = format_analysis_summarization_prompt(state.analysis_verification_report)
        messages.append(HumanMessage(content=summarization_prompt))
        
        model_kwargs = config.get("configurable", {}).get("model_kwargs", {})
        llm = self._get_model(
            api=self.api_type,
            model_name=self.model_name,
            api_key=self.api_key,
            endpoint=self.endpoint,
            temperature=self.temperature,
            **model_kwargs
        )
        
        response = run_with_retry(llm.invoke, arg=messages)
        final_summary = response.content if isinstance(response.content, str) else str(response.content)
        final_process = self._extract_process_name(final_summary)
        
        print(f"\nFinal Process: {final_process}")
        print(f"\nFinal Summary:\n{final_summary}")
        
        return {
            "messages": messages + [response],
            "final_process_name": final_process,
            "final_summary": final_summary,
            "verification_stage": "complete",
        }
    
    # =========================================================================
    # Graph Construction
    # =========================================================================
    
    def _create_agent_graph(self, debug: bool = False):
        """Create the agent workflow graph."""
        
        workflow = StateGraph(
            GeneAgentState,
            input=GeneAgentState,
            output=GeneAgentState
        )
        
        # Add nodes
        workflow.add_node("generate_initial_analysis", self._generate_initial_analysis_node)
        workflow.add_node("generate_topic_claims", self._generate_topic_claims_node)
        workflow.add_node("verify_claims", self._verify_claims_node)
        workflow.add_node("update_topic", self._update_topic_node)
        workflow.add_node("generate_analysis_claims", self._generate_analysis_claims_node)
        workflow.add_node("update_analysis", self._update_analysis_node)
        
        # Add edges
        workflow.add_edge("generate_initial_analysis", "generate_topic_claims")
        workflow.add_edge("generate_topic_claims", "verify_claims")
        
        workflow.add_conditional_edges(
            "verify_claims",
            self._should_continue_verification,
            {
                "verify_claims": "verify_claims",
                "update_topic": "update_topic",
                "update_analysis": "update_analysis",
                "end": END
            }
        )
        
        workflow.add_edge("update_topic", "generate_analysis_claims")
        workflow.add_edge("generate_analysis_claims", "verify_claims")
        workflow.add_edge("update_analysis", END)
        
        # Set entry point
        workflow.set_entry_point("generate_initial_analysis")
        
        # Compile
        return workflow.compile(debug=debug, name=self.name)
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    def generate(
        self,
        gene_set: Union[str, List[str]],
        verbose: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Run the GeneAgent on a gene set.
        
        Args:
            gene_set: Gene set as comma-separated string or list of gene names
            verbose: Whether to print progress
            
        Returns:
            List of state snapshots from the agent execution
        """
        assert self.agent_graph is not None, "Agent graph is not set"
        
        # Normalize gene set
        gene_set_normalized = self._normalize_gene_set(gene_set)
        gene_list = gene_set_normalized.split(",")
        
        if not gene_set_normalized:
            return [{"error": "gene_set is required"}]
        
        try:
            all_results = []
            
            inputs = {
                "messages": [],
                "gene_set": gene_set_normalized,
                "gene_list": gene_list,
            }
            
            # Stream the execution
            for stream_mode, chunk in self.agent_graph.stream(
                inputs,
                stream_mode=["values"],
                config={
                    "configurable": {
                        "model_kwargs": {
                            "max_completion_tokens": 8000,
                        }
                    },
                    "recursion_limit": 100  # Allow for many verification rounds
                }
            ):
                all_results.append(chunk)
            
            return all_results
            
        except Exception as e:
            print(f"Error during execution: {e}")
            raise e
    
    def go(
        self,
        gene_set: Union[str, List[str]],
        verbose: bool = True
    ) -> ExecutionResults:
        """
        Execute the GeneAgent and return structured results.
        
        Args:
            gene_set: Gene set as comma-separated string or list of gene names
                     Examples: "BRCA1,TP53,EGFR" or ["BRCA1", "TP53", "EGFR"]
            verbose: Whether to print progress
            
        Returns:
            ExecutionResults containing the final response and execution history
        """
        results = self.generate(gene_set, verbose=verbose)
        
        if not results or "error" in results[0]:
            return ExecutionResults(
                sandbox=None,
                message_history=[],
                code_execution_results=[],
                final_response=str(results[0].get("error", "Unknown error"))
            )
        
        final_state = results[-1]
        message_history = self._format_messages(final_state.get('messages', []))
        
        # Build final response
        final_summary = final_state.get('final_summary', '')
        
        if self.include_verification_reports:
            # Include verification reports for transparency
            response_parts = [
                "# Gene Set Analysis Results",
                f"\n## Gene Set\n{final_state.get('gene_set', '')}",
                f"\n## Final Analysis\n{final_summary}",
            ]
            
            if final_state.get('topic_verification_report'):
                response_parts.append(
                    f"\n## Topic Verification Report\n{final_state.get('topic_verification_report', '')}"
                )
            
            if final_state.get('analysis_verification_report'):
                response_parts.append(
                    f"\n## Analysis Verification Report\n{final_state.get('analysis_verification_report', '')}"
                )
            
            response_parts.append(
                f"\n## Statistics\n- Total claims verified: {final_state.get('total_claims_verified', 0)}"
            )
            
            final_response = "\n".join(response_parts)
        else:
            final_response = final_summary
        
        return ExecutionResults(
            sandbox=None,
            message_history=message_history,
            code_execution_results=[],
            final_response=final_response
        )
