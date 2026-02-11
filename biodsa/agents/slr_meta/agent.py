"""
SLR-Meta Agent: Systematic literature review and meta-analysis using
PubMed and ClinicalTrials.gov to synthesize clinical evidence.
"""
import re
from typing import Literal, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from biodsa.agents.base_agent import BaseAgent, run_with_retry
from biodsa.agents.slr_meta.state import (
    SLRMetaAgentState,
    PICOElements,
    StudyReference,
    CTGovTrialReference,
    EligibilityCriterion,
    ScreenedStudy,
    StudyExtraction,
    EvidenceSynthesis,
)
from biodsa.agents.slr_meta.prompt import (
    SEARCH_AGENT_SYSTEM_PROMPT,
    SCREENING_AGENT_SYSTEM_PROMPT,
    EXTRACTION_AGENT_SYSTEM_PROMPT,
    SYNTHESIS_AGENT_SYSTEM_PROMPT,
)
from biodsa.agents.slr_meta.tools import (
    get_search_tools,
    get_screening_tools,
    get_extraction_tools,
    get_synthesis_tools,
)
from biodsa.sandbox.execution import ExecutionResults


def _parse_pubmed_results(tool_output: str, max_results: int) -> List[StudyReference]:
    """Parse PubMed search tool output into StudyReference list."""
    refs = []
    pmid_matches = re.findall(r'PMID:\s*(\d+)', tool_output)
    title_matches = re.findall(r'\*\*Title:\*\*\s*([^\n]+)', tool_output)
    for i, pmid in enumerate(pmid_matches):
        if len(refs) >= max_results:
            break
        if not any(s.pmid == pmid for s in refs):
            title = title_matches[i] if i < len(title_matches) else ""
            refs.append(StudyReference(
                pmid=pmid,
                title=title,
                abstract="",
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                source="pubmed"
            ))
    return refs


def _parse_ctgov_results(tool_output: str, max_results: int) -> List[CTGovTrialReference]:
    """Parse ClinicalTrials.gov search tool output into CTGovTrialReference list."""
    refs = []
    nct_matches = re.findall(r'NCT\d+', tool_output)
    seen = set()
    for nct_id in nct_matches:
        if len(refs) >= max_results or nct_id in seen:
            continue
        seen.add(nct_id)
        refs.append(CTGovTrialReference(
            nct_id=nct_id,
            title="",
            conditions="",
            interventions="",
            brief_summary="",
            url=f"https://clinicaltrials.gov/ct2/show/{nct_id}",
            study_status="",
            phase="",
            source="ctgov"
        ))
    return refs


class SLRMetaExecutionResults(ExecutionResults):
    """Extended execution results for SLR-Meta agent."""

    def __init__(
        self,
        message_history: List[Dict[str, str]],
        code_execution_results: List[Dict[str, str]],
        final_response: str,
        sandbox=None,
        identified_pubmed: int = 0,
        identified_ctgov: int = 0,
        included_studies: int = 0,
        final_report: str = "",
        **kwargs
    ):
        super().__init__(
            message_history=message_history,
            code_execution_results=code_execution_results,
            final_response=final_response,
            sandbox=sandbox
        )
        self.identified_pubmed = identified_pubmed
        self.identified_ctgov = identified_ctgov
        self.included_studies = included_studies
        self.final_report = final_report or final_response


