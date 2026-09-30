"""
InformGen Agent Module

A workflow agent for document generation that:
- Takes a document template (list of sections with titles and guidance)
- Reads source text documents from a sandbox (auto-discovered)
- Writes sections iteratively with review and refinement
- Assembles the final document

Usage:
    from biodsa.agents.informgen import InformGenAgent
    
    agent = InformGenAgent(
        model_name="gpt-4o",
        api_type="azure",
        api_key="your-api-key",
        endpoint="your-endpoint"
    )
    
    # Register workspace with source documents (uploads to sandbox)
    agent.register_workspace(workspace_dir="/path/to/sources")
    
    # Define document template
    template = [
        {"title": "Introduction", "guidance": "Write an introduction..."},
        {"title": "Methods", "guidance": "Describe the methodology..."},
        {"title": "Results", "guidance": "Present the findings..."},
    ]
    
    # Generate the document (source docs auto-discovered from sandbox)
    result = agent.go(document_template=template)
    
    # Access the generated document
    print(result.final_document)
"""

from biodsa.agents.informgen.agent import InformGenAgent, InformGenExecutionResults
from biodsa.agents.informgen.state import (
    InformGenAgentState,
    SectionWriterState,
    SectionTemplate,
    SectionContent
)

__all__ = [
    "InformGenAgent",
    "InformGenExecutionResults",
    "InformGenAgentState",
    "SectionWriterState", 
    "SectionTemplate",
    "SectionContent"
]
