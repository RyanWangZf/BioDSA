"""
Tools for the InformGen agent.

These tools support document generation by reading source materials,
writing sections, and managing the document workflow.
"""
from typing import Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper


class ReadSourceDocumentInput(BaseModel):
    """Input schema for reading a source document."""
    file_path: str = Field(
        description="Path to the source document file in the sandbox (e.g., '/workdir/source1.txt')"
    )


class ReadSourceDocumentTool(BaseTool):
    """Tool for reading source documents from the sandbox."""
    
    name: str = "read_source_document"
    description: str = """Read the contents of a source document from the sandbox.
    
Use this tool to read source documents that contain the material you need to reference
when writing document sections. Provide the full path to the file in the sandbox.

Returns the full text content of the document.
"""
    args_schema: Type[BaseModel] = ReadSourceDocumentInput
    sandbox: Optional[ExecutionSandboxWrapper] = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None, **kwargs):
        super().__init__(**kwargs)
        self.sandbox = sandbox
    
    def _run(self, file_path: str) -> str:
        """Read the source document from the sandbox."""
        if self.sandbox is None or self.sandbox.container is None:
            return f"Error: Sandbox is not available. Cannot read file: {file_path}"
        
        try:
            # Execute cat command to read file
            exit_code, output = self.sandbox.container.exec_run(
                f'cat "{file_path}"',
                workdir=self.sandbox.workdir
            )
            
            if exit_code != 0:
                return f"Error reading file {file_path}: {output.decode('utf-8')}"
            
            content = output.decode('utf-8')
            return content
            
        except Exception as e:
            return f"Error reading source document: {str(e)}"


class ListSourceDocumentsInput(BaseModel):
    """Input schema for listing source documents."""
    directory: str = Field(
        default="/workdir",
        description="Directory to list files from (default: /workdir)"
    )


class ListSourceDocumentsTool(BaseTool):
    """Tool for listing available source documents in the sandbox."""
    
    name: str = "list_source_documents"
    description: str = """List all available source documents in the sandbox directory.
    
Use this tool to discover what source documents are available for reference.
Returns a list of file paths that can be read with read_source_document.
"""
    args_schema: Type[BaseModel] = ListSourceDocumentsInput
    sandbox: Optional[ExecutionSandboxWrapper] = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None, **kwargs):
        super().__init__(**kwargs)
        self.sandbox = sandbox
    
    def _run(self, directory: str = "/workdir") -> str:
        """List source documents in the sandbox."""
        if self.sandbox is None or self.sandbox.container is None:
            return "Error: Sandbox is not available. Cannot list files."
        
        try:
            # Execute ls command to list files
            exit_code, output = self.sandbox.container.exec_run(
                f'ls -la "{directory}"',
                workdir=self.sandbox.workdir
            )
            
            if exit_code != 0:
                return f"Error listing directory {directory}: {output.decode('utf-8')}"
            
            return output.decode('utf-8')
            
        except Exception as e:
            return f"Error listing source documents: {str(e)}"


class WriteSectionInput(BaseModel):
    """Input schema for writing a section."""
    section_title: str = Field(
        description="Title of the section being written"
    )
    section_content: str = Field(
        description="The written content for the section"
    )


class WriteSectionTool(BaseTool):
    """Tool for submitting a written section."""
    
    name: str = "write_section"
    description: str = """Submit the written content for the current section.
    
Use this tool when you have finished writing a section. Provide the section title
and the complete content you have written. This will save the section and mark it
for review.

The content should be well-formatted markdown text ready to be included in the final document.
"""
    args_schema: Type[BaseModel] = WriteSectionInput
    
    def _run(self, section_title: str, section_content: str) -> str:
        """Submit the written section."""
        # This tool's output is processed by the agent to update state
        return f"Section '{section_title}' submitted successfully. Content length: {len(section_content)} characters."


class ReviewSectionInput(BaseModel):
    """Input schema for reviewing a section."""
    section_title: str = Field(
        description="Title of the section being reviewed"
    )
    section_content: str = Field(
        description="The content of the section to review"
    )
    guidance: str = Field(
        description="The original guidance/requirements for this section"
    )


