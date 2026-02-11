"""
Tools for the SLR-Meta agent: PubMed search, ClinicalTrials.gov search,
screening, data extraction, evidence synthesis, and meta-analysis.
"""
import nest_asyncio
nest_asyncio.apply()

import warnings
warnings.filterwarnings("ignore", message="coroutine .* was never awaited", category=RuntimeWarning)

from typing import Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

# Reuse PubMed tools from TrialMind-SLR
from biodsa.agents.trialmind_slr.tools import (
    PubMedSearchTool,
    FetchAbstractsTool,
    GenerateCriteriaTool,
    ScreenStudyTool,
    ExtractDataTool,
    SynthesizeEvidenceTool,
    GenerateSLRReportTool,
)

# ClinicalTrials.gov search
from biodsa.tools.clinical_trials import search_trials


# =============================================================================
# ClinicalTrials.gov search tool
# =============================================================================

class CTGovSearchInput(BaseModel):
    """Input schema for ClinicalTrials.gov search."""
    conditions: str = Field(
        default="",
        description="Condition terms, comma-separated (e.g. 'lymphoma, B-cell lymphoma')"
    )
    terms: str = Field(
        default="",
        description="General search terms, comma-separated"
    )
    interventions: str = Field(
        default="",
        description="Intervention names, comma-separated (e.g. 'CAR-T, pembrolizumab')"
    )
    phase: Optional[str] = Field(
        default=None,
        description="Trial phase: PHASE1, PHASE2, PHASE3, PHASE4, or leave empty for any"
    )
    recruiting_status: str = Field(
        default="ANY",
        description="OPEN, CLOSED, or ANY"
    )
    page_size: int = Field(
        default=50,
        description="Number of trials to return (1-1000)"
    )


class CTGovSearchTool(BaseTool):
    """Search ClinicalTrials.gov for clinical trials matching the research question."""

    name: str = "ctgov_search"
    description: str = """Search ClinicalTrials.gov for relevant clinical trials.

Use this tool to find registered trials that match the population, intervention,
and condition from your research question. You can filter by:
- conditions: disease/condition terms (e.g. "B-cell lymphoma", "melanoma")
- terms: general keywords
- interventions: treatment names (e.g. "CAR-T", "immunotherapy")
- phase: PHASE1, PHASE2, PHASE3, PHASE4 (optional)
- recruiting_status: OPEN, CLOSED, or ANY
- page_size: number of results (default 50)

Returns a list of trials with NCT ID, title, conditions, interventions, status, and URL.
"""
    args_schema: Type[BaseModel] = CTGovSearchInput

    def _run(
        self,
        conditions: str = "",
        terms: str = "",
        interventions: str = "",
        phase: Optional[str] = None,
        recruiting_status: str = "ANY",
        page_size: int = 50,
    ) -> str:
        """Execute ClinicalTrials.gov search."""
        try:
            cond_list = [c.strip() for c in conditions.split(",") if c.strip()] if conditions else None
            terms_list = [t.strip() for t in terms.split(",") if t.strip()] if terms else None
            int_list = [i.strip() for i in interventions.split(",") if i.strip()] if interventions else None

            output_df, output_str, total_count, next_page_token = search_trials(
                conditions=cond_list,
                terms=terms_list,
                interventions=int_list,
                phase=phase,
                recruiting_status=recruiting_status,
                page_size=min(page_size, 100),
                expand_synonyms=True,
            )
            return output_str
        except Exception as e:
            return f"Error searching ClinicalTrials.gov: {str(e)}"


# =============================================================================
# Meta-analysis tool (template for quantitative synthesis)
# =============================================================================

class MetaAnalysisInput(BaseModel):
    """Input for meta-analysis synthesis step."""
    extracted_data: str = Field(
        description="JSON or structured text of extracted study data (outcomes, effect sizes, sample sizes)"
    )
    target_outcomes: str = Field(
        default="primary_outcome,secondary_outcome,safety",
        description="Comma-separated outcomes to pool"
    )
    effect_measure: str = Field(
        default="OR",
        description="Effect measure: OR, RR, RD, MD, SMD, HR"
    )


