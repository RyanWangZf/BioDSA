"""
InformGen Agent: A workflow agent for document generation.

This agent generates documents section by section based on a template
and source materials. It supports iterative refinement of each section.
"""
import os
from typing import Literal, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from biodsa.agents.base_agent import BaseAgent, run_with_retry
from biodsa.agents.informgen.state import (
    InformGenAgentState,
    SectionWriterState,
    SectionTemplate,
    SectionContent
)
from biodsa.agents.informgen.prompt import (
    ORCHESTRATOR_SYSTEM_PROMPT,
    SECTION_WRITER_SYSTEM_PROMPT,
    SECTION_WRITER_ITERATION_PROMPT,
    SECTION_REVIEWER_SYSTEM_PROMPT,
    DOCUMENT_ASSEMBLY_PROMPT,
    ITERATION_BUDGET_PROMPT,
    PROGRESS_UPDATE_PROMPT
)
from biodsa.agents.informgen.tools import (
    ReadSourceDocumentTool,
    ListSourceDocumentsTool,
    WriteSectionTool,
    ApproveSectionTool,
    SaveDocumentTool,
    get_informgen_writer_tools,
    get_informgen_reviewer_tools,
    get_informgen_orchestrator_tools
)
from biodsa.sandbox.execution import ExecutionResults


class InformGenExecutionResults(ExecutionResults):
    """Extended execution results for InformGen agent."""
    
    def __init__(
        self,
        message_history: List[Dict[str, str]],
        code_execution_results: List[Dict[str, str]],
        final_response: str,
        sandbox=None,
        completed_sections: List[Dict[str, Any]] = None,
        final_document: str = "",
        total_input_tokens: int = 0,
        total_output_tokens: int = 0
    ):
        super().__init__(
            message_history=message_history,
            code_execution_results=code_execution_results,
            final_response=final_response,
            sandbox=sandbox
        )
        self.completed_sections = completed_sections or []
        self.final_document = final_document
        self.total_input_tokens = total_input_tokens
        self.total_output_tokens = total_output_tokens
    
    def get_section_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """Get a specific section by its title."""
        for section in self.completed_sections:
            if section.get('title') == title:
                return section
        return None
    
    def get_document(self) -> str:
        """Get the final assembled document."""
        return self.final_document


