from typing import List, Optional, Dict, Any, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import pandas as pd
import re
import os

from biodsa.tools.clinical_trials.trials import (
    search_trials,
    fetch_trial_details_by_ids,
    RecruitingStatus,
    StudyType,
    SponsorType,
    TrialPhase,
    AgeGroup,
    PrimaryPurpose,
    InterventionType,
    SortOrder,
    DateField,
    LineOfTherapy,
)
from biodsa.sandbox.sandbox_interface import ExecutionSandboxWrapper
from biodsa.tool_wrappers.utils import run_python_repl
from biodsa.tool_wrappers.utils import clean_task_name_for_filename

__all__ = [
    "SearchTrialsTool",
    "FetchTrialDetailsTool",
    "SearchTrialsToolInput",
    "FetchTrialDetailsToolInput",
]


# =====================================================
# Tool 1: Search Clinical Trials
# =====================================================
class SearchTrialsToolInput(BaseModel):
    """Input schema for SearchTrialsTool."""
    task_name: str = Field(
        ...,
        description="A less than three word description of what is the search for",
    )
    max_pages: Optional[int] = Field(
        default=1,
        description="Maximum number of pages to search for"
    )

    conditions: Optional[List[str]] = Field(
        default=None,
        description="List of medical conditions or diseases to search for (e.g., ['breast cancer', 'diabetes'])"
    )
    terms: Optional[List[str]] = Field(
        default=None,
        description="General search terms or keywords"
    )
    interventions: Optional[List[str]] = Field(
        default=None,
        description="Intervention or drug names (e.g., ['pembrolizumab', 'chemotherapy'])"
    )
    recruiting_status: Optional[str] = Field(
        default=None,
        description="Recruitment status: 'OPEN', 'CLOSED', or 'ANY'"
    )
    study_type: Optional[str] = Field(
        default=None,
        description="Type of study: 'INTERVENTIONAL', 'OBSERVATIONAL', or 'EXPANDED_ACCESS'"
    )
    sponsor: Optional[str] = Field(
        default=None,
        description="Sponsor name of the trial"
    )
    sponsor_type: Optional[str] = Field(
        default=None,
        description="Sponsor type: 'INDUSTRY', 'FED', 'NETWORK', 'NIH', 'OTHER', 'OTHER_GOV', 'INDIV'"
    )
    nct_ids: Optional[List[str]] = Field(
        default=None,
        description="Specific NCT IDs to search for (e.g., ['NCT04567890'])"
    )
    lat: Optional[float] = Field(
        default=None,
        description="Latitude for location-based search"
    )
    long: Optional[float] = Field(
        default=None,
        description="Longitude for location-based search"
    )
    distance: Optional[float] = Field(
        default=None,
        description="Distance in miles from lat/long (default: 50 miles if location provided)"
    )
    min_date: Optional[str] = Field(
        default=None,
        description="Minimum date filter (YYYY-MM-DD)"
    )
    max_date: Optional[str] = Field(
        default=None,
        description="Maximum date filter (YYYY-MM-DD)"
    )
    date_field: Optional[str] = Field(
        default=None,
        description="Date field to filter: 'POSTED', 'UPDATE', 'START', 'PRIMARY_COMPLETION', 'COMPLETION'"
    )
    phase: Optional[str] = Field(
        default=None,
        description="Trial phase: 'EARLY_PHASE1', 'PHASE1', 'PHASE2', 'PHASE3', 'PHASE4', 'NOT_APPLICABLE'"
    )
    age_group: Optional[str] = Field(
        default=None,
        description="Age group: 'CHILD', 'ADULT', 'OLDER_ADULT'"
    )
    primary_purpose: Optional[str] = Field(
        default=None,
        description="Primary purpose: 'TREATMENT', 'PREVENTION', 'DIAGNOSTIC', 'SUPPORTIVE_CARE', etc."
    )
    intervention_type: Optional[str] = Field(
        default=None,
        description="Intervention type: 'DRUG', 'DEVICE', 'BIOLOGICAL', 'PROCEDURE', etc."
    )
    sort: Optional[str] = Field(
        default=None,
        description="Sort order: 'RELEVANCE', 'LAST_UPDATE', 'ENROLLMENT', 'START_DATE', etc."
    )
    prior_therapies: Optional[List[str]] = Field(
        default=None,
        description="Prior therapies to search in eligibility criteria"
    )
    progression_on: Optional[List[str]] = Field(
        default=None,
        description="Therapies the patient has progressed on"
    )
    required_mutations: Optional[List[str]] = Field(
        default=None,
        description="Required genetic mutations in eligibility criteria"
    )
    excluded_mutations: Optional[List[str]] = Field(
        default=None,
        description="Excluded genetic mutations in eligibility criteria"
    )
    biomarker_expression: Optional[Dict[str, str]] = Field(
        default=None,
        description="Biomarker expression requirements (e.g., {'PD-L1': '≥50%'})"
    )
    line_of_therapy: Optional[str] = Field(
        default=None,
        description="Line of therapy: '1L' (first-line), '2L' (second-line), '3L+' (third-line or later)"
    )
    allow_brain_mets: Optional[bool] = Field(
        default=None,
        description="Whether to include trials that accept brain metastases"
    )
    page_size: Optional[int] = Field(
        default=None,
        description="Number of results per page (1-1000)"
    )
    expand_synonyms: bool = Field(
        default=True,
        description="Expand condition searches with disease synonyms"
    )

