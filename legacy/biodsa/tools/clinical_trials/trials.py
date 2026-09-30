import json
import logging
import asyncio
from typing import Annotated
import pandas as pd
import httpx
import requests

from pydantic import BaseModel, Field, field_validator, model_validator
from enum import StrEnum

from .utils import ensure_list
from .utils import to_markdown as render_to_markdown
from .ctgov_parser import parse_ctgov_json_response

CLINICAL_TRIALS_BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

async def request_api(
    url: str, 
    request: dict = None, 
    method: str = "GET", 
    use_requests: bool = False
) -> tuple:
    """
    Minimal API request helper.
    
    Args:
        url: The URL to request
        request: Request parameters (query params for GET, body for POST)
        method: HTTP method (GET, POST, etc.)
        use_requests: If True, use requests library (sync), else use httpx (async)
        
    Returns:
        Tuple of (response_json, error)
    """
    try:
        if use_requests:
            # Synchronous request using requests library
            if method.upper() == "GET":
                response = requests.get(url, params=request, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=request, timeout=10)
            else:
                response = requests.request(method, url, json=request, timeout=10)
            response.raise_for_status()
            return response.json(), None
        else:
            # Asynchronous request using httpx
            async with httpx.AsyncClient() as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=request, timeout=10)
                elif method.upper() == "POST":
                    response = await client.post(url, json=request, timeout=10)
                else:
                    response = await client.request(method, url, json=request, timeout=10)
                response.raise_for_status()
                return response.json(), None
    except Exception as e:
        # Return error in the second position of the tuple
        error = type('Error', (), {'code': getattr(e, 'status_code', 500), 'message': str(e)})()
        return None, error

class SortOrder(StrEnum):
    RELEVANCE = "RELEVANCE"
    LAST_UPDATE = "LAST_UPDATE"
    ENROLLMENT = "ENROLLMENT"
    START_DATE = "START_DATE"
    COMPLETION_DATE = "COMPLETION_DATE"
    SUBMITTED_DATE = "SUBMITTED_DATE"


class TrialPhase(StrEnum):
    EARLY_PHASE1 = "EARLY_PHASE1"
    PHASE1 = "PHASE1"
    PHASE2 = "PHASE2"
    PHASE3 = "PHASE3"
    PHASE4 = "PHASE4"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RecruitingStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    ANY = "ANY"


class StudyType(StrEnum):
    INTERVENTIONAL = "INTERVENTIONAL"
    OBSERVATIONAL = "OBSERVATIONAL"
    EXPANDED_ACCESS = "EXPANDED_ACCESS"
    OTHER = "OTHER"


class InterventionType(StrEnum):
    DRUG = "DRUG"
    DEVICE = "DEVICE"
    BIOLOGICAL = "BIOLOGICAL"
    PROCEDURE = "PROCEDURE"
    RADIATION = "RADIATION"
    BEHAVIORAL = "BEHAVIORAL"
    GENETIC = "GENETIC"
    DIETARY = "DIETARY"
    DIAGNOSTIC_TEST = "DIAGNOSTIC_TEST"
    OTHER = "OTHER"

class DateField(StrEnum):
    LAST_UPDATE = "LAST_UPDATE"
    STUDY_START = "STUDY_START"
    PRIMARY_COMPLETION = "PRIMARY_COMPLETION"
    OUTCOME_POSTING = "OUTCOME_POSTING"
    COMPLETION = "COMPLETION"
    FIRST_POSTING = "FIRST_POSTING"
    SUBMITTED_DATE = "SUBMITTED_DATE"


class PrimaryPurpose(StrEnum):
    TREATMENT = "TREATMENT"
    PREVENTION = "PREVENTION"
    DIAGNOSTIC = "DIAGNOSTIC"
    SUPPORTIVE_CARE = "SUPPORTIVE_CARE"
    SCREENING = "SCREENING"
    HEALTH_SERVICES = "HEALTH_SERVICES"
    BASIC_SCIENCE = "BASIC_SCIENCE"
    DEVICE_FEASIBILITY = "DEVICE_FEASIBILITY"
    OTHER = "OTHER"


class AgeGroup(StrEnum):
    CHILD = "CHILD"
    ADULT = "ADULT"
    SENIOR = "SENIOR"
    ALL = "ALL"


class LineOfTherapy(StrEnum):
    FIRST_LINE = "1L"
    SECOND_LINE = "2L"
    THIRD_LINE_PLUS = "3L+"


CTGOV_SORT_MAPPING = {
    SortOrder.RELEVANCE: "@relevance",
    SortOrder.LAST_UPDATE: "LastUpdatePostDate:desc",
    SortOrder.ENROLLMENT: "EnrollmentCount:desc",
    SortOrder.START_DATE: "StudyStartDate:desc",
    SortOrder.COMPLETION_DATE: "PrimaryCompletionDate:desc",
    SortOrder.SUBMITTED_DATE: "StudyFirstSubmitDate:desc",
}

