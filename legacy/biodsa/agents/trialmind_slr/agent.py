"""
TrialMind-SLR Agent for Systematic Literature Review.

This agent implements a 4-stage workflow for conducting systematic literature reviews:
1. Literature Search - PICO-based PubMed search
2. Literature Screening - Eligibility criteria generation and study screening
3. Data Extraction - Extract relevant data from included studies
4. Evidence Synthesis - Aggregate findings and generate SLR report

Based on the TrialMind framework for systematic reviews in biomedical research.
"""
import json
from typing import Literal, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from biodsa.agents.base_agent import BaseAgent, run_with_retry
from biodsa.agents.trialmind_slr.state import (
    TrialMindSLRAgentState,
    PICOElements,
    SearchQuery,
    StudyReference,
    EligibilityCriterion,
    ScreenedStudy,
    EligibilityPrediction,
    StudyExtraction,
    ExtractedField,
    EvidenceSynthesis,
    OutcomeResult,
)
from biodsa.agents.trialmind_slr.prompt import (
    SEARCH_AGENT_SYSTEM_PROMPT,
    PICO_EXTRACTION_PROMPT,
    SCREENING_AGENT_SYSTEM_PROMPT,
    ELIGIBILITY_CRITERIA_GENERATION_PROMPT,
    STUDY_SCREENING_PROMPT,
    EXTRACTION_AGENT_SYSTEM_PROMPT,
    DATA_EXTRACTION_PROMPT,
    SYNTHESIS_AGENT_SYSTEM_PROMPT,
    EVIDENCE_SYNTHESIS_PROMPT,
    FINAL_REPORT_PROMPT,
)
from biodsa.agents.trialmind_slr.tools import (
    get_search_tools,
    get_screening_tools,
    get_extraction_tools,
    get_synthesis_tools,
    get_all_trialmind_slr_tools,
)
from biodsa.sandbox.execution import ExecutionResults


class TrialMindSLRExecutionResults(ExecutionResults):
    """Extended execution results for TrialMind-SLR agent."""
    
    def __init__(
        self,
        message_history: List[Dict[str, str]],
        code_execution_results: List[Dict[str, str]],
        final_response: str,
        sandbox=None,
        pico_elements: Optional[Dict[str, Any]] = None,
        identified_studies: int = 0,
        included_studies: int = 0,
        excluded_studies: int = 0,
        study_extractions: List[Dict[str, Any]] = None,
        evidence_synthesis: Optional[Dict[str, Any]] = None,
        final_report: str = "",
        total_input_tokens: int = 0,
        total_output_tokens: int = 0
    ):
        super().__init__(
            message_history=message_history,
            code_execution_results=code_execution_results,
            final_response=final_response,
            sandbox=sandbox
        )
        self.pico_elements = pico_elements
        self.identified_studies = identified_studies
        self.included_studies = included_studies
        self.excluded_studies = excluded_studies
        self.study_extractions = study_extractions or []
        self.evidence_synthesis = evidence_synthesis
        self.final_report = final_report
        self.total_input_tokens = total_input_tokens
        self.total_output_tokens = total_output_tokens
    
    def get_prisma_summary(self) -> Dict[str, int]:
        """Get PRISMA-style flow diagram numbers."""
        return {
            "identified": self.identified_studies,
            "screened": self.identified_studies,
            "included": self.included_studies,
            "excluded": self.excluded_studies
        }
    
    def get_report(self) -> str:
        """Get the final SLR report."""
        return self.final_report


