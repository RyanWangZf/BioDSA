"""
Custom tools for the TrialGPT agent.
"""
# IMPORTANT: Apply nest_asyncio FIRST before any other imports
# This is required for Jupyter notebooks and LangGraph which run their own event loops
import nest_asyncio
nest_asyncio.apply()

import warnings
# Suppress the coroutine warning that can occur with nested event loops
# The code works correctly, but Python's GC may emit this warning during cleanup
warnings.filterwarnings("ignore", message="coroutine .* was never awaited", category=RuntimeWarning)

from typing import Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from biodsa.tools.clinical_trials import search_trials, fetch_trial_details_by_ids


class ClinicalTrialSearchInput(BaseModel):
    """Input schema for clinical trial search tool."""
    conditions: Optional[str] = Field(
        default=None,
        description="Condition/disease terms to search for (e.g., 'breast cancer', 'NSCLC'). Can be comma-separated for multiple conditions."
    )
    interventions: Optional[str] = Field(
        default=None,
        description="Intervention/treatment names to search for (e.g., 'pembrolizumab', 'chemotherapy'). Can be comma-separated."
    )
    terms: Optional[str] = Field(
        default=None,
        description="General search terms that don't fit specific categories. Can be comma-separated."
    )
    phase: Optional[str] = Field(
        default=None,
        description="Trial phase filter (EARLY_PHASE1, PHASE1, PHASE2, PHASE3, PHASE4)"
    )
    age_group: Optional[str] = Field(
        default=None,
        description="Age group filter (CHILD, ADULT, SENIOR, ALL)"
    )
    recruiting_status: Optional[str] = Field(
        default="OPEN",
        description="Recruitment status (OPEN for actively recruiting, CLOSED, ANY)"
    )
    required_mutations: Optional[str] = Field(
        default=None,
        description="Required mutations to search in eligibility criteria (e.g., 'EGFR', 'BRAF V600E'). Can be comma-separated."
    )
    prior_therapies: Optional[str] = Field(
        default=None,
        description="Prior therapies to search for in eligibility criteria. Can be comma-separated."
    )
    page_size: int = Field(
        default=50,
        description="Number of results to return (max 100)"
    )


class ClinicalTrialSearchTool(BaseTool):
    """Tool for searching clinical trials on ClinicalTrials.gov."""
    
    name: str = "clinical_trial_search"
    description: str = """Search for clinical trials on ClinicalTrials.gov based on conditions, interventions, and other criteria.
    
Use this tool to find clinical trials that may be relevant for a patient. You can search by:
- Disease/condition (e.g., 'breast cancer', 'non-small cell lung cancer')
- Intervention/treatment (e.g., 'pembrolizumab', 'immunotherapy')
- Genetic mutations (e.g., 'EGFR', 'BRAF V600E')
- Prior therapies
- Phase, age group, and recruitment status

Returns a list of matching trials with their NCT IDs, titles, conditions, interventions, and eligibility criteria.
"""
    args_schema: Type[BaseModel] = ClinicalTrialSearchInput
    
    def _run(
        self,
        conditions: Optional[str] = None,
        interventions: Optional[str] = None,
        terms: Optional[str] = None,
        phase: Optional[str] = None,
        age_group: Optional[str] = None,
        recruiting_status: str = "OPEN",
        required_mutations: Optional[str] = None,
        prior_therapies: Optional[str] = None,
        page_size: int = 50
    ) -> str:
        """Execute the clinical trial search."""
        try:
            # Call the search_trials function
            # nest_asyncio is applied at module import to handle Jupyter/LangGraph event loops
            df, output_str, total_count, next_page_token = search_trials(
                conditions=conditions,
                interventions=interventions,
                terms=terms,
                phase=phase,
                age_group=age_group,
                recruiting_status=recruiting_status,
                required_mutations=required_mutations,
                prior_therapies=prior_therapies,
                page_size=min(page_size, 100)
            )
            
            # Format the results for the agent
            if len(df) == 0:
                return f"No clinical trials found matching the search criteria.\n\nSearch parameters:\n- Conditions: {conditions}\n- Interventions: {interventions}\n- Terms: {terms}"
            
            # Build a detailed output
            result_parts = [
                f"# Clinical Trial Search Results",
                f"**Total trials found:** {total_count}",
                f"**Returned in this batch:** {len(df)}",
                "",
                "## Trial List:",
                ""
            ]
            
            for idx, row in df.iterrows():
                trial_info = [
                    f"### {idx + 1}. {row.get('NCT Number', 'N/A')}",
                    f"**Title:** {row.get('Study Title', 'N/A')}",
                    f"**Status:** {row.get('Study Status', 'N/A')}",
                    f"**Phase:** {row.get('Phases', 'N/A')}",
                    f"**Conditions:** {row.get('Conditions', 'N/A')}",
                    f"**Interventions:** {row.get('Interventions', 'N/A')}",
                    f"**URL:** {row.get('Study URL', 'N/A')}",
                    ""
                ]
                result_parts.extend(trial_info)
            
            if next_page_token:
                result_parts.append(f"\n*More results available. Next page token: {next_page_token}*")
            
            return "\n".join(result_parts)
            
        except Exception as e:
            return f"Error searching clinical trials: {str(e)}"


class TrialDetailsInput(BaseModel):
    """Input schema for fetching trial details."""
    trial_ids: str = Field(
        description="NCT IDs of trials to fetch details for. Can be comma-separated for multiple trials (e.g., 'NCT12345678,NCT87654321')."
    )