class SearchTrialsTool(BaseTool):
    """
    Tool to search for clinical trials on ClinicalTrials.gov.

    This comprehensive search tool allows filtering by:
    - Medical conditions and diseases
    - Interventions and drugs
    - Trial phase, status, and type
    - Geographic location
    - Patient eligibility criteria (biomarkers, mutations, prior therapies)
    - Sponsor information
    - Dates and enrollment

    Returns detailed trial information including title, status, conditions, interventions,
    eligibility criteria, locations, and more.
    """

    name: str = "search_clinical_trials"
    description: str = (
        "Search for clinical trials on ClinicalTrials.gov with comprehensive filtering options. "
        "Filter by conditions (diseases), interventions (drugs), trial phase, recruitment status, "
        "location, patient eligibility (mutations, biomarkers, prior therapies), and more. "
        "Returns trial metadata including NCT ID, title, status, phase, conditions, interventions, "
        "eligibility criteria, study design, locations, and contact information. "
        "CRITICAL USE: When looking for clinical trial options for specific diseases, patient populations, "
        "or investigating trial designs and outcomes."
    )
    args_schema: Type[BaseModel] = SearchTrialsToolInput
    sandbox: ExecutionSandboxWrapper = None

    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox

    def _run(
        self,
        task_name: str,
        conditions: Optional[List[str]] = None,
        terms: Optional[List[str]] = None,
        interventions: Optional[List[str]] = None,
        recruiting_status: Optional[str] = None,
        study_type: Optional[str] = None,
        sponsor: Optional[str] = None,
        sponsor_type: Optional[str] = None,
        nct_ids: Optional[List[str]] = None,
        lat: Optional[float] = None,
        long: Optional[float] = None,
        distance: Optional[float] = None,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None,
        date_field: Optional[str] = None,
        phase: Optional[str] = None,
        age_group: Optional[str] = None,
        primary_purpose: Optional[str] = None,
        intervention_type: Optional[str] = None,
        sort: Optional[str] = None,
        prior_therapies: Optional[List[str]] = None,
        progression_on: Optional[List[str]] = None,
        required_mutations: Optional[List[str]] = None,
        excluded_mutations: Optional[List[str]] = None,
        biomarker_expression: Optional[Dict[str, str]] = None,
        line_of_therapy: Optional[str] = None,
        allow_brain_mets: Optional[bool] = None,
        page_size: Optional[int] = None,
        max_pages: Optional[int] = None,
        expand_synonyms: bool = True,
    ) -> str:
        """Execute the tool to search clinical trials."""

        task_name = clean_task_name_for_filename(task_name)

        if max_pages is None:
            max_pages = 1

        if self.sandbox is not None:
            workdir = self.sandbox.get_workdir()
        else:
            # local, get the current exefcution directory
            workdir = os.path.join(os.getcwd(), "workdir")
            # create the directory if it doesn't exist
            os.makedirs(workdir, exist_ok=True)
        tgt_filepath = os.path.join(workdir, f"{task_name}.csv")

        # Generate Python code template
        code_template = f"""
import pandas as pd
from biodsa.tools.clinical_trials.trials import search_trials

# Search for clinical trials
next_page_token = None
all_df = []
for page in range(1, {max_pages} + 1):
    df, md_str, total_count, next_page_token = search_trials(
        conditions={repr(conditions)},
        terms={repr(terms)},
        interventions={repr(interventions)},
        recruiting_status={repr(recruiting_status)},
        study_type={repr(study_type)},
        sponsor={repr(sponsor)},
        sponsor_type={repr(sponsor_type)},
        nct_ids={repr(nct_ids)},
        lat={lat},
        long={long},
        distance={distance},
        min_date={repr(min_date)},
        max_date={repr(max_date)},
        date_field={repr(date_field)},
        phase={repr(phase)},
        age_group={repr(age_group)},
        primary_purpose={repr(primary_purpose)},
        intervention_type={repr(intervention_type)},
        sort={repr(sort)},
        prior_therapies={repr(prior_therapies)},
        progression_on={repr(progression_on)},
        required_mutations={repr(required_mutations)},
        excluded_mutations={repr(excluded_mutations)},
        biomarker_expression={repr(biomarker_expression)},
        line_of_therapy={repr(line_of_therapy)},
        allow_brain_mets={allow_brain_mets},
        page_size={page_size},
        expand_synonyms={expand_synonyms},
        save_path={repr(tgt_filepath)},
        next_page_hash=next_page_token,
    )
    all_df.append(df)
    if next_page_token is None:
        break

if len(all_df) > 0:
    all_df = pd.concat(all_df)
    all_df.to_csv('{tgt_filepath}', index=False)
    print("The search results are saved at '{tgt_filepath}'")
    print(all_df.head().to_markdown())
else:
    print("No search results found. Please try again with different query.")
"""
        
        # Execute in sandbox if available
        if self.sandbox is not None:
            exit_code, output, artifacts, running_time, peak_memory = self.sandbox.execute(
                language="python",
                code=code_template
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += f"*Execution time: {running_time:.2f}s, Peak memory: {peak_memory:.2f}MB*"
            
            if exit_code != 0:
                result += f"\n\n⚠️ **Warning:** Code exited with non-zero status ({exit_code})"
            
            return result
        else:
            # Fallback: execute locally
            output = run_python_repl(code_template)
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            
            return result

# =====================================================
# Tool 2: Fetch Trial Details by IDs
# =====================================================
class FetchTrialDetailsToolInput(BaseModel):
    """Input schema for FetchTrialDetailsTool."""
    task_name: str = Field(
        ...,
        description="A less than three word description of what is the search for",
    )
    trial_ids: List[str] = Field(
        ...,
        description="List of NCT IDs to fetch detailed information for (e.g., ['NCT04567890', 'NCT03456789'])"
    )


class FetchTrialDetailsTool(BaseTool):
    """
    Tool to fetch detailed information for specific clinical trials by their NCT IDs.

    This tool retrieves comprehensive information about clinical trials including:
    - Study design and methodology
    - Detailed eligibility criteria
    - Outcome measures and endpoints
    - Contact and location information
    - Study results and publications (if available)

    Use this when you have specific NCT IDs and need complete trial details.
    """

    name: str = "fetch_trial_details"
    description: str = (
        "Fetch detailed information for specific clinical trials using their NCT IDs. "
        "Returns comprehensive trial data including full study design, detailed eligibility criteria, "
        "outcome measures, contacts, locations, arms/groups, and published results if available. "
        "CRITICAL USE: When you have identified relevant trials (by NCT ID) and need complete details "
        "for analysis, comparison, or extracting specific protocol information."
    )
    args_schema: Type[BaseModel] = FetchTrialDetailsToolInput
    sandbox: ExecutionSandboxWrapper = None

    def __init__(self, sandbox: ExecutionSandboxWrapper = None):
        super().__init__()
        self.sandbox = sandbox

    def _run(
        self,
        trial_ids: List[str],
        task_name: str,
    ) -> str:
        """Execute the tool to fetch trial details."""

        task_name = clean_task_name_for_filename(task_name)
        if self.sandbox is not None:
            workdir = self.sandbox.get_workdir()
        else:
            # local, get the current exefcution directory
            workdir = os.path.join(os.getcwd(), "workdir")
            # create the directory if it doesn't exist
            os.makedirs(workdir, exist_ok=True)
        tgt_filepath = os.path.join(workdir, f"{task_name}.csv")

        if not trial_ids or len(trial_ids) == 0:
            return "Error: No trial IDs provided. Please provide at least one NCT ID."

        # Generate Python code template
        code_template = f"""
from biodsa.tools.clinical_trials.trials import fetch_trial_details_by_ids

# Fetch trial details
df, md_str, total_count, next_page_token = fetch_trial_details_by_ids(
    trial_ids={repr(trial_ids)},
    save_path={repr(tgt_filepath)},
)

# Generate output
if df is None or len(df) == 0:
    print(f"No details found for the provided trial IDs: {{', '.join({repr(trial_ids)})}}")
else:
    print(md_str)
"""
        
        # Execute in sandbox if available
        if self.sandbox is not None:
            exit_code, output, artifacts, running_time, peak_memory = self.sandbox.execute(
                language="python",
                code=code_template
            )
            
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"
            result += f"*Execution time: {running_time:.2f}s, Peak memory: {peak_memory:.2f}MB*"
            
            if exit_code != 0:
                result += f"\n\n⚠️ **Warning:** Code exited with non-zero status ({exit_code})"
            
            return result
        else:
            # Fallback: execute locally
            output = run_python_repl(code_template)
            result = f"### Executed Code:\n```python\n{code_template}\n```\n\n"
            result += f"### Output:\n```\n{output}\n```\n\n"            
            return result