class InformGenAgent(BaseAgent):
    """
    InformGen Agent: Document generation workflow agent.
    
    This agent takes a document template (list of section specifications) and 
    source documents, then generates the document section by section with 
    iterative refinement.
    
    Workflow:
    1. Read source documents
    2. For each section in template:
        a. Write initial draft based on guidance and sources
        b. Review the draft
        c. If needs revision, iterate (up to max_iterations)
        d. Mark section as complete
    3. Assemble final document from all sections
    """
    
    name = "informgen"
    max_iterations_per_section: int = 3
    
    def __init__(
        self,
        model_name: str,
        api_type: str,
        api_key: str,
        endpoint: str = None,
        container_id: str = None,
        model_kwargs: Dict[str, Any] = None,
        max_iterations_per_section: int = 3,
        llm_timeout: Optional[float] = None,
        **kwargs
    ):
        """
        Initialize the InformGen agent.
        
        Args:
            model_name: Name of the LLM model to use
            api_type: API type (e.g., 'azure', 'openai')
            api_key: API key for the LLM service
            endpoint: API endpoint
            container_id: Optional Docker container ID for sandbox
            model_kwargs: Additional kwargs for the LLM
            max_iterations_per_section: Maximum refinement iterations per section
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
        self.max_iterations_per_section = max_iterations_per_section
        self.agent_graph = self._create_agent_graph()
    
    def _build_orchestrator_system_prompt(self, state: InformGenAgentState) -> str:
        """Build the system prompt for the orchestrator agent."""
        source_docs_str = "\n".join([f"- {path}" for path in state.source_documents])
        if not source_docs_str:
            source_docs_str = "No source documents registered yet."
        
        return ORCHESTRATOR_SYSTEM_PROMPT.format(
            source_documents_str=source_docs_str,
            num_sections=len(state.document_template),
            current_section_index=state.current_section_index,
            workflow_status=state.workflow_status
        )
    
    def _build_writer_system_prompt(
        self,
        section_template: SectionTemplate,
        source_contents: Dict[str, str],
        previous_sections: List[SectionContent]
    ) -> str:
        """Build the system prompt for the section writer."""
        # Summarize source contents
        source_summary_parts = []
        for path, content in source_contents.items():
            # Truncate long content for the prompt
            preview = content[:2000] + "..." if len(content) > 2000 else content
            source_summary_parts.append(f"## {path}\n{preview}")
        source_contents_summary = "\n\n".join(source_summary_parts) if source_summary_parts else "No source documents available."
        
        # Summarize previous sections
        prev_sections_parts = []
        for section in previous_sections:
            prev_sections_parts.append(f"## {section.title}\n{section.content[:500]}...")
        previous_sections_summary = "\n\n".join(prev_sections_parts) if prev_sections_parts else "This is the first section."
        
        return SECTION_WRITER_SYSTEM_PROMPT.format(
            section_title=section_template.title,
            section_guidance=section_template.guidance,
            source_contents_summary=source_contents_summary,
            previous_sections_summary=previous_sections_summary
        )
    
    def _build_reviewer_system_prompt(
        self,
        section_template: SectionTemplate,
        draft_content: str,
        source_contents: Dict[str, str]
    ) -> str:
        """Build the system prompt for the section reviewer."""
        # Summarize source contents
        source_summary_parts = []
        for path, content in source_contents.items():
            preview = content[:1000] + "..." if len(content) > 1000 else content
            source_summary_parts.append(f"## {path}\n{preview}")
        source_contents_summary = "\n\n".join(source_summary_parts) if source_summary_parts else "No source documents available."
        
        return SECTION_REVIEWER_SYSTEM_PROMPT.format(
            section_title=section_template.title,
            section_guidance=section_template.guidance,
            draft_content=draft_content,
            source_contents_summary=source_contents_summary
        )
    
    def _get_orchestrator_tools(self):
        """Get tools for the orchestrator agent."""
        return get_informgen_orchestrator_tools(sandbox=self.sandbox)
    
    def _get_writer_tools(self):
        """Get tools for the section writer agent."""
        return get_informgen_writer_tools(sandbox=self.sandbox)
    
    def _get_reviewer_tools(self):
        """Get tools for the section reviewer agent."""
        return get_informgen_reviewer_tools()
    
    # =========================================================================
    # Main Workflow Nodes
    # =========================================================================
    
    def _initialize_node(self, state: InformGenAgentState, config: RunnableConfig) -> InformGenAgentState:
        """Initialize the workflow by reading source documents."""
        print("Initializing InformGen workflow...")
        
        # Read all source documents into cache
        source_contents = {}
        read_tool = ReadSourceDocumentTool(sandbox=self.sandbox)
        
        for doc_path in state.source_documents:
            print(f"Reading source document: {doc_path}")
            content = read_tool._run(file_path=doc_path)
            if not content.startswith("Error"):
                source_contents[doc_path] = content
            else:
                print(f"Warning: {content}")
        
        return {
            "source_contents": source_contents,
            "workflow_status": "writing",
            "current_section_index": 0,
            "messages": [AIMessage(content=f"Initialized workflow. Read {len(source_contents)} source documents. Starting section writing...")]
        }
    
    def _section_writer_node(self, state: InformGenAgentState, config: RunnableConfig) -> InformGenAgentState:
        """Write or revise the current section."""
        current_idx = state.current_section_index
        if current_idx >= len(state.document_template):
            return {"workflow_status": "assembling"}
        
        section_template = state.document_template[current_idx]
        print(f"Writing section {current_idx + 1}/{len(state.document_template)}: {section_template.title}")
        
        # Build system prompt
        system_prompt = self._build_writer_system_prompt(
            section_template=section_template,
            source_contents=state.source_contents,
            previous_sections=state.completed_sections
        )
        
        # Check if this is a revision
        messages = [SystemMessage(content=system_prompt)]
        
        if state.current_section_draft and state.current_iteration > 0:
            # This is a revision - get feedback from the last reviewer response
            feedback = "Please improve the section based on the review."
            for msg in reversed(state.messages):
                if isinstance(msg, AIMessage) and "NEEDS_REVISION" in str(msg.content):
                    feedback = msg.content
                    break
            
            revision_prompt = SECTION_WRITER_ITERATION_PROMPT.format(
                section_title=section_template.title,
                review_feedback=feedback,
                previous_draft=state.current_section_draft
            )
            messages.append(HumanMessage(content=revision_prompt))
        else:
            # First draft
            messages.append(HumanMessage(content=f"Please write the section '{section_template.title}' following the guidance provided."))
        
        # Add iteration budget info
        iteration_info = ITERATION_BUDGET_PROMPT.format(
            current_iteration=state.current_iteration + 1,
            max_iterations=self.max_iterations_per_section,
            budget_message="" if state.current_iteration < self.max_iterations_per_section - 1 
                          else "This is the final iteration. Please finalize the section."
        )
        messages.append(HumanMessage(content=iteration_info))
        
        # Call the model
        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=None,  # Writer generates content directly
            model_kwargs=self.model_kwargs or {}
        )
        
        # Get tokens
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        
        return {
            "messages": [response],
            "current_section_draft": response.content,
            "current_iteration": state.current_iteration + 1,
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens
        }
    
    def _section_reviewer_node(self, state: InformGenAgentState, config: RunnableConfig) -> InformGenAgentState:
        """Review the current section draft."""
        current_idx = state.current_section_index
        section_template = state.document_template[current_idx]
        
        print(f"Reviewing section: {section_template.title} (iteration {state.current_iteration})")
        
        # Build reviewer prompt
        system_prompt = self._build_reviewer_system_prompt(
            section_template=section_template,
            draft_content=state.current_section_draft or "",
            source_contents=state.source_contents
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="Please review this section and provide your assessment.")
        ]
        
        # Call the model
        response = self._call_model(
            model_name=self.model_name,
            messages=messages,
            tools=None,
            model_kwargs=self.model_kwargs or {}
        )
        
        # Get tokens
        input_tokens, output_tokens = self._get_input_output_tokens(response)
        
        return {
            "messages": [response],
            "total_input_tokens": state.total_input_tokens + input_tokens,
            "total_output_tokens": state.total_output_tokens + output_tokens
        }
    
    def _check_review_decision(self, state: InformGenAgentState) -> Literal["approved", "revise", "max_iterations"]:
        """Check the review decision and determine next step."""
        # Check if we've hit max iterations
        if state.current_iteration >= self.max_iterations_per_section:
            print(f"Max iterations ({self.max_iterations_per_section}) reached. Approving section.")
            return "max_iterations"
        
        # Check the last message for approval status
        last_message = state.messages[-1]
        if isinstance(last_message, AIMessage):
            content = str(last_message.content).upper()
            if "APPROVED" in content and "NEEDS_REVISION" not in content:
                return "approved"
            elif "NEEDS_REVISION" in content:
                return "revise"
        
        # Default to approved if unclear
        return "approved"
    
    def _complete_section_node(self, state: InformGenAgentState, config: RunnableConfig) -> InformGenAgentState:
        """Mark the current section as complete and move to the next."""
        current_idx = state.current_section_index
        section_template = state.document_template[current_idx]
        
        print(f"Completing section: {section_template.title}")
        
        # Create completed section
        completed_section = SectionContent(
            title=section_template.title,
            content=state.current_section_draft or "",
            iteration_count=state.current_iteration,
            status="completed"
        )
        
        # Add to completed sections
        new_completed_sections = list(state.completed_sections)
        new_completed_sections.append(completed_section)
        
        # Move to next section
        next_idx = current_idx + 1
        workflow_status = "writing" if next_idx < len(state.document_template) else "assembling"
        
        return {
            "completed_sections": new_completed_sections,
            "current_section_index": next_idx,
            "current_section_draft": None,
            "current_iteration": 0,
            "workflow_status": workflow_status,
            "messages": [AIMessage(content=f"Section '{section_template.title}' completed. Moving to next section.")]
        }
    
    def _assemble_document_node(self, state: InformGenAgentState, config: RunnableConfig) -> InformGenAgentState:
        """Assemble the final document from all completed sections."""
        print("Assembling final document...")
        
        # Build the document from completed sections
        document_parts = []
        
        for section in state.completed_sections:
            document_parts.append(f"# {section.title}\n\n{section.content}")
        
        final_document = "\n\n---\n\n".join(document_parts)
        
        # Optionally, we could call the LLM to polish the final document
        # For now, we just concatenate the sections
        
        return {
            "final_document": final_document,
            "workflow_status": "completed",
            "messages": [AIMessage(content=f"Document assembly complete. Total sections: {len(state.completed_sections)}")]
        }
    
    def _should_continue_writing(self, state: InformGenAgentState) -> Literal["write", "assemble", "complete"]:
        """Determine if we should continue writing or assemble."""
        if state.workflow_status == "assembling" or state.current_section_index >= len(state.document_template):
            return "assemble"
        return "write"
    
    def _should_revise_or_complete(self, state: InformGenAgentState) -> Literal["revise", "complete"]:
        """Determine if section needs revision or is complete."""
        decision = self._check_review_decision(state)
        if decision == "revise":
            return "revise"
        return "complete"
    
    # =========================================================================
    # Graph Creation
    # =========================================================================
    
    def _create_agent_graph(self, debug: bool = False):
        """Create the main agent workflow graph."""
        
        workflow = StateGraph(
            InformGenAgentState,
            input=InformGenAgentState,
            output=InformGenAgentState
        )
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("section_writer", self._section_writer_node)
        workflow.add_node("section_reviewer", self._section_reviewer_node)
        workflow.add_node("complete_section", self._complete_section_node)
        workflow.add_node("assemble_document", self._assemble_document_node)
        
        # Set entry point
        workflow.set_entry_point("initialize")
        
        # Add edges
        workflow.add_edge("initialize", "section_writer")
        workflow.add_edge("section_writer", "section_reviewer")
        
        # Conditional edge after review
        workflow.add_conditional_edges(
            "section_reviewer",
            self._should_revise_or_complete,
            {
                "revise": "section_writer",
                "complete": "complete_section"
            }
        )
        
        # After completing a section, check if more sections or assemble
        workflow.add_conditional_edges(
            "complete_section",
            self._should_continue_writing,
            {
                "write": "section_writer",
                "assemble": "assemble_document",
                "complete": END
            }
        )
        
        workflow.add_edge("assemble_document", END)
        
        return workflow.compile(debug=debug, name=self.name)
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    def register_source_documents(self, document_paths: List[str]) -> bool:
        """
        Register source documents to be uploaded to the sandbox.
        
        Args:
            document_paths: List of local file paths to source documents
            
        Returns:
            True if successful
        """
        if self.sandbox is None:
            print("Warning: No sandbox available. Documents will be read from local paths.")
            return False
        
        for local_path in document_paths:
            if os.path.exists(local_path):
                filename = os.path.basename(local_path)
                target_path = f"{self.sandbox.workdir}/{filename}"
                
                with open(local_path, 'r') as f:
                    content = f.read()
                
                self.sandbox.upload_file(
                    data=content,
                    target_file_path=target_path
                )
                print(f"Uploaded: {local_path} -> {target_path}")
            else:
                print(f"Warning: File not found: {local_path}")
        
        return True
    
    def _discover_source_documents(self) -> List[str]:
        """
        Discover source documents in the sandbox workdir.
        
        Returns:
            List of file paths in the sandbox workdir
        """
        if self.sandbox is None or self.sandbox.container is None:
            print("Warning: No sandbox available. Cannot discover source documents.")
            return []
        
        try:
            # List files in workdir
            exit_code, output = self.sandbox.container.exec_run(
                f'ls -1 {self.sandbox.workdir}',
                workdir=self.sandbox.workdir
            )
            
            if exit_code != 0:
                print(f"Warning: Could not list sandbox workdir: {output.decode('utf-8')}")
                return []
            
            files = output.decode('utf-8').strip().split('\n')
            # Filter to text-like files and construct full paths
            text_extensions = ('.txt', '.md', '.json', '.xml', '.csv', '.tsv', '.html', '.rst')
            source_docs = []
            for f in files:
                f = f.strip()
                if f and (f.lower().endswith(text_extensions) or '.' not in f):
                    source_docs.append(f"{self.sandbox.workdir}/{f}")
            
            print(f"Discovered {len(source_docs)} source documents in sandbox")
            return source_docs
            
        except Exception as e:
            print(f"Warning: Error discovering source documents: {e}")
            return []
    
    def generate(
        self,
        document_template: List[Dict[str, str]],
        source_documents: Optional[List[str]] = None,
        verbose: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate a document based on the template and source materials.
        
        Args:
            document_template: List of dicts with 'title' and 'guidance' keys
            source_documents: Optional list of paths to source documents (in sandbox).
                              If not provided, auto-discovers files in the sandbox workdir.
            verbose: Whether to print progress
            
        Returns:
            List of state snapshots from the workflow
        """
        # Auto-discover source documents if not provided
        if source_documents is None:
            source_documents = self._discover_source_documents()
            if verbose:
                print(f"Auto-discovered source documents: {source_documents}")
        
        # Convert template to SectionTemplate objects
        templates = [
            SectionTemplate(
                title=t.get('title', f'Section {i+1}'),
                guidance=t.get('guidance', ''),
                order=i
            )
            for i, t in enumerate(document_template)
        ]
        
        # Prepare inputs
        inputs = {
            "messages": [],
            "document_template": templates,
            "source_documents": source_documents,
            "max_iterations_per_section": self.max_iterations_per_section
        }
        
        # Run the workflow
        all_results = []
        try:
            for stream_mode, chunk in self.agent_graph.stream(
                inputs,
                stream_mode=["values"],
                config={"recursion_limit": 100}
            ):
                if verbose:
                    # Print progress
                    if 'workflow_status' in chunk:
                        print(f"Status: {chunk['workflow_status']}")
                    if 'current_section_index' in chunk:
                        total = len(templates)
                        current = chunk['current_section_index']
                        print(f"Progress: {current}/{total} sections")
                all_results.append(chunk)
                
        except Exception as e:
            print(f"Error during generation: {e}")
            raise
        
        return all_results
    
    def go(
        self,
        document_template: List[Dict[str, str]],
        source_documents: Optional[List[str]] = None,
        verbose: bool = True
    ) -> InformGenExecutionResults:
        """
        Execute the document generation workflow.
        
        Args:
            document_template: List of dicts with 'title' and 'guidance' keys
                Example: [
                    {"title": "Introduction", "guidance": "Write an introduction covering..."},
                    {"title": "Methods", "guidance": "Describe the methodology..."},
                ]
            source_documents: Optional list of paths to source documents in the sandbox.
                              If not provided, auto-discovers files in the sandbox workdir.
            verbose: Whether to print progress
            
        Returns:
            InformGenExecutionResults with the generated document and metadata
        """
        results = self.generate(
            document_template=document_template,
            source_documents=source_documents,
            verbose=verbose
        )
        
        # Get final state
        final_state = results[-1]
        
        # Extract results
        message_history = self._format_messages(final_state.get('messages', []))
        completed_sections = [
            {
                'title': s.title,
                'content': s.content,
                'iteration_count': s.iteration_count,
                'status': s.status
            }
            for s in final_state.get('completed_sections', [])
        ]
        final_document = final_state.get('final_document', '')
        final_response = final_document if final_document else "Document generation completed."
        
        return InformGenExecutionResults(
            message_history=message_history,
            code_execution_results=[],
            final_response=final_response,
            sandbox=self.sandbox,
            completed_sections=completed_sections,
            final_document=final_document,
            total_input_tokens=final_state.get('total_input_tokens', 0),
            total_output_tokens=final_state.get('total_output_tokens', 0)
        )