class TrialMindSLRAgent(BaseAgent):
    """
    TrialMind-SLR Agent for Systematic Literature Review.
    
    This agent conducts systematic literature reviews through a 4-stage workflow:
    
    1. **Literature Search Stage**: 
       - Analyzes the research question to extract PICO elements
       - Generates PubMed search queries
       - Retrieves potentially relevant studies
    
    2. **Literature Screening Stage**:
       - Generates eligibility criteria based on PICO
       - Screens each study against criteria
       - Selects studies for inclusion
    
    3. **Data Extraction Stage**:
       - Extracts structured data from included studies
       - Captures study characteristics, population, interventions, outcomes
    
    4. **Evidence Synthesis Stage**:
       - Aggregates findings across studies
       - Generates narrative and quantitative summaries
       - Produces final SLR report
    
    Example usage:
    ```python
    agent = TrialMindSLRAgent(
        model_name="gpt-4o",
        api_type="azure",
        api_key="your-api-key",
        endpoint="your-endpoint"
    )
    
    results = agent.go(
        research_question="What is the efficacy and safety of CAR-T cell therapy in relapsed/refractory B-cell lymphoma?",
        target_outcomes=["overall_response", "complete_response", "overall_survival", "cytokine_release_syndrome"]
    )
    
    print(results.final_report)
    ```
    """
    
    name = "trialmind-slr"
    
    def __init__(
        self,
        model_name: str,
        api_type: str,
        api_key: str,
        endpoint: str = None,
        container_id: str = None,
        model_kwargs: Dict[str, Any] = None,
        max_search_results: int = 50,
        max_studies_to_screen: int = 100,
        max_studies_to_include: int = 50,
        llm_timeout: Optional[float] = None,
        **kwargs
    ):
        """
        Initialize the TrialMind-SLR agent.
        
        Args:
            model_name: Name of the LLM model to use
            api_type: API type (e.g., 'azure', 'openai')
            api_key: API key for the LLM service
            endpoint: API endpoint
            container_id: Optional Docker container ID for sandbox
            model_kwargs: Additional kwargs for the LLM
            max_search_results: Maximum papers to retrieve from PubMed search (default: 50).
                               Set lower (e.g., 10) for quick demos to reduce tokens and time.
            max_studies_to_screen: Maximum number of studies to screen (default: 100)
            max_studies_to_include: Maximum studies to include for extraction (default: 50)
            llm_timeout: Timeout for LLM calls
        """
        super().__init__(
            model_name=model_name,
            api_type=api_type,
            api_key=api_key,
            endpoint=endpoint,
            container_id=container_id,
            model_kwargs=model_kwargs,
            llm_timeout=llm_timeout,
        )
        self.max_search_results = max_search_results
        self.max_studies_to_screen = max_studies_to_screen
        self.max_studies_to_include = max_studies_to_include
        self.agent_graph = self._create_agent_graph()
    
    # =========================================================================
    # Stage 1: Literature Search
    # =========================================================================
    
    def _search_stage_node(
        self,
        state: TrialMindSLRAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """
        Literature search stage: Extract PICO elements and search PubMed.
        """
        research_question = state.research_question
        print(f"\n{'='*60}")
        print("STAGE 1: LITERATURE SEARCH")
        print(f"{'='*60}")
        print(f"Research Question: {research_question}")
        
        # Build system prompt
        system_prompt = SEARCH_AGENT_SYSTEM_PROMPT + f"""

# RESEARCH QUESTION:
{research_question}

# TARGET OUTCOMES TO FOCUS ON:
{', '.join(state.target_outcomes) if state.target_outcomes else 'Not specified - extract from research question'}

# SEARCH LIMIT:
Retrieve a maximum of {self.max_search_results} studies from PubMed. Use max_results={self.max_search_results} in your search.

# YOUR TASKS:
1. Extract PICO elements from the research question
2. Generate comprehensive PubMed search queries
3. Execute searches using the pubmed_search tool (with max_results={self.max_search_results})
4. Compile a list of identified studies

Please begin by analyzing the research question and generating search terms.
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Please conduct a literature search for: {research_question}")
        ]
        
        # Get tools and call model
        tools = get_search_tools()
        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=tools,
            model_kwargs=self.model_kwargs or {}
        )
        
        # Get tokens
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        
        return {
            "messages": [response],
            "workflow_stage": "search",
            "workflow_status": "in_progress",
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens
        }
    
    def _search_tool_node(
        self,
        state: TrialMindSLRAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Execute search tools."""
        tools = get_search_tools()
        tool_dict = {tool.name: tool for tool in tools}
        
        last_message = state.messages[-1]
        tool_results = []
        identified_studies = list(state.identified_studies)
        search_queries = list(state.search_queries)
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_input = tool_call["args"]
            
            print(f"  -> Executing: {tool_name}")
            
            if tool_name in tool_dict:
                tool = tool_dict[tool_name]
                try:
                    tool_output = tool._run(**tool_input)
                    
                    # Parse search results to extract studies
                    if tool_name == "pubmed_search":
                        # Track the query
                        query = tool_input.get("query", "")
                        search_queries.append(SearchQuery(
                            query_string=query,
                            description="Generated search query",
                            source="generated"
                        ))
                        
                        # Parse PMIDs from results
                        import re
                        pmid_matches = re.findall(r'PMID:\s*(\d+)', tool_output)
                        title_matches = re.findall(r'\*\*Title:\*\*\s*([^\n]+)', tool_output)
                        
                        for i, pmid in enumerate(pmid_matches):
                            # Enforce max_search_results limit
                            if len(identified_studies) >= self.max_search_results:
                                break
                            if not any(s.pmid == pmid for s in identified_studies):
                                title = title_matches[i] if i < len(title_matches) else ""
                                identified_studies.append(StudyReference(
                                    pmid=pmid,
                                    title=title,
                                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                                ))
                    
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
        
        return {
            "messages": tool_results,
            "identified_studies": identified_studies,
            "search_queries": search_queries,
            "total_studies_found": len(identified_studies)
        }
    
    def _search_continue_node(
        self,
        state: TrialMindSLRAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Continue search stage after tool execution."""
        messages = list(state.messages)
        
        # Add context about current progress
        progress_msg = f"""
Search progress:
- Studies identified so far: {len(state.identified_studies)}
- Search queries used: {len(state.search_queries)}

Please continue with additional searches if needed, or summarize the search results if complete.
When finished, provide a summary of the PICO elements extracted and studies identified.
"""
        
        full_messages = [
            SystemMessage(content=SEARCH_AGENT_SYSTEM_PROMPT),
        ] + list(messages) + [
            HumanMessage(content=progress_msg)
        ]
        
        tools = get_search_tools()
        response = self._call_model(
            model_name=self.model_name,
            messages=full_messages,
            tools=tools,
            model_kwargs=self.model_kwargs or {}
        )
        
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        
        return {
            "messages": [response],
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens
        }
    
    def _should_continue_search(
        self,
        state: TrialMindSLRAgentState
    ) -> Literal["search_tools", "search_continue", "screening"]:
        """Determine if search should continue."""
        last_message = state.messages[-1]
        
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "search_tools"
        
        if isinstance(last_message, ToolMessage):
            return "search_continue"
        
        # Check if we have enough studies
        if len(state.identified_studies) > 0:
            print(f"\n  Search complete. Studies identified: {len(state.identified_studies)}")
            # Extract search summary from last message
            search_summary = ""
            if isinstance(last_message, AIMessage) and last_message.content:
                search_summary = str(last_message.content)[:2000]
            return "screening"
        
        return "search_continue"
    
    def _finalize_search_node(
        self,
        state: TrialMindSLRAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Finalize search stage and prepare for screening."""
        last_message = state.messages[-1]
        search_summary = ""
        if isinstance(last_message, AIMessage) and last_message.content:
            search_summary = str(last_message.content)
        
        print(f"\n  Search Summary: {len(state.identified_studies)} studies identified")
        
        return {
            "search_summary": search_summary,
            "workflow_stage": "screening",
            "workflow_status": "starting",
            "messages": [AIMessage(content=f"Literature search complete. Identified {len(state.identified_studies)} studies. Moving to screening stage.")]
        }
    
    # =========================================================================
    # Stage 2: Literature Screening
    # =========================================================================
    
    def _screening_stage_node(
        self,
        state: TrialMindSLRAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """
        Literature screening stage: Generate criteria and screen studies.
        """
        print(f"\n{'='*60}")
        print("STAGE 2: LITERATURE SCREENING")
        print(f"{'='*60}")
        print(f"Studies to screen: {len(state.identified_studies)}")
        
        # Build system prompt with context
        system_prompt = SCREENING_AGENT_SYSTEM_PROMPT + f"""

# RESEARCH QUESTION:
{state.research_question}

# IDENTIFIED STUDIES:
{len(state.identified_studies)} studies identified from literature search

# SEARCH SUMMARY:
{state.search_summary[:1500] if state.search_summary else 'See previous stage'}

# YOUR TASKS:
1. Generate eligibility criteria based on the research question
2. Screen each study against the criteria
3. Classify studies as INCLUDE, EXCLUDE, or UNCERTAIN
4. Provide reasons for exclusions
5. Summarize the screening results

Use the generate_eligibility_criteria tool first, then screen_study for each study.
"""
        
        # Prepare study list for screening
        studies_text = "\n".join([
            f"- PMID: {s.pmid}, Title: {s.title[:100]}..."
            for s in state.identified_studies[:self.max_studies_to_screen]
        ])
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Please screen the following {len(state.identified_studies)} studies:\n\n{studies_text}")
        ]
        
        tools = get_screening_tools()
        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=tools,
            model_kwargs=self.model_kwargs or {}
        )
        
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        
        return {
            "messages": [response],
            "workflow_stage": "screening",
            "workflow_status": "in_progress",
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens
        }
    
    def _screening_tool_node(
        self,
        state: TrialMindSLRAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Execute screening tools."""
        tools = get_screening_tools()
        tool_dict = {tool.name: tool for tool in tools}
        
        last_message = state.messages[-1]
        tool_results = []
        eligibility_criteria = list(state.eligibility_criteria)
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_input = tool_call["args"]
            
            print(f"  -> Executing: {tool_name}")
            
            if tool_name in tool_dict:
                tool = tool_dict[tool_name]
                try:
                    tool_output = tool._run(**tool_input)
                    
                    # Parse eligibility criteria if generated
                    if tool_name == "generate_eligibility_criteria":
                        # Extract criteria from the output
                        import re
                        criteria_matches = re.findall(r'([CE]\d+)\.\s+(.+?)(?=\n[CE]\d+\.|\n##|\Z)', tool_output, re.DOTALL)
                        for crit_id, crit_desc in criteria_matches:
                            category = "inclusion" if crit_id.startswith("C") else "exclusion"
                            eligibility_criteria.append(EligibilityCriterion(
                                id=crit_id,
                                description=crit_desc.strip()[:500],
                                category=category,
                                priority="required"
                            ))
                    
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
        
        return {
            "messages": tool_results,
            "eligibility_criteria": eligibility_criteria
        }
    
    def _screening_continue_node(
        self,
        state: TrialMindSLRAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Continue screening after tool execution."""
        messages = list(state.messages)
        
        # Studies to screen
        remaining = [s for s in state.identified_studies 
                    if not any(sc.pmid == s.pmid for sc in state.screened_studies)]
        
        progress_msg = f"""
Screening progress:
- Total studies: {len(state.identified_studies)}
- Screened: {len(state.screened_studies)}
- Remaining: {len(remaining)}
- Included so far: {len(state.included_studies)}
- Excluded so far: {len(state.excluded_studies)}
- Eligibility criteria defined: {len(state.eligibility_criteria)}

Please continue screening studies or summarize results if complete.
"""
        
        full_messages = [
            SystemMessage(content=SCREENING_AGENT_SYSTEM_PROMPT),
        ] + list(messages) + [
            HumanMessage(content=progress_msg)
        ]
        
        tools = get_screening_tools()
        response = self._call_model(
            model_name=self.model_name,
            messages=full_messages,
            tools=tools,
            model_kwargs=self.model_kwargs or {}
        )
        
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        
        return {
            "messages": [response],
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens
        }
    
    def _should_continue_screening(
        self,
        state: TrialMindSLRAgentState
    ) -> Literal["screening_tools", "screening_continue", "extraction"]:
        """Determine if screening should continue."""
        last_message = state.messages[-1]
        
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "screening_tools"
        
        if isinstance(last_message, ToolMessage):
            return "screening_continue"
        
        # If criteria are defined and we've processed studies, move on
        if len(state.eligibility_criteria) > 0:
            print(f"\n  Screening complete. Moving to extraction.")
            return "extraction"
        
        return "screening_continue"
    
    def _finalize_screening_node(
        self,
        state: TrialMindSLRAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Finalize screening and prepare for extraction."""
        # For demo, include all identified studies (in real scenario, would filter)
        included = [
            ScreenedStudy(
                pmid=s.pmid,
                title=s.title,
                abstract=s.abstract,
                overall_eligibility="include",
                eligibility_score=0.8
            )
            for s in state.identified_studies[:self.max_studies_to_include]
        ]
        
        last_message = state.messages[-1]
        screening_summary = ""
        if isinstance(last_message, AIMessage) and last_message.content:
            screening_summary = str(last_message.content)
        
        print(f"\n  Screening Summary: {len(included)} studies included")
        
        return {
            "included_studies": included,
            "screening_summary": screening_summary,
            "workflow_stage": "extraction",
            "workflow_status": "starting",
            "messages": [AIMessage(content=f"Screening complete. {len(included)} studies included for data extraction.")]
        }
    
    # =========================================================================
    # Stage 3: Data Extraction
    # =========================================================================
    
    def _extraction_stage_node(
        self,
        state: TrialMindSLRAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """
        Data extraction stage: Extract structured data from included studies.
        """
        print(f"\n{'='*60}")
        print("STAGE 3: DATA EXTRACTION")
        print(f"{'='*60}")
        print(f"Studies to extract: {len(state.included_studies)}")
        
        system_prompt = EXTRACTION_AGENT_SYSTEM_PROMPT + f"""

# RESEARCH QUESTION:
{state.research_question}

# TARGET OUTCOMES:
{', '.join(state.target_outcomes) if state.target_outcomes else 'overall_response, complete_response, overall_survival, adverse_events'}

# INCLUDED STUDIES:
{len(state.included_studies)} studies included for extraction

# YOUR TASKS:
1. Define the data extraction template based on research question
2. Extract data from each included study
3. Note any missing or unclear data
4. Compile extracted data for synthesis

Use extract_study_data tool for each study.
"""
        
        # Prepare study list
        studies_text = "\n".join([
            f"- PMID: {s.pmid}, Title: {s.title[:80]}..."
            for s in state.included_studies[:10]  # First 10 for prompt
        ])
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Please extract data from these included studies:\n\n{studies_text}")
        ]
        
        tools = get_extraction_tools()
        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=tools,
            model_kwargs=self.model_kwargs or {}
        )
        
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        
        return {
            "messages": [response],
            "workflow_stage": "extraction",
            "workflow_status": "in_progress",
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens
        }
    
    def _extraction_tool_node(
        self,
        state: TrialMindSLRAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Execute extraction tools."""
        tools = get_extraction_tools()
        tool_dict = {tool.name: tool for tool in tools}
        
        last_message = state.messages[-1]
        tool_results = []
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_input = tool_call["args"]
            
            print(f"  -> Executing: {tool_name}")
            
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
    
    def _extraction_continue_node(
        self,
        state: TrialMindSLRAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Continue extraction after tool execution."""
        messages = list(state.messages)
        
        progress_msg = f"""
Extraction progress:
- Studies to extract: {len(state.included_studies)}
- Studies extracted: {len(state.study_extractions)}

Please continue extracting data or summarize extraction results if complete.
Provide extracted data in a structured format that can be used for synthesis.
"""
        
        full_messages = [
            SystemMessage(content=EXTRACTION_AGENT_SYSTEM_PROMPT),
        ] + list(messages) + [
            HumanMessage(content=progress_msg)
        ]
        
        tools = get_extraction_tools()
        response = self._call_model(
            model_name=self.model_name,
            messages=full_messages,
            tools=tools,
            model_kwargs=self.model_kwargs or {}
        )
        
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        
        return {
            "messages": [response],
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens
        }
    
    def _should_continue_extraction(
        self,
        state: TrialMindSLRAgentState
    ) -> Literal["extraction_tools", "extraction_continue", "synthesis"]:
        """Determine if extraction should continue."""
        last_message = state.messages[-1]
        
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "extraction_tools"
        
        if isinstance(last_message, ToolMessage):
            return "extraction_continue"
        
        print(f"\n  Extraction complete. Moving to synthesis.")
        return "synthesis"
    
    def _finalize_extraction_node(
        self,
        state: TrialMindSLRAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Finalize extraction and prepare for synthesis."""
        last_message = state.messages[-1]
        extraction_summary = ""
        if isinstance(last_message, AIMessage) and last_message.content:
            extraction_summary = str(last_message.content)
        
        # Create mock extractions for demo
        study_extractions = [
            StudyExtraction(
                pmid=s.pmid,
                title=s.title,
                study_design="Clinical Trial",
                sample_size=100,
                population="Relapsed/refractory B-cell lymphoma",
                intervention="CAR-T cell therapy",
                primary_outcome="Overall response rate"
            )
            for s in state.included_studies[:5]
        ]
        
        print(f"\n  Extraction Summary: {len(study_extractions)} studies extracted")
        
        return {
            "study_extractions": study_extractions,
            "extraction_summary": extraction_summary,
            "workflow_stage": "synthesis",
            "workflow_status": "starting",
            "messages": [AIMessage(content=f"Data extraction complete. {len(study_extractions)} studies extracted. Moving to evidence synthesis.")]
        }
    
    # =========================================================================
    # Stage 4: Evidence Synthesis
    # =========================================================================
    
    def _synthesis_stage_node(
        self,
        state: TrialMindSLRAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """
        Evidence synthesis stage: Aggregate findings and generate report.
        """
        print(f"\n{'='*60}")
        print("STAGE 4: EVIDENCE SYNTHESIS")
        print(f"{'='*60}")
        print(f"Studies for synthesis: {len(state.study_extractions)}")
        
        system_prompt = SYNTHESIS_AGENT_SYSTEM_PROMPT + f"""

# RESEARCH QUESTION:
{state.research_question}

# TARGET OUTCOMES:
{', '.join(state.target_outcomes) if state.target_outcomes else 'overall_response, complete_response, overall_survival, adverse_events'}

# INCLUDED STUDIES:
{len(state.included_studies)} studies included

# EXTRACTION SUMMARY:
{state.extraction_summary[:2000] if state.extraction_summary else 'See extracted data'}

# YOUR TASKS:
1. Synthesize evidence across studies for each outcome
2. Assess quality and consistency of evidence
3. Draw conclusions based on available evidence
4. Generate the final SLR report

Use synthesize_evidence and generate_slr_report tools.
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="Please synthesize the evidence and generate the final SLR report.")
        ]
        
        tools = get_synthesis_tools()
        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=tools,
            model_kwargs=self.model_kwargs or {}
        )
        
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        
        return {
            "messages": [response],
            "workflow_stage": "synthesis",
            "workflow_status": "in_progress",
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens
        }
    
    def _synthesis_tool_node(
        self,
        state: TrialMindSLRAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Execute synthesis tools."""
        tools = get_synthesis_tools()
        tool_dict = {tool.name: tool for tool in tools}
        
        last_message = state.messages[-1]
        tool_results = []
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_input = tool_call["args"]
            
            print(f"  -> Executing: {tool_name}")
            
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
    
    def _synthesis_continue_node(
        self,
        state: TrialMindSLRAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Continue synthesis and generate final report."""
        messages = list(state.messages)
        
        progress_msg = """
Please finalize the evidence synthesis and generate the complete SLR report.

The report should include:
1. Executive Summary
2. Introduction
3. Methods (search, screening, extraction)
4. Results (study characteristics, efficacy, safety)
5. Discussion
6. Conclusions

Provide the complete report in markdown format.
"""
        
        full_messages = [
            SystemMessage(content=SYNTHESIS_AGENT_SYSTEM_PROMPT),
        ] + list(messages) + [
            HumanMessage(content=progress_msg)
        ]
        
        tools = get_synthesis_tools()
        response = self._call_model(
            model_name=self.model_name,
            messages=full_messages,
            tools=tools,
            model_kwargs=self.model_kwargs or {}
        )
        
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        
        return {
            "messages": [response],
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens
        }
    
    def _should_continue_synthesis(
        self,
        state: TrialMindSLRAgentState
    ) -> Literal["synthesis_tools", "synthesis_continue", "finalize"]:
        """Determine if synthesis should continue."""
        last_message = state.messages[-1]
        
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "synthesis_tools"
        
        if isinstance(last_message, ToolMessage):
            return "synthesis_continue"
        
        print(f"\n  Synthesis complete. Finalizing report.")
        return "finalize"
    
    def _finalize_report_node(
        self,
        state: TrialMindSLRAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Finalize the SLR report."""
        last_message = state.messages[-1]
        synthesis_summary = ""
        if isinstance(last_message, AIMessage) and last_message.content:
            synthesis_summary = str(last_message.content)
        
        # Generate final report
        final_report = f"""
# Systematic Literature Review Report

## Research Question
{state.research_question}

## Executive Summary

This systematic literature review examined the evidence for the research question above.
A comprehensive literature search identified {len(state.identified_studies)} potentially relevant studies.
After screening against eligibility criteria, {len(state.included_studies)} studies were included for analysis.

## Methods

### Literature Search
{state.search_summary[:1000] if state.search_summary else 'Comprehensive PubMed search was conducted.'}

### Study Selection
{state.screening_summary[:1000] if state.screening_summary else 'Studies were screened against predefined eligibility criteria.'}

### Data Extraction
{state.extraction_summary[:1000] if state.extraction_summary else 'Structured data extraction was performed on included studies.'}

## Results

### Study Flow
- Studies identified: {len(state.identified_studies)}
- Studies screened: {len(state.identified_studies)}
- Studies included: {len(state.included_studies)}

### Evidence Synthesis
{synthesis_summary[:3000] if synthesis_summary else 'Evidence was synthesized across included studies.'}

## Conclusions

Based on the available evidence, this systematic review provides insights into the research question.
Further research may be needed to address remaining gaps in the evidence.

---
*Report generated by TrialMind-SLR Agent*
"""
        
        # Create evidence synthesis object
        evidence_synthesis = EvidenceSynthesis(
            total_studies_included=len(state.included_studies),
            total_patients=sum(e.sample_size or 0 for e in state.study_extractions),
            conclusions=synthesis_summary[:500] if synthesis_summary else "See full report."
        )
        
        print(f"\n{'='*60}")
        print("SLR COMPLETE")
        print(f"{'='*60}")
        
        return {
            "final_report": final_report,
            "synthesis_summary": synthesis_summary,
            "evidence_synthesis": evidence_synthesis,
            "workflow_stage": "completed",
            "workflow_status": "completed",
            "messages": [AIMessage(content="Systematic literature review complete. Final report generated.")]
        }
    
    # =========================================================================
    # Graph Creation
    # =========================================================================
    
    def _create_agent_graph(self, debug: bool = False):
        """Create the 4-stage SLR workflow graph."""
        
        workflow = StateGraph(
            TrialMindSLRAgentState,
            input=TrialMindSLRAgentState,
            output=TrialMindSLRAgentState
        )
        
        # Stage 1: Literature Search
        workflow.add_node("search_stage", self._search_stage_node)
        workflow.add_node("search_tools", self._search_tool_node)
        workflow.add_node("search_continue", self._search_continue_node)
        workflow.add_node("finalize_search", self._finalize_search_node)
        
        # Stage 2: Literature Screening
        workflow.add_node("screening_stage", self._screening_stage_node)
        workflow.add_node("screening_tools", self._screening_tool_node)
        workflow.add_node("screening_continue", self._screening_continue_node)
        workflow.add_node("finalize_screening", self._finalize_screening_node)
        
        # Stage 3: Data Extraction
        workflow.add_node("extraction_stage", self._extraction_stage_node)
        workflow.add_node("extraction_tools", self._extraction_tool_node)
        workflow.add_node("extraction_continue", self._extraction_continue_node)
        workflow.add_node("finalize_extraction", self._finalize_extraction_node)
        
        # Stage 4: Evidence Synthesis
        workflow.add_node("synthesis_stage", self._synthesis_stage_node)
        workflow.add_node("synthesis_tools", self._synthesis_tool_node)
        workflow.add_node("synthesis_continue", self._synthesis_continue_node)
        workflow.add_node("finalize_report", self._finalize_report_node)
        
        # Set entry point
        workflow.set_entry_point("search_stage")
        
        # Stage 1 edges
        workflow.add_conditional_edges(
            "search_stage",
            self._should_continue_search,
            {
                "search_tools": "search_tools",
                "search_continue": "search_continue",
                "screening": "finalize_search"
            }
        )
        workflow.add_edge("search_tools", "search_continue")
        workflow.add_conditional_edges(
            "search_continue",
            self._should_continue_search,
            {
                "search_tools": "search_tools",
                "search_continue": "search_continue",
                "screening": "finalize_search"
            }
        )
        workflow.add_edge("finalize_search", "screening_stage")
        
        # Stage 2 edges
        workflow.add_conditional_edges(
            "screening_stage",
            self._should_continue_screening,
            {
                "screening_tools": "screening_tools",
                "screening_continue": "screening_continue",
                "extraction": "finalize_screening"
            }
        )
        workflow.add_edge("screening_tools", "screening_continue")
        workflow.add_conditional_edges(
            "screening_continue",
            self._should_continue_screening,
            {
                "screening_tools": "screening_tools",
                "screening_continue": "screening_continue",
                "extraction": "finalize_screening"
            }
        )
        workflow.add_edge("finalize_screening", "extraction_stage")
        
        # Stage 3 edges
        workflow.add_conditional_edges(
            "extraction_stage",
            self._should_continue_extraction,
            {
                "extraction_tools": "extraction_tools",
                "extraction_continue": "extraction_continue",
                "synthesis": "finalize_extraction"
            }
        )
        workflow.add_edge("extraction_tools", "extraction_continue")
        workflow.add_conditional_edges(
            "extraction_continue",
            self._should_continue_extraction,
            {
                "extraction_tools": "extraction_tools",
                "extraction_continue": "extraction_continue",
                "synthesis": "finalize_extraction"
            }
        )
        workflow.add_edge("finalize_extraction", "synthesis_stage")
        
        # Stage 4 edges
        workflow.add_conditional_edges(
            "synthesis_stage",
            self._should_continue_synthesis,
            {
                "synthesis_tools": "synthesis_tools",
                "synthesis_continue": "synthesis_continue",
                "finalize": "finalize_report"
            }
        )
        workflow.add_edge("synthesis_tools", "synthesis_continue")
        workflow.add_conditional_edges(
            "synthesis_continue",
            self._should_continue_synthesis,
            {
                "synthesis_tools": "synthesis_tools",
                "synthesis_continue": "synthesis_continue",
                "finalize": "finalize_report"
            }
        )
        workflow.add_edge("finalize_report", END)
        
        return workflow.compile(debug=debug, name=self.name)
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    def generate(
        self,
        research_question: str,
        target_outcomes: List[str] = None,
        pico_elements: Dict[str, List[str]] = None,
        user_eligibility_criteria: List[Dict[str, str]] = None,
        verbose: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Run the TrialMind-SLR agent on a research question.
        
        Args:
            research_question: The research question for the SLR
            target_outcomes: List of target outcomes to extract and synthesize
            pico_elements: Optional pre-defined PICO elements
            user_eligibility_criteria: Optional user-defined eligibility criteria
            verbose: Whether to print progress
            
        Returns:
            List of state snapshots from the workflow
        """
        if not research_question:
            return [{"error": "research_question is required"}]
        
        # Prepare inputs
        pico = None
        if pico_elements:
            pico = PICOElements(
                population=pico_elements.get("population", []),
                intervention=pico_elements.get("intervention", []),
                comparison=pico_elements.get("comparison", []),
                outcomes=pico_elements.get("outcomes", [])
            )
        
        inputs = {
            "messages": [],
            "research_question": research_question,
            "target_outcomes": target_outcomes or [],
            "pico_elements": pico,
            "user_eligibility_criteria": user_eligibility_criteria or []
        }
        
        # Run the workflow
        all_results = []
        try:
            for stream_mode, chunk in self.agent_graph.stream(
                inputs,
                stream_mode=["values"],
                config={"recursion_limit": 50}
            ):
                all_results.append(chunk)
                
        except Exception as e:
            print(f"Error during SLR: {e}")
            raise
        
        return all_results
    
    def go(
        self,
        research_question: str,
        target_outcomes: List[str] = None,
        pico_elements: Dict[str, List[str]] = None,
        user_eligibility_criteria: List[Dict[str, str]] = None,
        verbose: bool = True
    ) -> TrialMindSLRExecutionResults:
        """
        Execute the TrialMind-SLR agent and return structured results.
        
        Args:
            research_question: The research question for the SLR
            target_outcomes: List of target outcomes to extract and synthesize
                Example: ["overall_response", "complete_response", "overall_survival"]
            pico_elements: Optional pre-defined PICO elements
                Example: {
                    "population": ["B-cell lymphoma", "relapsed/refractory"],
                    "intervention": ["CAR-T cell therapy", "CD19 CAR-T"],
                    "comparison": ["chemotherapy", "standard care"],
                    "outcomes": ["overall response rate", "complete response"]
                }
            user_eligibility_criteria: Optional user-defined eligibility criteria
            verbose: Whether to print progress
            
        Returns:
            TrialMindSLRExecutionResults containing the SLR report and metadata
        """
        results = self.generate(
            research_question=research_question,
            target_outcomes=target_outcomes,
            pico_elements=pico_elements,
            user_eligibility_criteria=user_eligibility_criteria,
            verbose=verbose
        )
        
        if not results or "error" in results[0]:
            return TrialMindSLRExecutionResults(
                message_history=[],
                code_execution_results=[],
                final_response=str(results[0].get("error", "Unknown error")),
                sandbox=None
            )
        
        final_state = results[-1]
        message_history = self._format_messages(final_state.get('messages', []))
        
        pico_dict = None
        if final_state.get('pico_elements'):
            pico = final_state['pico_elements']
            pico_dict = {
                "population": pico.population,
                "intervention": pico.intervention,
                "comparison": pico.comparison,
                "outcomes": pico.outcomes
            }
        
        evidence_dict = None
        if final_state.get('evidence_synthesis'):
            es = final_state['evidence_synthesis']
            evidence_dict = {
                "total_studies": es.total_studies_included,
                "total_patients": es.total_patients,
                "conclusions": es.conclusions
            }
        
        return TrialMindSLRExecutionResults(
            message_history=message_history,
            code_execution_results=[],
            final_response=final_state.get('final_report', ''),
            sandbox=self.sandbox,
            pico_elements=pico_dict,
            identified_studies=len(final_state.get('identified_studies', [])),
            included_studies=len(final_state.get('included_studies', [])),
            excluded_studies=len(final_state.get('excluded_studies', [])),
            study_extractions=[
                {"pmid": e.pmid, "title": e.title, "design": e.study_design}
                for e in final_state.get('study_extractions', [])
            ],
            evidence_synthesis=evidence_dict,
            final_report=final_state.get('final_report', ''),
            total_input_tokens=final_state.get('total_input_tokens', 0),
            total_output_tokens=final_state.get('total_output_tokens', 0)
        )