CTGOV_PHASE_MAPPING = {
    TrialPhase.EARLY_PHASE1: ("EARLY_PHASE1",),
    TrialPhase.PHASE1: ("PHASE1",),
    TrialPhase.PHASE2: ("PHASE2",),
    TrialPhase.PHASE3: ("PHASE3",),
    TrialPhase.PHASE4: ("PHASE4",),
    TrialPhase.NOT_APPLICABLE: ("NOT_APPLICABLE",),
}

OPEN_STATUSES = (
    "AVAILABLE",
    "ENROLLING_BY_INVITATION",
    "NOT_YET_RECRUITING",
    "RECRUITING",
)
CLOSED_STATUSES = (
    "ACTIVE_NOT_RECRUITING",
    "COMPLETED",
    "SUSPENDED",
    "TERMINATED",
    "WITHDRAWN",
)
CTGOV_RECRUITING_STATUS_MAPPING = {
    RecruitingStatus.OPEN: OPEN_STATUSES,
    RecruitingStatus.CLOSED: CLOSED_STATUSES,
    RecruitingStatus.ANY: None,
}

CTGOV_STUDY_TYPE_MAPPING = {
    StudyType.INTERVENTIONAL: ("Interventional",),
    StudyType.OBSERVATIONAL: ("Observational",),
    StudyType.EXPANDED_ACCESS: ("Expanded Access",),
    StudyType.OTHER: ("Other",),
}

CTGOV_INTERVENTION_TYPE_MAPPING = {
    InterventionType.DRUG: ("Drug",),
    InterventionType.DEVICE: ("Device",),
    InterventionType.BIOLOGICAL: ("Biological",),
    InterventionType.PROCEDURE: ("Procedure",),
    InterventionType.RADIATION: ("Radiation",),
    InterventionType.BEHAVIORAL: ("Behavioral",),
    InterventionType.GENETIC: ("Genetic",),
    InterventionType.DIETARY: ("Dietary",),
    InterventionType.DIAGNOSTIC_TEST: ("Diagnostic Test",),
    InterventionType.OTHER: ("Other",),
}

CTGOV_DATE_FIELD_MAPPING = {
    DateField.LAST_UPDATE: "LastUpdatePostDate",
    DateField.STUDY_START: "StartDate",
    DateField.PRIMARY_COMPLETION: "PrimaryCompletionDate",
    DateField.OUTCOME_POSTING: "ResultsFirstPostDate",
    DateField.COMPLETION: "CompletionDate",
    DateField.FIRST_POSTING: "StudyFirstPostDate",
    DateField.SUBMITTED_DATE: "StudyFirstSubmitDate",
}

CTGOV_PRIMARY_PURPOSE_MAPPING = {
    PrimaryPurpose.TREATMENT: ("Treatment",),
    PrimaryPurpose.PREVENTION: ("Prevention",),
    PrimaryPurpose.DIAGNOSTIC: ("Diagnostic",),
    PrimaryPurpose.SUPPORTIVE_CARE: ("Supportive Care",),
    PrimaryPurpose.SCREENING: ("Screening",),
    PrimaryPurpose.HEALTH_SERVICES: ("Health Services",),
    PrimaryPurpose.BASIC_SCIENCE: ("Basic Science",),
    PrimaryPurpose.DEVICE_FEASIBILITY: ("Device Feasibility",),
    PrimaryPurpose.OTHER: ("Other",),
}

CTGOV_AGE_GROUP_MAPPING = {
    AgeGroup.CHILD: ("Child",),
    AgeGroup.ADULT: ("Adult",),
    AgeGroup.SENIOR: ("Older Adult",),
    AgeGroup.ALL: None,
}

class SponsorType(StrEnum):
    INDUSTRY = "INDUSTRY"
    NIH = "NIH"
    FEDERAL = "FEDERAL"
    OTHER = "OTHER"

CTGOV_SPONSOR_TYPE_MAPPING = {
    SponsorType.INDUSTRY: ("INDUSTRY",),
    SponsorType.NIH: ("NIH",),
    SponsorType.FEDERAL: ("FED",),
    SponsorType.OTHER: ("OTHER","OTHER_GOV","INDIV","NETWORK","AMBIG","UNKNOWN",),
}

