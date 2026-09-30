# InformGen Agent

A workflow agent for document generation that iteratively writes sections based on templates and source materials.

**Paper**: Wang, Z., Gao, J., Danek, B., Theodorou, B., Shaik, R., Thati, S., Won, S., & Sun, J. (2025). Compliance and Factuality of Large Language Models for Clinical Research Document Generation. *Journal of the American Medical Informatics Association*.

```bibtex
@article{wang2025informgen,
  title={Compliance and Factuality of Large Language Models for Clinical Research Document Generation},
  author={Wang, Zifeng and Gao, Junyi and Danek, Benjamin and Theodorou, Brandon and Shaik, Ruba and Thati, Shivashankar and Won, Seunghyun and Sun, Jimeng},
  journal={Journal of the American Medical Informatics Association},
  year={2025}
}
```

## Overview

The InformGen agent automates document generation by:
1. Reading source text documents from a sandbox
2. Processing a document template section by section
3. Writing each section with iterative refinement (write → review → revise)
4. Assembling the final document

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     InformGen Workflow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐     ┌───────────────┐     ┌─────────────────┐   │
│  │Initialize│────▶│Section Writer │────▶│Section Reviewer │   │
│  └──────────┘     └───────────────┘     └─────────────────┘   │
│                          ▲                       │             │
│                          │      ┌────────────────┘             │
│                          │      ▼                              │
│                   ┌──────┴──────────────┐                      │
│                   │ APPROVED?           │                      │
│                   │ - Yes: Complete     │                      │
│                   │ - No: Revise        │                      │
│                   └─────────────────────┘                      │
│                          │                                     │
│                          ▼                                     │
│                 ┌─────────────────┐     ┌───────────────────┐ │
│                 │Complete Section │────▶│Assemble Document  │ │
│                 └─────────────────┘     └───────────────────┘ │
│                          │                       │             │
│                          ▼                       ▼             │
│                   More sections?            Final Document     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Usage

### Basic Example

```python
from biodsa.agents.informgen import InformGenAgent

# Initialize the agent
agent = InformGenAgent(
    model_name="gpt-4o",
    api_type="azure",
    api_key="your-api-key",
    endpoint="your-endpoint",
    max_iterations_per_section=3  # Max refinement iterations per section
)

# Register workspace with source documents
agent.register_workspace(workspace_dir="/path/to/source/docs")

# Define document template
template = [
    {
        "title": "Executive Summary",
        "guidance": "Write a concise executive summary covering the key findings and recommendations. Keep it under 500 words."
    },
    {
        "title": "Introduction",
        "guidance": "Introduce the topic, provide background context, and state the purpose of this document."
    },
    {
        "title": "Methodology",
        "guidance": "Describe the approach and methods used in the analysis. Include data sources and analytical techniques."
    },
    {
        "title": "Results",
        "guidance": "Present the key findings with supporting data and evidence from the source materials."
    },
    {
        "title": "Conclusions",
        "guidance": "Summarize the main conclusions and provide actionable recommendations."
    }
]

# Generate the document
result = agent.go(
    document_template=template,
    source_documents=[
        "/workdir/research_paper.txt",
        "/workdir/data_analysis.txt",
        "/workdir/notes.txt"
    ]
)

# Access results
print(result.final_document)  # The complete generated document
print(result.completed_sections)  # Individual section details
print(f"Tokens used: {result.total_input_tokens} input, {result.total_output_tokens} output")
```

### Uploading Source Documents

```python
# Option 1: Upload files individually
agent.register_source_documents([
    "/local/path/to/doc1.txt",
    "/local/path/to/doc2.txt"
])

# Option 2: Upload entire workspace (all .csv, .txt files)
agent.register_workspace(workspace_dir="/local/path/to/sources")
```

### Custom Iteration Control

```python
# Allow more iterations for complex sections
agent = InformGenAgent(
    model_name="gpt-4o",
    api_type="azure",
    api_key="your-api-key",
    endpoint="your-endpoint",
    max_iterations_per_section=5  # More refinement passes
)
```

## Document Template Format

Each section in the template should have:

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | The section title (used as heading) |
| `guidance` | string | Instructions for writing this section |

### Example Templates

**Research Report:**
```python
template = [
    {"title": "Abstract", "guidance": "Write a 150-250 word abstract summarizing the research objectives, methods, results, and conclusions."},
    {"title": "Introduction", "guidance": "Provide background on the topic, review relevant literature, and state the research questions."},
    {"title": "Materials and Methods", "guidance": "Describe experimental design, data collection, and analysis methods."},
    {"title": "Results", "guidance": "Present findings objectively with references to figures and tables."},
    {"title": "Discussion", "guidance": "Interpret results, compare with literature, discuss limitations."},
    {"title": "Conclusions", "guidance": "Summarize key findings and their implications."},
]
```

**Business Proposal:**
```python
template = [
    {"title": "Executive Summary", "guidance": "One-page overview of the proposal and key benefits."},
    {"title": "Problem Statement", "guidance": "Define the problem or opportunity being addressed."},
    {"title": "Proposed Solution", "guidance": "Detail the solution and its components."},
    {"title": "Implementation Plan", "guidance": "Timeline, milestones, and resource requirements."},
    {"title": "Budget", "guidance": "Cost breakdown and financial projections."},
    {"title": "Risk Assessment", "guidance": "Identify risks and mitigation strategies."},
]
```

## Components

### State (`state.py`)

- `InformGenAgentState`: Main workflow state tracking progress
- `SectionWriterState`: State for section writing sub-workflow
- `SectionTemplate`: Definition of a document section
- `SectionContent`: Completed section with content and metadata

### Prompts (`prompt.py`)

- `ORCHESTRATOR_SYSTEM_PROMPT`: Instructions for workflow coordination
- `SECTION_WRITER_SYSTEM_PROMPT`: Instructions for section writing
- `SECTION_REVIEWER_SYSTEM_PROMPT`: Instructions for section review
- `DOCUMENT_ASSEMBLY_PROMPT`: Instructions for final assembly

### Tools (`tools.py`)

- `ReadSourceDocumentTool`: Read source files from sandbox
- `ListSourceDocumentsTool`: List available source files
- `WriteSectionTool`: Submit written section content
- `ApproveSectionTool`: Approve or request section revision
- `SaveDocumentTool`: Save final document to sandbox

### Agent (`agent.py`)

- `InformGenAgent`: Main agent class
- `InformGenExecutionResults`: Results container with document and metadata

## Workflow Details

### Section Writing Process

For each section in the template:

1. **Write**: Generate initial draft based on guidance and source materials
2. **Review**: Evaluate draft against requirements
3. **Decision**:
   - If APPROVED: Mark complete, move to next section
   - If NEEDS_REVISION: Provide feedback, repeat from step 1
4. **Limit**: After `max_iterations_per_section`, approve automatically

### Document Assembly

After all sections are complete:
1. Collect all completed sections
2. Format with section headings
3. Add separators between sections
4. Return final document

## Output

The `InformGenExecutionResults` object provides:

```python
result.final_document        # Complete document as string
result.completed_sections    # List of section dicts with metadata
result.message_history       # Full conversation history
result.total_input_tokens    # Token usage
result.total_output_tokens

# Get specific section
intro = result.get_section_by_title("Introduction")
```

## Best Practices

1. **Clear Guidance**: Provide specific, actionable guidance for each section
2. **Quality Sources**: Ensure source documents contain relevant information
3. **Reasonable Sections**: Keep section count manageable (5-10 sections typical)
4. **Iteration Balance**: 2-3 iterations usually sufficient; more for complex sections