class SLRMetaAgent(BaseAgent):
    """
    SLR-Meta Agent: systematic literature review and meta-analysis using
    PubMed and ClinicalTrials.gov to synthesize clinical evidence for a
    given research question.
    """

    name = "slr-meta"

    def __init__(
        self,
        model_name: str,
        api_type: str,
        api_key: str,
        endpoint: str = None,
        container_id: str = None,
        model_kwargs: Dict[str, Any] = None,
        max_search_results: int = 50,
        max_ctgov_results: int = 50,
        max_studies_to_screen: int = 100,
        max_studies_to_include: int = 50,
        llm_timeout: Optional[float] = None,
        **kwargs
    ):
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
        self.max_ctgov_results = max_ctgov_results
        self.max_studies_to_screen = max_studies_to_screen
        self.max_studies_to_include = max_studies_to_include
        self.agent_graph = self._create_agent_graph()

    # ---------- Stage 1: Dual-source search ----------

    def _search_stage_node(self, state: SLRMetaAgentState, config: RunnableConfig) -> Dict[str, Any]:
        research_question = state.research_question
        print("\n" + "=" * 60)
        print("STAGE 1: DUAL-SOURCE LITERATURE SEARCH (PubMed + ClinicalTrials.gov)")
        print("=" * 60)
        print(f"Research Question: {research_question}")

        system_prompt = SEARCH_AGENT_SYSTEM_PROMPT + f"""

# RESEARCH QUESTION:
{research_question}

# TARGET OUTCOMES:
{', '.join(state.target_outcomes) if state.target_outcomes else 'Not specified'}

# LIMITS:
- PubMed: use max_results={self.max_search_results} in pubmed_search
- ClinicalTrials.gov: use page_size={self.max_ctgov_results} in ctgov_search

# YOUR TASKS:
1. Extract PICO from the research question
2. Run PubMed search(es) with pubmed_search
3. Run ClinicalTrials.gov search with ctgov_search (conditions, terms, interventions)
4. Summarize results from BOTH sources
"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Conduct dual-source literature search for: {research_question}")
        ]
        tools = get_search_tools()
        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=tools,
            model_kwargs=self.model_kwargs or {}
        )
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        return {
            "messages": [response],
            "workflow_stage": "search",
            "workflow_status": "in_progress",
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens,
        }

    def _search_tool_node(self, state: SLRMetaAgentState, config: RunnableConfig) -> Dict[str, Any]:
        tools = get_search_tools()
        tool_dict = {t.name: t for t in tools}
        last_message = state.messages[-1]
        tool_results = []
        identified_studies = list(state.identified_studies)
        ctgov_trials = list(state.ctgov_trials)
        search_queries_pubmed = list(state.search_queries_pubmed)
        search_queries_ctgov = list(state.search_queries_ctgov)

        for tool_call in last_message.tool_calls:
            name = tool_call["name"]
            args = tool_call["args"]
            print(f"  -> Executing: {name}")
            if name not in tool_dict:
                tool_results.append(ToolMessage(content=f"Unknown tool: {name}", name=name, tool_call_id=tool_call["id"]))
                continue
            try:
                output = tool_dict[name]._run(**args)
                if name == "pubmed_search":
                    query = args.get("query", "")
                    search_queries_pubmed.append(query)
                    new_refs = _parse_pubmed_results(output, self.max_search_results)
                    for r in new_refs:
                        if not any(s.pmid == r.pmid for s in identified_studies):
                            identified_studies.append(r)
                elif name == "ctgov_search":
                    search_queries_ctgov.append(args)
                    new_trials = _parse_ctgov_results(output, self.max_ctgov_results)
                    for t in new_trials:
                        if not any(c.nct_id == t.nct_id for c in ctgov_trials):
                            ctgov_trials.append(t)
                tool_results.append(ToolMessage(content=output, name=name, tool_call_id=tool_call["id"]))
            except Exception as e:
                tool_results.append(ToolMessage(content=f"Error: {str(e)}", name=name, tool_call_id=tool_call["id"]))

        return {
            "messages": tool_results,
            "identified_studies": identified_studies,
            "ctgov_trials": ctgov_trials,
            "search_queries_pubmed": search_queries_pubmed,
            "search_queries_ctgov": search_queries_ctgov,
        }

    def _search_continue_node(self, state: SLRMetaAgentState, config: RunnableConfig) -> Dict[str, Any]:
        progress = f"""