# Line of therapy patterns for EligibilityCriteria search
LINE_OF_THERAPY_PATTERNS = {
    LineOfTherapy.FIRST_LINE: [
        '"first line"',
        '"first-line"',
        '"1st line"',
        '"frontline"',
        '"treatment naive"',
        '"previously untreated"',
    ],
    LineOfTherapy.SECOND_LINE: [
        '"second line"',
        '"second-line"',
        '"2nd line"',
        '"one prior line"',
        '"1 prior line"',
    ],
    LineOfTherapy.THIRD_LINE_PLUS: [
        '"third line"',
        '"third-line"',
        '"3rd line"',
        '"≥2 prior"',
        '"at least 2 prior"',
        '"heavily pretreated"',
    ],
}

DEFAULT_FORMAT = "json"
DEFAULT_MARKUP = "markdown"

# default fields to be parsed and returned to save time
DEFAULT_RETURN_FIELDS = [
    "NCT Number",
    "Study Title",
    "Study URL",
    "Study Status",
    "Brief Summary",
    "Study Results",
    "Conditions",
    "Interventions",
    "Phases",
    "Enrollment",
    "Study Type",
    "Study Design",
    "Start Date",
    "Completion Date",
]


class TrialQuery(BaseModel):
    """Parameters for querying clinical trial data from ClinicalTrials.gov."""

    conditions: list[str] | None = Field(
        default=None,
        description="List of condition terms.",
    )
    terms: list[str] | None = Field(
        default=None,
        description="General search terms that don't fit specific categories.",
    )
    interventions: list[str] | None = Field(
        default=None,
        description="Intervention names.",
    )
    recruiting_status: RecruitingStatus | None = Field(
        default=None,
        description="Study recruitment status. Use 'OPEN' for actively recruiting trials, 'CLOSED' for completed/terminated trials, or 'ANY' for all trials. Common aliases like 'recruiting', 'active', 'enrolling' map to 'OPEN'.",
    )
    study_type: StudyType | None = Field(
        default=None,
        description="Type of study.",
    )
    nct_ids: list[str] | None = Field(
        default=None,
        description="Clinical trial NCT IDs",
    )
    sponsor: str | None = Field(
        default=None,
        description="Sponsor of the trial",
    )
    sponsor_type: SponsorType | None = Field(
        default=None,
        description="Sponsor type of the trial",
    )
    lat: float | None = Field(
        default=None,
        description="Latitude for location search. AI agents should geocode city/location names (e.g., 'Cleveland' → 41.4993, -81.6944) before using this parameter.",
    )
    long: float | None = Field(
        default=None,
        description="Longitude for location search. AI agents should geocode city/location names (e.g., 'Cleveland' → 41.4993, -81.6944) before using this parameter.",
    )
    distance: int | None = Field(
        default=None,
        description="Distance from lat/long in miles (default: 50 miles if lat/long provided but distance not specified)",
    )
    min_date: str | None = Field(
        default=None,
        description="Minimum date for filtering",
    )
    max_date: str | None = Field(
        default=None,
        description="Maximum date for filtering",
    )
    date_field: DateField | None = Field(
        default=None,
        description="Date field to filter on",
    )
    phase: TrialPhase | None = Field(
        default=None,
        description="Trial phase filter",
    )
    age_group: AgeGroup | None = Field(
        default=None,
        description="Age group filter",
    )
    primary_purpose: PrimaryPurpose | None = Field(
        default=None,
        description="Primary purpose of the trial",
    )
    intervention_type: InterventionType | None = Field(
        default=None,
        description="Type of intervention",
    )

    sort: SortOrder | None = Field(
        default=None,
        description="Sort order for results",
    )
    next_page_hash: str | None = Field(
        default=None,
        description="Token to retrieve the next page of results",
    )
    # New eligibility-focused fields
    prior_therapies: list[str] | None = Field(
        default=None,
        description="Prior therapies to search for in eligibility criteria",
    )
    progression_on: list[str] | None = Field(
        default=None,
        description="Therapies the patient has progressed on",
    )
    required_mutations: list[str] | None = Field(
        default=None,
        description="Required mutations in eligibility criteria",
    )
    excluded_mutations: list[str] | None = Field(
        default=None,
        description="Excluded mutations in eligibility criteria",
    )
    biomarker_expression: dict[str, str] | None = Field(
        default=None,
        description="Biomarker expression requirements (e.g., {'PD-L1': '≥50%'})",
    )
    line_of_therapy: LineOfTherapy | None = Field(
        default=None,
        description="Line of therapy filter",
    )
    allow_brain_mets: bool | None = Field(
        default=None,
        description="Whether to allow trials that accept brain metastases",
    )
    page_size: int | None = Field(
        default=None,
        description="Number of results per page",
        ge=1,
        le=1000,
    )
    expand_synonyms: bool = Field(
        default=True,
        description="Expand condition searches with disease synonyms from MyDisease.info",
    )

    @field_validator("recruiting_status", mode="before")
    @classmethod
    def normalize_recruiting_status(cls, v):
        """Normalize common recruiting status aliases to enum values."""
        if isinstance(v, str):
            v_lower = v.lower()
            # Map common aliases
            alias_map = {
                "recruiting": "OPEN",
                "active": "OPEN",
                "enrolling": "OPEN",
                "closed": "CLOSED",
                "completed": "CLOSED",
                "terminated": "CLOSED",
            }
            return alias_map.get(v_lower, v)
        return v

    # Field validators for list fields
    @model_validator(mode="before")
    def convert_list_fields(cls, data):
        """Convert string values to lists for list fields."""
        if isinstance(data, dict):
            for field_name in [
                "conditions",
                "terms",
                "interventions",
                "nct_ids",
                "prior_therapies",
                "progression_on",
                "required_mutations",
                "excluded_mutations",
            ]:
                if field_name in data and data[field_name] is not None:
                    data[field_name] = ensure_list(
                        data[field_name], split_strings=True
                    )
        return data