class ReviewSectionTool(BaseTool):
    """Tool for reviewing a written section."""
    
    name: str = "review_section"
    description: str = """Review a written section and provide feedback.
    
Use this tool to evaluate whether a section meets the requirements specified in the guidance.
Returns an assessment of whether the section is approved or needs revision, along with specific feedback.
"""
    args_schema: Type[BaseModel] = ReviewSectionInput
    
    def _run(self, section_title: str, section_content: str, guidance: str) -> str:
        """Review the section - actual review is done by the LLM agent."""
        # This is a placeholder - the actual review is done by the reviewer agent
        return f"Review requested for section '{section_title}'. Please evaluate based on the guidance provided."


class ApproveSectionInput(BaseModel):
    """Input schema for approving a section."""
    section_title: str = Field(
        description="Title of the section being approved"
    )
    approval_status: str = Field(
        description="APPROVED or NEEDS_REVISION"
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Feedback for the section (required if NEEDS_REVISION)"
    )


class ApproveSectionTool(BaseTool):
    """Tool for approving or requesting revision of a section."""
    
    name: str = "approve_section"
    description: str = """Approve a section or request revisions.
    
After reviewing a section, use this tool to either:
- APPROVED: Mark the section as complete and ready for the final document
- NEEDS_REVISION: Request changes with specific feedback

If requesting revision, you must provide feedback explaining what needs to be changed.
"""
    args_schema: Type[BaseModel] = ApproveSectionInput
    
    def _run(self, section_title: str, approval_status: str, feedback: Optional[str] = None) -> str:
        """Approve or request revision of the section."""
        if approval_status == "APPROVED":
            return f"Section '{section_title}' has been approved and marked as complete."
        elif approval_status == "NEEDS_REVISION":
            if not feedback:
                return "Error: Feedback is required when requesting revisions."
            return f"Section '{section_title}' needs revision. Feedback: {feedback}"
        else:
            return f"Error: Invalid approval status '{approval_status}'. Use 'APPROVED' or 'NEEDS_REVISION'."


class SaveDocumentInput(BaseModel):
    """Input schema for saving the final document."""
    filename: str = Field(
        description="Filename for the output document (e.g., 'report.md')"
    )
    content: str = Field(
        description="The complete document content to save"
    )


class SaveDocumentTool(BaseTool):
    """Tool for saving the final assembled document to the sandbox."""
    
    name: str = "save_document"
    description: str = """Save the final assembled document to the sandbox.
    
Use this tool when the document is complete and ready to be saved.
Provide a filename and the complete document content.
The file will be saved in the sandbox workdir.
"""
    args_schema: Type[BaseModel] = SaveDocumentInput
    sandbox: Optional[ExecutionSandboxWrapper] = None
    
    def __init__(self, sandbox: ExecutionSandboxWrapper = None, **kwargs):
        super().__init__(**kwargs)
        self.sandbox = sandbox
    
    def _run(self, filename: str, content: str) -> str:
        """Save the document to the sandbox."""
        if self.sandbox is None:
            return f"Warning: No sandbox available. Document content:\n\n{content}"
        
        try:
            # Write file to sandbox
            file_path = f"{self.sandbox.workdir}/{filename}"
            self.sandbox.upload_file(
                data=content,
                target_file_path=file_path
            )
            return f"Document saved successfully to {file_path}"
            
        except Exception as e:
            return f"Error saving document: {str(e)}"


def get_informgen_writer_tools(sandbox: ExecutionSandboxWrapper = None) -> List[BaseTool]:
    """Get tools for the section writer agent."""
    return [
        ReadSourceDocumentTool(sandbox=sandbox),
        ListSourceDocumentsTool(sandbox=sandbox),
        WriteSectionTool(),
    ]


def get_informgen_reviewer_tools() -> List[BaseTool]:
    """Get tools for the section reviewer agent."""
    return [
        ApproveSectionTool(),
    ]


def get_informgen_orchestrator_tools(sandbox: ExecutionSandboxWrapper = None) -> List[BaseTool]:
    """Get all tools for the orchestrator agent."""
    return [
        ReadSourceDocumentTool(sandbox=sandbox),
        ListSourceDocumentsTool(sandbox=sandbox),
        SaveDocumentTool(sandbox=sandbox),
    ]