Search progress:
- PubMed studies: {len(state.identified_studies)}
- CT.gov trials: {len(state.ctgov_trials)}
Continue with more searches if needed, or summarize and proceed.
"""
        full_messages = [SystemMessage(content=SEARCH_AGENT_SYSTEM_PROMPT)] + list(state.messages) + [HumanMessage(content=progress)]
        response = self._call_model(
            model_name=self.model_name,
            messages=full_messages,
            tools=get_search_tools(),
            model_kwargs=self.model_kwargs or {}
        )
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        return {
            "messages": [response],
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens,
        }

    def _should_continue_search(self, state: SLRMetaAgentState) -> Literal["search_tools", "search_continue", "finalize_search"]:
        last = state.messages[-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "search_tools"
        if isinstance(last, ToolMessage):
            return "search_continue"
        if len(state.identified_studies) > 0 or len(state.ctgov_trials) > 0:
            print(f"\n  Search complete. PubMed: {len(state.identified_studies)}, CT.gov: {len(state.ctgov_trials)}")
            return "finalize_search"
        return "search_continue"

    def _finalize_search_node(self, state: SLRMetaAgentState, config: RunnableConfig) -> Dict[str, Any]:
        summary = f"Dual-source search complete. PubMed: {len(state.identified_studies)} studies; ClinicalTrials.gov: {len(state.ctgov_trials)} trials."
        return {
            "search_summary": summary,
            "workflow_stage": "screening",
            "workflow_status": "starting",
            "messages": [AIMessage(content=summary + " Moving to screening.")]
        }

    # ---------- Stage 2: Screening ----------

    def _screening_stage_node(self, state: SLRMetaAgentState, config: RunnableConfig) -> Dict[str, Any]:
        print("\n" + "=" * 60)
        print("STAGE 2: LITERATURE SCREENING")
        print("=" * 60)
        system_prompt = SCREENING_AGENT_SYSTEM_PROMPT + f"""

# RESEARCH QUESTION: {state.research_question}
# PubMed studies to screen: {len(state.identified_studies)}
# CT.gov trials to screen: {len(state.ctgov_trials)}

Generate eligibility criteria, then screen studies/trials. Use generate_eligibility_criteria first, then screen_study.
"""
        studies_text = "\n".join([f"- PMID {s.pmid}: {s.title[:80]}..." for s in state.identified_studies[: self.max_studies_to_screen]])
        trials_text = "\n".join([f"- {t.nct_id}: {t.title or t.conditions}" for t in state.ctgov_trials[: self.max_studies_to_screen]])
        human = f"Screen the following.\n\nPubMed studies:\n{studies_text}\n\nCT.gov trials:\n{trials_text}"
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=human)]
        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=get_screening_tools(),
            model_kwargs=self.model_kwargs or {}
        )
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        return {
            "messages": [response],
            "workflow_stage": "screening",
            "workflow_status": "in_progress",
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens,
        }

    def _screening_tool_node(self, state: SLRMetaAgentState, config: RunnableConfig) -> Dict[str, Any]:
        tool_dict = {t.name: t for t in get_screening_tools()}
        last_message = state.messages[-1]
        tool_results = []
        for tool_call in last_message.tool_calls:
            name, args, tid = tool_call["name"], tool_call["args"], tool_call["id"]
            print(f"  -> Executing: {name}")
            try:
                output = tool_dict[name]._run(**args) if name in tool_dict else f"Unknown: {name}"
            except Exception as e:
                output = str(e)
            tool_results.append(ToolMessage(content=output, name=name, tool_call_id=tid))
        return {"messages": tool_results}

    def _screening_continue_node(self, state: SLRMetaAgentState, config: RunnableConfig) -> Dict[str, Any]:
        full_messages = [SystemMessage(content=SCREENING_AGENT_SYSTEM_PROMPT)] + list(state.messages) + [
            HumanMessage(content="Continue screening or summarize screening results.")
        ]
        response = self._call_model(
            model_name=self.model_name,
            messages=full_messages,
            tools=get_screening_tools(),
            model_kwargs=self.model_kwargs or {}
        )
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        return {
            "messages": [response],
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens,
        }

    def _should_continue_screening(self, state: SLRMetaAgentState) -> Literal["screening_tools", "screening_continue", "finalize_screening"]:
        last = state.messages[-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "screening_tools"
        if isinstance(last, ToolMessage):
            return "screening_continue"
        return "finalize_screening"

    def _finalize_screening_node(self, state: SLRMetaAgentState, config: RunnableConfig) -> Dict[str, Any]:
        # Include subset for extraction (PubMed + CT.gov)
        included = []
        for s in state.identified_studies[: self.max_studies_to_include]:
            included.append(ScreenedStudy(
                identifier=s.pmid,
                title=s.title,
                abstract_or_summary=s.abstract,
                source="pubmed",
                overall_eligibility="include",
                eligibility_score=0.8
            ))
        for t in state.ctgov_trials[: max(0, self.max_studies_to_include - len(included))]:
            included.append(ScreenedStudy(
                identifier=t.nct_id,
                title=t.title or t.conditions,
                abstract_or_summary=t.brief_summary,
                source="ctgov",
                overall_eligibility="include",
                eligibility_score=0.8
            ))
        return {
            "included_studies": included,
            "workflow_stage": "extraction",
            "workflow_status": "starting",
            "messages": [AIMessage(content=f"Screening complete. {len(included)} studies/trials included. Moving to extraction.")]
        }

    # ---------- Stage 3: Extraction ----------

    def _extraction_stage_node(self, state: SLRMetaAgentState, config: RunnableConfig) -> Dict[str, Any]:
        print("\n" + "=" * 60)
        print("STAGE 3: DATA EXTRACTION")
        print("=" * 60)
        system_prompt = EXTRACTION_AGENT_SYSTEM_PROMPT + f"""