def _inject_ids(
    params: dict[str, list[str]], ids: list[str], has_other_filters: bool
) -> None:
    """Inject NCT IDs into params using intersection or id-only semantics.

    Args:
        params: The parameter dictionary to modify
        ids: List of NCT IDs to inject
        has_other_filters: Whether other filters are present
    """
    ids_csv = ",".join(ids)
    if has_other_filters:  # intersection path
        params["filter.ids"] = [ids_csv]
    elif len(ids_csv) < 1800:  # pure-ID & small
        params["query.id"] = [ids_csv]
    else:  # pure-ID & large
        params["filter.ids"] = [ids_csv]


def _build_prior_therapy_essie(therapies: list[str]) -> list[str]:
    """Build Essie fragments for prior therapy search."""
    fragments = []
    for therapy in therapies:
        if therapy.strip():  # Skip empty strings
            fragment = f'AREA[EligibilityCriteria]("{therapy}" AND (prior OR previous OR received))'
            fragments.append(fragment)
    return fragments


def _build_progression_essie(therapies: list[str]) -> list[str]:
    """Build Essie fragments for progression on therapy search."""
    fragments = []
    for therapy in therapies:
        if therapy.strip():  # Skip empty strings
            fragment = f'AREA[EligibilityCriteria]("{therapy}" AND (progression OR resistant OR refractory))'
            fragments.append(fragment)
    return fragments


def _build_required_mutations_essie(mutations: list[str]) -> list[str]:
    """Build Essie fragments for required mutations."""
    fragments = []
    for mutation in mutations:
        if mutation.strip():  # Skip empty strings
            fragment = f'AREA[EligibilityCriteria]("{mutation}")'
            fragments.append(fragment)
    return fragments


def _build_excluded_mutations_essie(mutations: list[str]) -> list[str]:
    """Build Essie fragments for excluded mutations."""
    fragments = []
    for mutation in mutations:
        if mutation.strip():  # Skip empty strings
            fragment = f'AREA[EligibilityCriteria](NOT "{mutation}")'
            fragments.append(fragment)
    return fragments


def _build_biomarker_expression_essie(biomarkers: dict[str, str]) -> list[str]:
    """Build Essie fragments for biomarker expression requirements."""
    fragments = []
    for marker, expression in biomarkers.items():
        if marker.strip() and expression.strip():  # Skip empty values
            fragment = (
                f'AREA[EligibilityCriteria]("{marker}" AND "{expression}")'
            )
            fragments.append(fragment)
    return fragments


def _build_line_of_therapy_essie(line: LineOfTherapy) -> str:
    """Build Essie fragment for line of therapy."""
    patterns = LINE_OF_THERAPY_PATTERNS.get(line, [])
    if patterns:
        # Join all patterns with OR within a single AREA block
        pattern_str = " OR ".join(patterns)
        return f"AREA[EligibilityCriteria]({pattern_str})"
    return ""


def _build_brain_mets_essie(allow: bool) -> str:
    """Build Essie fragment for brain metastases filter."""
    if allow is False:
        return 'AREA[EligibilityCriteria](NOT "brain metastases")'
    return ""