class MetaAnalysisTool(BaseTool):
    """Tool to guide quantitative meta-analysis of extracted study data."""

    name: str = "meta_analysis"
    description: str = """Perform or guide quantitative meta-analysis across included studies.

Use when you have extracted outcome data (event counts, means/SDs, effect estimates)
from multiple studies and want to:
1. Assess whether studies are sufficiently homogeneous for pooling
2. Propose pooled effect estimates (e.g. pooled OR, RR, mean difference)
3. Describe heterogeneity (I², tau², Q test) when appropriate
4. Produce forest-plot style summary and narrative interpretation

Input: extracted_data (structured), target_outcomes, effect_measure (OR, RR, MD, SMD, HR).
Output: Template and guidance for completing the meta-analysis narrative and numbers.
"""
    args_schema: Type[BaseModel] = MetaAnalysisInput

    def _run(
        self,
        extracted_data: str,
        target_outcomes: str = "primary_outcome,secondary_outcome,safety",
        effect_measure: str = "OR",
    ) -> str:
        """Return meta-analysis framework and template."""
        outcomes = [o.strip() for o in target_outcomes.split(",")]
        template = f"""
# Meta-Analysis Framework

## Extracted Data Summary
{extracted_data[:3000]}{"..." if len(extracted_data) > 3000 else ""}

## Target Outcomes
{chr(10).join([f"- {o}" for o in outcomes])}

## Effect Measure
{effect_measure} (e.g. Odds Ratio, Risk Ratio, Mean Difference, Standardized Mean Difference, Hazard Ratio)

## Steps to Complete

1. **Eligibility for pooling**: Same outcome definition and comparable effect measure across studies.
2. **Pooled estimate**: Compute or describe pooled {effect_measure} with 95% CI (e.g. inverse-variance or Mantel-Haenszel for binary; generic inverse-variance for continuous).
3. **Heterogeneity**: Report I², tau², Q, p-value; interpret as low/moderate/high.
4. **Sensitivity analyses**: Mention if any study drives heterogeneity or if excluding one study changes conclusions.
5. **Summary**: One sentence per outcome with pooled estimate and heterogeneity.

## Output Format

For each outcome:
- **Outcome name**: [name]
- **Studies included**: [n]
- **Pooled {effect_measure}** (95% CI): [value]
- **Heterogeneity**: I² = [%], p = [value]
- **Interpretation**: [1–2 sentences]

Complete the meta-analysis using the extracted data above. If data are insufficient for formal pooling, provide a narrative synthesis with ranges and direction of effects.
"""
        return template


# =============================================================================
# Tool registries
# =============================================================================

def get_search_tools() -> List[BaseTool]:
    """Tools for dual-source literature search (PubMed + CT.gov)."""
    return [
        PubMedSearchTool(),
        FetchAbstractsTool(),
        CTGovSearchTool(),
    ]


def get_screening_tools() -> List[BaseTool]:
    """Tools for screening stage."""
    return [
        GenerateCriteriaTool(),
        ScreenStudyTool(),
        FetchAbstractsTool(),
    ]


def get_extraction_tools() -> List[BaseTool]:
    """Tools for data extraction."""
    return [
        ExtractDataTool(),
        FetchAbstractsTool(),
    ]


def get_synthesis_tools() -> List[BaseTool]:
    """Tools for evidence synthesis and meta-analysis."""
    return [
        SynthesizeEvidenceTool(),
        MetaAnalysisTool(),
        GenerateSLRReportTool(),
    ]


def get_all_slr_meta_tools() -> List[BaseTool]:
    """All tools for the SLR-Meta agent."""
    return (
        get_search_tools()
        + get_screening_tools()
        + get_extraction_tools()
        + get_synthesis_tools()
    )