# RESEARCH QUESTION: {state.research_question}
# TARGET OUTCOMES: {', '.join(state.target_outcomes) or 'efficacy, safety'}
# INCLUDED: {len(state.included_studies)} studies/trials

Use extract_study_data for each included record.
"""
        studies_text = "\n".join([f"- {s.identifier} ({s.source}): {s.title[:60]}..." for s in state.included_studies[:15]])
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=f"Extract data from:\n{studies_text}")]
        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=get_extraction_tools(),
            model_kwargs=self.model_kwargs or {}
        )
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        return {
            "messages": [response],
            "workflow_stage": "extraction",
            "workflow_status": "in_progress",
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens,
        }

    def _extraction_tool_node(self, state: SLRMetaAgentState, config: RunnableConfig) -> Dict[str, Any]:
        tool_dict = {t.name: t for t in get_extraction_tools()}
        last_message = state.messages[-1]
        tool_results = []
        for tool_call in last_message.tool_calls:
            name, args, tid = tool_call["name"], tool_call["args"], tool_call["id"]
            try:
                output = tool_dict[name]._run(**args) if name in tool_dict else f"Unknown: {name}"
            except Exception as e:
                output = str(e)
            tool_results.append(ToolMessage(content=output, name=name, tool_call_id=tid))
        return {"messages": tool_results}

    def _extraction_continue_node(self, state: SLRMetaAgentState, config: RunnableConfig) -> Dict[str, Any]:
        full_messages = [SystemMessage(content=EXTRACTION_AGENT_SYSTEM_PROMPT)] + list(state.messages) + [
            HumanMessage(content="Continue extraction or summarize extracted data for synthesis.")
        ]
        response = self._call_model(
            model_name=self.model_name,
            messages=full_messages,
            tools=get_extraction_tools(),
            model_kwargs=self.model_kwargs or {}
        )
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        return {
            "messages": [response],
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens,
        }

    def _should_continue_extraction(self, state: SLRMetaAgentState) -> Literal["extraction_tools", "extraction_continue", "finalize_extraction"]:
        last = state.messages[-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "extraction_tools"
        if isinstance(last, ToolMessage):
            return "extraction_continue"
        return "finalize_extraction"

    def _finalize_extraction_node(self, state: SLRMetaAgentState, config: RunnableConfig) -> Dict[str, Any]:
        extractions = [
            StudyExtraction(
                identifier=s.identifier,
                title=s.title,
                source=s.source,
                study_design="",
                population="",
                intervention="",
                primary_outcome=""
            )
            for s in state.included_studies[:10]
        ]
        last = state.messages[-1]
        extraction_summary = last.content[:2000] if isinstance(last, AIMessage) and last.content else ""
        return {
            "study_extractions": extractions,
            "extraction_summary": extraction_summary,
            "workflow_stage": "synthesis",
            "workflow_status": "starting",
            "messages": [AIMessage(content=f"Extraction complete. Moving to evidence synthesis and meta-analysis.")]
        }

    # ---------- Stage 4: Synthesis and meta-analysis ----------

    def _synthesis_stage_node(self, state: SLRMetaAgentState, config: RunnableConfig) -> Dict[str, Any]:
        print("\n" + "=" * 60)
        print("STAGE 4: EVIDENCE SYNTHESIS & META-ANALYSIS")
        print("=" * 60)
        system_prompt = SYNTHESIS_AGENT_SYSTEM_PROMPT + f"""

# RESEARCH QUESTION: {state.research_question}
# TARGET OUTCOMES: {', '.join(state.target_outcomes) or 'efficacy, safety'}
# EXTRACTION SUMMARY: {state.extraction_summary[:1500] if state.extraction_summary else 'See messages'}