async def convert_query(query: TrialQuery) -> dict[str, list[str]]:  # noqa: C901
    """Convert a TrialQuery object into a dict of query params
    for the ClinicalTrials.gov API (v2). Each key maps to one or
    more strings in a list, consistent with parse_qs outputs.
    """
    # Start with required fields
    params: dict[str, list[str]] = {
        "format": [DEFAULT_FORMAT],
        "markupFormat": [DEFAULT_MARKUP],
        "countTotal": ["true"],
    }

    # Track whether we have other filters (for NCT ID intersection logic)
    has_other_filters = False

    # Handle conditions with optional synonym expansion
    if query.conditions:
        has_other_filters = True
        expanded_conditions = []

        if query.expand_synonyms:
            # TODO: Implement synonym expansion later using biothings client
            # Expand each condition with synonyms
            # client = BioThingsClient()
            # for condition in query.conditions:
            #     try:
            #         synonyms = await client.get_disease_synonyms(condition)
            #         expanded_conditions.extend(synonyms)
            #     except Exception as e:
            #         logging.warning(
            #             f"Failed to get synonyms for {condition}: {e}"
            #         )
            #         expanded_conditions.append(condition)
            expanded_conditions = query.conditions
        else:
            expanded_conditions = query.conditions

        # Remove duplicates while preserving order
        seen = set()
        unique_conditions = []
        for cond in expanded_conditions:
            if cond.lower() not in seen:
                seen.add(cond.lower())
                unique_conditions.append(cond)

        if len(unique_conditions) == 1:
            params["query.cond"] = [unique_conditions[0]]
        else:
            # Join multiple terms with OR, wrapped in parentheses
            params["query.cond"] = [f"({' OR '.join(unique_conditions)})"]

    # Handle terms and interventions (no synonym expansion)
    for key, val in [
        ("query.term", query.terms),
        ("query.intr", query.interventions),
    ]:
        if val:
            has_other_filters = True
            if len(val) == 1:
                params[key] = [val[0]]
            else:
                # Join multiple terms with OR, wrapped in parentheses
                params[key] = [f"({' OR '.join(val)})"]

    # Collect Essie fragments for eligibility criteria
    essie_fragments: list[str] = []

    # Prior therapies
    if query.prior_therapies:
        has_other_filters = True
        essie_fragments.extend(
            _build_prior_therapy_essie(query.prior_therapies)
        )

    # Progression on therapies
    if query.progression_on:
        has_other_filters = True
        essie_fragments.extend(_build_progression_essie(query.progression_on))

    # Required mutations
    if query.required_mutations:
        has_other_filters = True
        essie_fragments.extend(
            _build_required_mutations_essie(query.required_mutations)
        )

    # Excluded mutations
    if query.excluded_mutations:
        has_other_filters = True
        essie_fragments.extend(
            _build_excluded_mutations_essie(query.excluded_mutations)
        )

    # Biomarker expression
    if query.biomarker_expression:
        has_other_filters = True
        essie_fragments.extend(
            _build_biomarker_expression_essie(query.biomarker_expression)
        )

    # Line of therapy
    if query.line_of_therapy:
        has_other_filters = True
        line_fragment = _build_line_of_therapy_essie(query.line_of_therapy)
        if line_fragment:
            essie_fragments.append(line_fragment)

    # Brain metastases filter
    if query.allow_brain_mets is not None:
        has_other_filters = True
        brain_fragment = _build_brain_mets_essie(query.allow_brain_mets)
        if brain_fragment:
            essie_fragments.append(brain_fragment)

    # Combine all Essie fragments with AND and append to query.term
    if essie_fragments:
        combined_essie = " AND ".join(essie_fragments)
        if "query.term" in params:
            # Append to existing terms with AND
            params["query.term"][0] = (
                f"{params['query.term'][0]} AND {combined_essie}"
            )
        else:
            params["query.term"] = [combined_essie]

    # Geospatial
    if query.lat is not None and query.long is not None:
        has_other_filters = True
        geo_val = f"distance({query.lat},{query.long},{query.distance}mi)"
        params["filter.geo"] = [geo_val]

    # Collect advanced filters in a list
    advanced_filters: list[str] = []

    # Date filter
    if query.date_field and (query.min_date or query.max_date):
        has_other_filters = True
        date_field = CTGOV_DATE_FIELD_MAPPING[query.date_field]
        min_val = query.min_date or "MIN"
        max_val = query.max_date or "MAX"
        advanced_filters.append(
            f"AREA[{date_field}]RANGE[{min_val},{max_val}]",
        )

    # Sponsor filter
    if query.sponsor:
        has_other_filters = True
        advanced_filters.append(f"AREA[OrgFullName]{query.sponsor}")

    # Prepare a map of "AREA[...] -> (query_value, mapping_dict)"
    advanced_map = {
        "DesignPrimaryPurpose": (
            query.primary_purpose,
            CTGOV_PRIMARY_PURPOSE_MAPPING,
        ),
        "StudyType": (query.study_type, CTGOV_STUDY_TYPE_MAPPING),
        "InterventionType": (
            query.intervention_type,
            CTGOV_INTERVENTION_TYPE_MAPPING,
        ),
        "Phase": (query.phase, CTGOV_PHASE_MAPPING),
        "LeadSponsorClass": (query.sponsor_type, CTGOV_SPONSOR_TYPE_MAPPING),
    }

    # Append advanced filters
    for area, (qval, mapping) in advanced_map.items():
        if qval:
            has_other_filters = True
            # Check if mapping is a dict before using get method
            mapped = (
                mapping.get(qval)
                if mapping and isinstance(mapping, dict)
                else None
            )
            # Use the first mapped value if available, otherwise the literal
            value = mapped[0] if mapped else qval
            advanced_filters.append(f"AREA[{area}]{value}")

    # Age group
    if query.age_group and query.age_group != "ALL":
        has_other_filters = True
        mapped = CTGOV_AGE_GROUP_MAPPING[query.age_group]
        if mapped:
            advanced_filters.append(f"AREA[StdAge]{mapped[0]}")
        else:
            advanced_filters.append(f"AREA[StdAge]{query.age_group}")

    # If we collected any advanced filters, join them with AND
    if advanced_filters:
        params["filter.advanced"] = [" AND ".join(advanced_filters)]

    # NCT IDs - now using intersection semantics
    # Must be done BEFORE recruiting status to properly detect user-set filters
    if query.nct_ids:
        _inject_ids(params, query.nct_ids, has_other_filters)

    # Recruiting status - apply AFTER NCT ID injection
    # Only count as a user filter if explicitly set to something other than default
    if query.recruiting_status not in (None, RecruitingStatus.OPEN):
        # User explicitly set a non-default status
        if query.recruiting_status is not None:  # Type guard for mypy
            statuses = CTGOV_RECRUITING_STATUS_MAPPING.get(
                query.recruiting_status
            )
            if statuses:
                params["filter.overallStatus"] = [",".join(statuses)]
    elif not query.nct_ids or has_other_filters:
        # Apply default OPEN status only if:
        # 1. No NCT IDs provided, OR
        # 2. NCT IDs provided with other filters (intersection mode)
        params["filter.overallStatus"] = [",".join(OPEN_STATUSES)]

    # Sort & paging
    if query.sort is None:
        sort_val = CTGOV_SORT_MAPPING[SortOrder.RELEVANCE]
    else:
        sort_val = CTGOV_SORT_MAPPING.get(query.sort, query.sort)

    params["sort"] = [sort_val]
    if query.next_page_hash:
        params["pageToken"] = [query.next_page_hash]

    # Set page size
    if query.page_size:
        params["pageSize"] = [str(query.page_size)]
    else:
        params["pageSize"] = ["100"]

    return params


