"""
Example script demonstrating the InformGen agent.

This script generates a structured research report from source documents
about CRISPR-Cas9 gene therapy for sickle cell disease.
"""
import sys
import os

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(current_dir, ".env"))

from biodsa.agents.informgen import InformGenAgent

def main():
    # Initialize the agent
    agent = InformGenAgent(
        model_name="gpt-5",
        api_type="azure",
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        max_iterations_per_section=2  # Allow up to 2 refinement iterations per section
    )

    # Register workspace with source documents
    # All .txt files in this directory will be uploaded to the sandbox
    source_dir = os.path.join(current_dir, "tutorials", "test_data")
    agent.register_workspace(workspace_dir=source_dir)

    # Define the document template - a research report structure
    template = [
        {
            "title": "Executive Summary",
            "guidance": """Write a concise executive summary (300-400 words) that covers:
            - The main objective of the CRISPR-Cas9 gene therapy study
            - Key efficacy results (HbF levels, VOC reduction)
            - Safety profile summary
            - Main conclusions and significance
            This should be accessible to a general scientific audience."""
        },
        {
            "title": "Introduction and Background",
            "guidance": """Write an introduction section that covers:
            - Overview of sickle cell disease (prevalence, pathophysiology, clinical impact)
            - Current treatment landscape and limitations
            - Rationale for gene therapy approaches
            - BCL11A as a therapeutic target
            - Brief introduction to CRISPR-Cas9 technology
            Use information from the background literature source document."""
        },
        {
            "title": "Study Design and Methods",
            "guidance": """Describe the clinical trial methodology including:
            - Trial design (phase, centers, duration)
            - Patient eligibility criteria
            - Cell collection and CRISPR editing protocol
            - Conditioning regimen
            - Monitoring and follow-up schedule
            - Statistical analysis approach
            Be specific but concise. Reference the methodology source document."""
        },
        {
            "title": "Results",
            "guidance": """Present the key findings from the study:
            - Patient demographics and baseline characteristics
            - Primary endpoint: Fetal hemoglobin levels over time
            - Secondary endpoints: VOC frequency, transfusion requirements, quality of life
            - Safety results including adverse events
            - Biomarker changes
            Use specific numbers and statistics from the research findings document."""
        },
        {
            "title": "Discussion and Conclusions",
            "guidance": """Write a discussion section that:
            - Interprets the key findings in context of existing literature
            - Compares results to approved therapies (Casgevy, Lyfgenia)
            - Discusses limitations of the study
            - Addresses safety considerations and long-term follow-up needs
            - Outlines future directions and implications for the field
            - Provides clear conclusions about the therapy's potential"""
        },
    ]

    print("=" * 80)
    print("InformGen Agent - Document Generation Demo")
    print("=" * 80)
    print(f"\nGenerating a research report with {len(template)} sections...")
    print(f"Source documents will be auto-discovered from sandbox")
    print("\n" + "=" * 80 + "\n")

    # Generate the document
    # Note: source_documents is optional - agent will auto-discover files in sandbox
    result = agent.go(
        document_template=template,
        verbose=True
    )

    # Print results
    print("\n" + "=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)

    print(f"\nSections completed: {len(result.completed_sections)}")
    for section in result.completed_sections:
        print(f"  - {section['title']} ({section['iteration_count']} iterations)")

    print(f"\nToken usage:")
    print(f"  - Input tokens: {result.total_input_tokens:,}")
    print(f"  - Output tokens: {result.total_output_tokens:,}")

    print("\n" + "=" * 80)
    print("FINAL DOCUMENT")
    print("=" * 80 + "\n")
    print(result.final_document)

    # Optionally save to file
    output_path = os.path.join(current_dir, "test_artifacts", "informgen_report.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(result.final_document)
    print(f"\n\nDocument saved to: {output_path}")

    # Clean up sandbox
    agent.clear_workspace()


if __name__ == "__main__":
    main()