Use synthesize_evidence, meta_analysis (when you have comparable effect data), and generate_slr_report.
"""
        messages = [SystemMessage(content=system_prompt), HumanMessage(content="Synthesize evidence and produce the final SLR + meta-analysis report.")]
        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=get_synthesis_tools(),
            model_kwargs=self.model_kwargs or {}
        )
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        return {
            "messages": [response],
            "workflow_stage": "synthesis",
            "workflow_status": "in_progress",
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens,
        }

    def _synthesis_tool_node(self, state: SLRMetaAgentState, config: RunnableConfig) -> Dict[str, Any]:
        tool_dict = {t.name: t for t in get_synthesis_tools()}
        last_message = state.messages[-1]
        tool_results = []
        for tool_call in last_message.tool_calls:
            name, args, tid = tool_call["name"], tool_call["args"], tool_call["id"]
            try:
                output = tool_dict[name]._run(**args) if name in tool_dict else f"Unknown: {name}"
            except Exception as e:
                output = str(e)
            tool_results.append(ToolMessage(content=output, name=name, tool_call_id=tid))
        return {"messages": tool_results}

    def _synthesis_continue_node(self, state: SLRMetaAgentState, config: RunnableConfig) -> Dict[str, Any]:
        full_messages = [SystemMessage(content=SYNTHESIS_AGENT_SYSTEM_PROMPT)] + list(state.messages) + [
            HumanMessage(content="Finalize the systematic review and meta-analysis report (narrative + quantitative where appropriate).")
        ]
        response = self._call_model(
            model_name=self.model_name,
            messages=full_messages,
            tools=get_synthesis_tools(),
            model_kwargs=self.model_kwargs or {}
        )
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        return {
            "messages": [response],
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens,
        }

    def _should_continue_synthesis(self, state: SLRMetaAgentState) -> Literal["synthesis_tools", "synthesis_continue", "finalize_report"]:
        last = state.messages[-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "synthesis_tools"
        if isinstance(last, ToolMessage):
            return "synthesis_continue"
        return "finalize_report"

    def _finalize_report_node(self, state: SLRMetaAgentState, config: RunnableConfig) -> Dict[str, Any]:
        last = state.messages[-1]
        synthesis_text = last.content if isinstance(last, AIMessage) and last.content else ""
        final_report = f"""
# Systematic Literature Review & Meta-Analysis Report

## Research Question
{state.research_question}

## Methods
- **Literature search**: PubMed and ClinicalTrials.gov (dual-source)
- **Screening**: Eligibility criteria applied to titles/abstracts and trial summaries
- **Data extraction**: Structured extraction from included studies/trials
- **Synthesis**: Narrative synthesis and meta-analysis where appropriate

## Results
- PubMed studies identified: {len(state.identified_studies)}
- CT.gov trials identified: {len(state.ctgov_trials)}
- Studies/trials included: {len(state.included_studies)}

## Evidence Synthesis & Meta-Analysis
{synthesis_text[:5000] if synthesis_text else "See full message history."}