async def search_ctgov(
    query: TrialQuery,
) -> str:
    """Search ClinicalTrials.gov for clinical trials."""
    params = await convert_query(query)

    # Log filter mode if NCT IDs are present
    if query.nct_ids:
        # Check if we're using intersection or id-only mode
        # Only count explicit user-set filters, not defaults
        has_other_filters = any([
            query.conditions,
            query.terms,
            query.interventions,
            query.lat is not None and query.long is not None,
            query.date_field and (query.min_date or query.max_date),
            query.primary_purpose,
            query.study_type,
            query.intervention_type,
            query.phase,
            query.age_group and query.age_group != AgeGroup.ALL,
            query.recruiting_status not in (None, RecruitingStatus.OPEN),
            query.prior_therapies,
            query.progression_on,
            query.required_mutations,
            query.excluded_mutations,
            query.biomarker_expression,
            query.line_of_therapy,
            query.allow_brain_mets is not None,
        ])

        if has_other_filters:
            logging.debug(
                "Filter mode: intersection (NCT IDs AND other filters)"
            )
        else:
            logging.debug("Filter mode: id-only (NCT IDs only)")


    response, error = await request_api(
        url=CLINICAL_TRIALS_BASE_URL,
        request=params,
        method="GET",
        use_requests=True,
    )

    data = response

    # paarse the response to get the target fields
    data, total_count, next_page_token = parse_ctgov_json_response(response)
    if error:
        data = {"error": f"Error {error.code}: {error.message}"}

    return data, total_count, next_page_token


# ================================================
# Unified search APIs
# ================================================