class TrialDetailsTool(BaseTool):
    """Tool for fetching detailed information about specific clinical trials."""
    
    name: str = "get_trial_details"
    description: str = """Fetch detailed information about specific clinical trials by their NCT IDs.
    
Use this tool when you need the complete eligibility criteria, detailed study description, 
or other comprehensive information about specific trials identified in the initial search.

Provide one or more NCT IDs (comma-separated) to get detailed information including:
- Complete eligibility criteria (inclusion/exclusion)
- Full study description and objectives
- Primary and secondary outcome measures
- Study design details
- Location information
"""
    args_schema: Type[BaseModel] = TrialDetailsInput
    
    def _run(self, trial_ids: str) -> str:
        """Fetch detailed trial information."""
        try:
            # Parse trial IDs
            ids_list = [tid.strip() for tid in trial_ids.split(",") if tid.strip()]
            
            if not ids_list:
                return "Error: No valid trial IDs provided."
            
            # Fetch trial details
            # nest_asyncio is applied at module import to handle Jupyter/LangGraph event loops
            df, output_str, total_count, _ = fetch_trial_details_by_ids(trial_ids=ids_list)
            
            if len(df) == 0:
                return f"No trials found for the provided IDs: {trial_ids}"
            
            # Build detailed output
            result_parts = [
                f"# Detailed Trial Information",
                f"**Trials retrieved:** {len(df)}",
                ""
            ]
            
            for idx, row in df.iterrows():
                trial_detail = [
                    f"## {row.get('NCT Number', 'N/A')}: {row.get('Study Title', 'N/A')}",
                    "",
                    f"**Status:** {row.get('Study Status', 'N/A')}",
                    f"**Phase:** {row.get('Phases', 'N/A')}",
                    f"**Study Type:** {row.get('Study Type', 'N/A')}",
                    f"**Enrollment:** {row.get('Enrollment', 'N/A')}",
                    "",
                    f"**Conditions:** {row.get('Conditions', 'N/A')}",
                    f"**Interventions:** {row.get('Interventions', 'N/A')}",
                    "",
                    "### Brief Summary:",
                    str(row.get('Brief Summary', 'N/A'))[:1000],
                    "",
                    "### Eligibility Criteria:",
                    str(row.get('Eligibility Criteria', 'N/A')),
                    "",
                    f"**Age:** {row.get('Age', 'N/A')}",
                    f"**Sex:** {row.get('Sex', 'N/A')}",
                    "",
                    f"**Locations:** {str(row.get('Locations', 'N/A'))[:500]}",
                    f"**URL:** {row.get('Study URL', 'N/A')}",
                    "",
                    "---",
                    ""
                ]
                result_parts.extend(trial_detail)
            
            return "\n".join(result_parts)
            
        except Exception as e:
            return f"Error fetching trial details: {str(e)}"


class PatientTrialMatchInput(BaseModel):
    """Input schema for patient-trial matching evaluation."""
    patient_summary: str = Field(
        description="Structured summary of patient information including demographics, diagnosis, biomarkers, and treatment history."
    )
    eligibility_criteria: str = Field(
        description="The eligibility criteria text from the clinical trial."
    )
    trial_id: str = Field(
        description="The NCT ID of the trial being evaluated."
    )


class PatientTrialMatchTool(BaseTool):
    """Tool for structured patient-trial eligibility matching."""
    
    name: str = "evaluate_eligibility"
    description: str = """Evaluate a patient's eligibility for a specific clinical trial.

This tool helps structure the eligibility assessment by comparing the patient's clinical profile 
against the trial's eligibility criteria. Use this after gathering trial details to perform 
a systematic evaluation.

Provide:
- Patient summary: Structured patient information
- Eligibility criteria: The trial's inclusion/exclusion criteria
- Trial ID: The NCT ID for reference

Returns a structured assessment of how well the patient matches the criteria.
"""
    args_schema: Type[BaseModel] = PatientTrialMatchInput
    
    def _run(
        self,
        patient_summary: str,
        eligibility_criteria: str,
        trial_id: str
    ) -> str:
        """Return a template for eligibility evaluation."""
        # This tool returns a structured template that guides the LLM's evaluation
        # The actual reasoning is done by the LLM using this structure
        
        template = f"""
# Eligibility Evaluation for {trial_id}

## Patient Summary:
{patient_summary}

## Trial Eligibility Criteria:
{eligibility_criteria}

## Evaluation Framework:

### Step 1: Inclusion Criteria Checklist
For each inclusion criterion, assess:
- [ ] Criterion 1: [MEETS/DOES NOT MEET/UNCLEAR]
- [ ] Criterion 2: [MEETS/DOES NOT MEET/UNCLEAR]
(Continue for all criteria...)

### Step 2: Exclusion Criteria Checklist  
For each exclusion criterion, assess:
- [ ] Criterion 1: [NOT VIOLATED/VIOLATED/UNCLEAR]
- [ ] Criterion 2: [NOT VIOLATED/VIOLATED/UNCLEAR]
(Continue for all criteria...)

### Step 3: Overall Assessment
- Inclusion criteria met: X/Y
- Exclusion criteria clear: X/Y
- Information gaps: (list any)

### Step 4: Eligibility Determination
- Score (0.0-1.0): 
- Recommendation: [ELIGIBLE/LIKELY_ELIGIBLE/UNCERTAIN/LIKELY_INELIGIBLE/INELIGIBLE]
- Key rationale:

Please complete this evaluation based on the patient and trial information provided.
"""
        return template


def get_trialgpt_tools() -> List[BaseTool]:
    """Get all tools for the TrialGPT agent."""
    return [
        ClinicalTrialSearchTool(),
        TrialDetailsTool(),
        PatientTrialMatchTool(),
    ]
