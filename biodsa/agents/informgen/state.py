"""
State definitions for the InformGen agent.

The InformGen agent generates documents by iteratively writing sections
based on a template and source documents.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Annotated, Sequence
from langgraph.graph.message import add_messages, BaseMessage


class SectionTemplate(BaseModel):
    """A template for a single document section."""
    title: str = Field(description="The title of the section")
    guidance: str = Field(description="Instructions for writing this section")
    order: int = Field(default=0, description="Order of the section in the document")


class SectionContent(BaseModel):
    """Content for a completed section."""
    title: str = Field(description="The title of the section")
    content: str = Field(description="The written content of the section")
    iteration_count: int = Field(default=1, description="Number of iterations to write this section")
    status: str = Field(default="pending", description="Status: pending, in_progress, completed, needs_revision")
    feedback: Optional[str] = Field(default=None, description="Feedback for revision if needed")


class InformGenAgentState(BaseModel):
    """State for the InformGen agent workflow."""
    
    # Message history
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Input: Document template
    document_template: List[SectionTemplate] = Field(
        default_factory=list, 
        description="List of section templates defining the document structure"
    )
    
    # Input: Source documents (paths in sandbox)
    source_documents: List[str] = Field(
        default_factory=list,
        description="Paths to source text documents in the sandbox"
    )
    
    # Source document contents (cached after reading)
    source_contents: Dict[str, str] = Field(
        default_factory=dict,
        description="Cached contents of source documents (path -> content)"
    )
    
    # Progress tracking
    current_section_index: int = Field(
        default=0, 
        description="Index of the current section being written"
    )
    
    current_iteration: int = Field(
        default=0,
        description="Current iteration number for the current section"
    )
    
    max_iterations_per_section: int = Field(
        default=3,
        description="Maximum number of iterations allowed per section"
    )
    
    # Output: Written sections
    completed_sections: List[SectionContent] = Field(
        default_factory=list,
        description="List of completed section contents"
    )
    
    # Current working section
    current_section_draft: Optional[str] = Field(
        default=None,
        description="Current draft of the section being worked on"
    )
    
    # Final document
    final_document: str = Field(
        default="",
        description="The final assembled document"
    )
    
    # Workflow control
    workflow_status: str = Field(
        default="initializing",
        description="Overall workflow status: initializing, writing, reviewing, completed"
    )
    
    # Token tracking
    total_input_tokens: int = Field(default=0, description="Total input tokens used")
    total_output_tokens: int = Field(default=0, description="Total output tokens used")


class SectionWriterState(BaseModel):
    """State for the section writer sub-workflow."""
    
    # Message history for this section
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Current section being written
    section_template: Optional[SectionTemplate] = Field(
        default=None,
        description="Template for the current section"
    )
    
    # Source content available
    source_contents: Dict[str, str] = Field(
        default_factory=dict,
        description="Contents of source documents"
    )
    
    # Previously completed sections (for context)
    previous_sections: List[SectionContent] = Field(
        default_factory=list,
        description="Previously completed sections for context"
    )
    
    # Current draft
    current_draft: Optional[str] = Field(
        default=None,
        description="Current draft of this section"
    )
    
    # Iteration tracking
    current_iteration: int = Field(default=0, description="Current iteration number")
    max_iterations: int = Field(default=3, description="Maximum iterations allowed")
    
    # Review feedback
    review_feedback: Optional[str] = Field(
        default=None,
        description="Feedback from the reviewer agent"
    )
    
    # Status
    is_complete: bool = Field(default=False, description="Whether this section is complete")
    
    # Token tracking
    total_input_tokens: int = Field(default=0, description="Total input tokens used")
    total_output_tokens: int = Field(default=0, description="Total output tokens used")