def search_trials(
    conditions: Annotated[
        list[str] | str | None,
        "Condition terms (e.g., 'breast cancer') - list or comma-separated string",
    ] = None,
    terms: Annotated[
        list[str] | str | None,
        "General search terms - list or comma-separated string",
    ] = None,
    interventions: Annotated[
        list[str] | str | None,
        "Intervention names (e.g., 'pembrolizumab') - list or comma-separated string",
    ] = None,
    recruiting_status: Annotated[
        RecruitingStatus | str | None,
        "Study recruitment status (OPEN, CLOSED, ANY)",
    ] = None,
    study_type: Annotated[StudyType | str | None, "Type of study"] = None,
    sponsor: Annotated[str | None, "Sponsor of the trial"] = None,
    sponsor_type: Annotated[SponsorType | None, "Sponsor type of the trial"] = None,
    nct_ids: Annotated[
        list[str] | str | None,
        "Clinical trial NCT IDs - list or comma-separated string",
    ] = None,
    lat: Annotated[
        float | None,
        "Latitude for location search. AI agents should geocode city/location names (e.g., 'Cleveland' → 41.4993, -81.6944) before using this parameter.",
    ] = None,
    long: Annotated[
        float | None,
        "Longitude for location search. AI agents should geocode city/location names (e.g., 'Cleveland' → 41.4993, -81.6944) before using this parameter.",
    ] = None,
    distance: Annotated[
        float | None,
        "Distance from lat/long in miles (default: 50 miles if lat/long provided but distance not specified)",
    ] = None,
    min_date: Annotated[
        str | None, "Minimum date for filtering (YYYY-MM-DD)"
    ] = None,
    max_date: Annotated[
        str | None, "Maximum date for filtering (YYYY-MM-DD)"
    ] = None,
    date_field: Annotated[
        DateField | str | None, "Date field to filter on"
    ] = None,
    phase: Annotated[TrialPhase | str | None, "Trial phase filter"] = None,
    age_group: Annotated[AgeGroup | str | None, "Age group filter"] = None,
    primary_purpose: Annotated[
        PrimaryPurpose | str | None, "Primary purpose of the trial"
    ] = None,
    intervention_type: Annotated[
        InterventionType | str | None, "Type of intervention"
    ] = None,
    sort: Annotated[SortOrder | str | None, "Sort order for results"] = None,
    next_page_hash: Annotated[
        str | None, "Token to retrieve the next page of results"
    ] = None,
    prior_therapies: Annotated[
        list[str] | str | None,
        "Prior therapies to search for in eligibility criteria - list or comma-separated string",
    ] = None,
    progression_on: Annotated[
        list[str] | str | None,
        "Therapies the patient has progressed on - list or comma-separated string",
    ] = None,
    required_mutations: Annotated[
        list[str] | str | None,
        "Required mutations in eligibility criteria - list or comma-separated string",
    ] = None,
    excluded_mutations: Annotated[
        list[str] | str | None,
        "Excluded mutations in eligibility criteria - list or comma-separated string",
    ] = None,
    biomarker_expression: Annotated[
        dict[str, str] | None,
        "Biomarker expression requirements (e.g., {'PD-L1': '≥50%'})",
    ] = None,
    line_of_therapy: Annotated[
        LineOfTherapy | str | None,
        "Line of therapy filter (1L, 2L, 3L+)",
    ] = None,
    allow_brain_mets: Annotated[
        bool | None,
        "Whether to allow trials that accept brain metastases",
    ] = None,
    page_size: Annotated[
        int | None,
        "Number of results per page (1-1000)",
    ] = None,
    expand_synonyms: Annotated[
        bool,
        "Expand condition searches with disease synonyms from MyDisease.info",
    ] = True,
    save_path: Annotated[
        str | None,
        "Path to save the results",
    ] = None,
) -> tuple[pd.DataFrame, str, int, str]:
    """
    Searches for clinical trials based on specified criteria.

    Parameters:
    - conditions: Condition terms (e.g., "breast cancer") - list or comma-separated string
    - terms: General search terms - list or comma-separated string
    - interventions: Intervention names (e.g., "pembrolizumab") - list or comma-separated string
    - recruiting_status: Study recruitment status (OPEN, CLOSED, ANY)
    - study_type: Type of study
    - nct_ids: Clinical trial NCT IDs - list or comma-separated string
    - sponsor: Sponsor of the trial
    - sponsor_type: Sponsor type of the trial
    - lat: Latitude for location search
    - long: Longitude for location search
    - distance: Distance from lat/long in miles
    - min_date: Minimum date for filtering (YYYY-MM-DD)
    - max_date: Maximum date for filtering (YYYY-MM-DD)
    - date_field: Date field to filter on
    - phase: Trial phase filter
    - age_group: Age group filter
    - primary_purpose: Primary purpose of the trial
    - intervention_type: Type of intervention
    - sort: Sort order for results
    - next_page_hash: Token to retrieve the next page of results
    - prior_therapies: Prior therapies to search for in eligibility criteria - list or comma-separated string
    - progression_on: Therapies the patient has progressed on - list or comma-separated string
    - required_mutations: Required mutations in eligibility criteria - list or comma-separated string
    - excluded_mutations: Excluded mutations in eligibility criteria - list or comma-separated string
    - biomarker_expression: Biomarker expression requirements (e.g., {'PD-L1': '≥50%'})
    - line_of_therapy: Line of therapy filter (1L, 2L, 3L+)
    - allow_brain_mets: Whether to allow trials that accept brain metastases
    - page_size: Number of results per page (1-1000)
    - expand_synonyms: Expand condition searches with disease synonyms from MyDisease.info
    - save_path: Path to save the results

    Returns:
    - output_df: DataFrame of clinical trials
    - output_str: Markdown formatted list of clinical trials search results
    - total_count: Total number of trials found
    - next_page_token: Token to retrieve the next page of results
    """
    # Convert individual parameters to a TrialQuery object
    ctgov_request_body = TrialQuery(
        conditions=ensure_list(conditions, split_strings=True),
        terms=ensure_list(terms, split_strings=True),
        interventions=ensure_list(interventions, split_strings=True),
        recruiting_status=recruiting_status,
        study_type=study_type,
        sponsor=sponsor,
        nct_ids=ensure_list(nct_ids, split_strings=True),
        sponsor_type=sponsor_type,
        lat=lat,
        long=long,
        distance=distance,
        min_date=min_date,
        max_date=max_date,
        date_field=date_field,
        phase=phase,
        age_group=age_group,
        primary_purpose=primary_purpose,
        intervention_type=intervention_type,
        sort=sort,
        next_page_hash=next_page_hash,
        prior_therapies=ensure_list(prior_therapies, split_strings=True),
        progression_on=ensure_list(progression_on, split_strings=True),
        required_mutations=ensure_list(required_mutations, split_strings=True),
        excluded_mutations=ensure_list(excluded_mutations, split_strings=True),
        biomarker_expression=biomarker_expression,
        line_of_therapy=line_of_therapy,
        allow_brain_mets=allow_brain_mets,
        page_size=page_size,
        expand_synonyms=expand_synonyms,
    )
    ctgov_data, total_count, next_page_token = asyncio.run(search_ctgov(ctgov_request_body))
    
    # build the output string
    all_available_fields = ctgov_data.columns.tolist()
    ctgov_data_brief = []
    keys_to_include = ["NCT Number","Conditions","Interventions","Study Title", "Study URL", "Study Status","Start Date","Completion Date" ,"Study Results"]
    ctgov_data_brief = ctgov_data[keys_to_include]
    output_str = render_to_markdown(ctgov_data_brief.to_dict(orient="records"))
    start_str = f"# Results summary:\nTotal {total_count} trials found. The next page token is `{next_page_token}`"
    output_str = f"{start_str}\n\n# Brief overview:\n\n{output_str}"
    output_df = pd.DataFrame(ctgov_data)

    if save_path is not None:
        try:
            if not save_path.endswith(".csv"):
                save_path = save_path + ".csv"
            if len(ctgov_data) > 0:
                output_df.to_csv(save_path, index=False)
                save_result_str = f"Results saved to {save_path}"
                save_result_str = f"{save_result_str}\nAll the available fields in the dataframe are: {all_available_fields}"
            else:
                save_result_str = f"No results found"
        except Exception as e:
            logging.error(f"Error saving results to {save_path}: {e}")
            save_result_str = f"Error saving results to {save_path}: {e}"
        output_str = f"{output_str}\n-----\n{save_result_str}"

    return output_df, output_str, total_count, next_page_token