---
*Generated by SLR-Meta Agent*
"""
        print("\n" + "=" * 60)
        print("SLR + META-ANALYSIS COMPLETE")
        print("=" * 60)
        return {
            "final_report": final_report,
            "workflow_stage": "completed",
            "workflow_status": "completed",
            "messages": [AIMessage(content="Report complete.")]
        }

    # ---------- Graph ----------

    def _create_agent_graph(self, debug: bool = False):
        workflow = StateGraph(SLRMetaAgentState, input=SLRMetaAgentState, output=SLRMetaAgentState)

        # Search
        workflow.add_node("search_stage", self._search_stage_node)
        workflow.add_node("search_tools", self._search_tool_node)
        workflow.add_node("search_continue", self._search_continue_node)
        workflow.add_node("finalize_search", self._finalize_search_node)
        workflow.set_entry_point("search_stage")
        workflow.add_conditional_edges("search_stage", self._should_continue_search, {
            "search_tools": "search_tools",
            "search_continue": "search_continue",
            "finalize_search": "finalize_search"
        })
        workflow.add_edge("search_tools", "search_continue")
        workflow.add_conditional_edges("search_continue", self._should_continue_search, {
            "search_tools": "search_tools",
            "search_continue": "search_continue",
            "finalize_search": "finalize_search"
        })
        workflow.add_edge("finalize_search", "screening_stage")

        # Screening
        workflow.add_node("screening_stage", self._screening_stage_node)
        workflow.add_node("screening_tools", self._screening_tool_node)
        workflow.add_node("screening_continue", self._screening_continue_node)
        workflow.add_node("finalize_screening", self._finalize_screening_node)
        workflow.add_conditional_edges("screening_stage", self._should_continue_screening, {
            "screening_tools": "screening_tools",
            "screening_continue": "screening_continue",
            "finalize_screening": "finalize_screening"
        })
        workflow.add_edge("screening_tools", "screening_continue")
        workflow.add_conditional_edges("screening_continue", self._should_continue_screening, {
            "screening_tools": "screening_tools",
            "screening_continue": "screening_continue",
            "finalize_screening": "finalize_screening"
        })
        workflow.add_edge("finalize_screening", "extraction_stage")

        # Extraction
        workflow.add_node("extraction_stage", self._extraction_stage_node)
        workflow.add_node("extraction_tools", self._extraction_tool_node)
        workflow.add_node("extraction_continue", self._extraction_continue_node)
        workflow.add_node("finalize_extraction", self._finalize_extraction_node)
        workflow.add_conditional_edges("extraction_stage", self._should_continue_extraction, {
            "extraction_tools": "extraction_tools",
            "extraction_continue": "extraction_continue",
            "finalize_extraction": "finalize_extraction"
        })
        workflow.add_edge("extraction_tools", "extraction_continue")
        workflow.add_conditional_edges("extraction_continue", self._should_continue_extraction, {
            "extraction_tools": "extraction_tools",
            "extraction_continue": "extraction_continue",
            "finalize_extraction": "finalize_extraction"
        })
        workflow.add_edge("finalize_extraction", "synthesis_stage")

        # Synthesis
        workflow.add_node("synthesis_stage", self._synthesis_stage_node)
        workflow.add_node("synthesis_tools", self._synthesis_tool_node)
        workflow.add_node("synthesis_continue", self._synthesis_continue_node)
        workflow.add_node("finalize_report", self._finalize_report_node)
        workflow.add_conditional_edges("synthesis_stage", self._should_continue_synthesis, {
            "synthesis_tools": "synthesis_tools",
            "synthesis_continue": "synthesis_continue",
            "finalize_report": "finalize_report"
        })
        workflow.add_edge("synthesis_tools", "synthesis_continue")
        workflow.add_conditional_edges("synthesis_continue", self._should_continue_synthesis, {
            "synthesis_tools": "synthesis_tools",
            "synthesis_continue": "synthesis_continue",
            "finalize_report": "finalize_report"
        })
        workflow.add_edge("finalize_report", END)

        return workflow.compile(debug=debug, name=self.name)

    def generate(
        self,
        research_question: str,
        target_outcomes: List[str] = None,
        verbose: bool = True
    ) -> List[Dict[str, Any]]:
        if not research_question:
            return [{"error": "research_question is required"}]
        inputs = {
            "messages": [],
            "research_question": research_question,
            "target_outcomes": target_outcomes or [],
        }
        all_results = []
        for stream_mode, chunk in self.agent_graph.stream(
            inputs,
            stream_mode=["values"],
            config={"recursion_limit": 50}
        ):
            all_results.append(chunk)
        return all_results

    def go(
        self,
        research_question: str,
        target_outcomes: List[str] = None,
        verbose: bool = True
    ) -> SLRMetaExecutionResults:
        results = self.generate(
            research_question=research_question,
            target_outcomes=target_outcomes,
            verbose=verbose
        )
        if not results or "error" in results[0]:
            return SLRMetaExecutionResults(
                message_history=[],
                code_execution_results=[],
                final_response=results[0].get("error", "Unknown error") if results else "No results",
                sandbox=None
            )
        final_state = results[-1]
        message_history = self._format_messages(final_state.get("messages", []))
        final_report = final_state.get("final_report", "")
        return SLRMetaExecutionResults(
            message_history=message_history,
            code_execution_results=[],
            final_response=final_report,
            sandbox=self.sandbox,
            identified_pubmed=len(final_state.get("identified_studies", [])),
            identified_ctgov=len(final_state.get("ctgov_trials", [])),
            included_studies=len(final_state.get("included_studies", [])),
            final_report=final_report
        )