def fetch_trial_details_by_ids(
    trial_ids: list[str],
    save_path: str = None,
) -> tuple[pd.DataFrame, str, int, str]:
    """
    Fetch trial details by their IDs from ClinicalTrials.gov.

    Args:
        - trial_ids: List of trial IDs to fetch details from
        - save_path: Path to save the results

    Returns:
        - output_df: DataFrame of clinical trials
        - output_str: Markdown formatted list of clinical trials search results
        - total_count: Total number of trials found
        - next_page_token: Token to retrieve the next page of results
    """
    ctgov_request_body = TrialQuery(
        nct_ids=trial_ids,
    )
    ctgov_data, total_count, next_page_token = asyncio.run(search_ctgov(ctgov_request_body))
    all_available_fields = ctgov_data.columns.tolist()

    output_str = render_to_markdown(ctgov_data.to_dict(orient="records"))
    start_str = f"# Results summary:\nTotal {total_count} trials found."
    output_str = f"{start_str}\n\n# Brief overview:\n\n{output_str}"
    output_df = pd.DataFrame(ctgov_data)
    if save_path is not None:
        try:
            if not save_path.endswith(".csv"):
                save_path = save_path + ".csv"
            if len(ctgov_data) > 0:
                output_df.to_csv(save_path, index=False)
                save_result_str = f"Results saved to {save_path}"
                save_result_str = f"{save_result_str}\nAll the available fields in the dataframe are: {all_available_fields}"
            else:
                save_result_str = f"No results found"
        except Exception as e:
            logging.error(f"Error saving results to {save_path}: {e}")
            save_result_str = f"Error saving results to {save_path}: {e}"
        output_str = f"{output_str}\n-----\n{save_result_str}"

    return output_df, output_str, total_count, next_page_token