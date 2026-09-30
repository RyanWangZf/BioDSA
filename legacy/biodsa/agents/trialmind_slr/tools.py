"""
Custom tools for the TrialMind-SLR agent.

Tools for systematic literature review including:
- PubMed search
- Eligibility screening
- Data extraction
- Evidence synthesis
"""
# IMPORTANT: Apply nest_asyncio FIRST before any other imports
# This is required for Jupyter notebooks and LangGraph which run their own event loops
import nest_asyncio
nest_asyncio.apply()

import warnings
warnings.filterwarnings("ignore", message="coroutine .* was never awaited", category=RuntimeWarning)

import re
import json
from typing import Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

try:
    from Bio import Entrez
    BIOPYTHON_AVAILABLE = True
except ImportError:
    BIOPYTHON_AVAILABLE = False
    Entrez = None


# =============================================================================
# PubMed Search Tools
# =============================================================================

class PubMedSearchInput(BaseModel):
    """Input schema for PubMed search tool."""
    query: str = Field(
        description="PubMed search query string. Use Boolean operators (AND, OR, NOT) and field tags like [Title/Abstract], [MeSH Terms], etc."
    )
    max_results: int = Field(
        default=100,
        description="Maximum number of results to return (max 500)"
    )
    email: str = Field(
        default="slr_agent@example.com",
        description="Email for NCBI API (required by Entrez)"
    )
    date_filter: Optional[str] = Field(
        default=None,
        description="Date filter in format 'YYYY/MM/DD:YYYY/MM/DD' (e.g., '2019/01/01:2024/12/31')"
    )


class PubMedSearchTool(BaseTool):
    """Tool for searching PubMed for relevant literature."""
    
    name: str = "pubmed_search"
    description: str = """Search PubMed for studies matching your query.
    
Use this tool to find relevant literature for your systematic review.
You can use Boolean operators (AND, OR, NOT) and field tags:
- [Title/Abstract] - Search title and abstract
- [MeSH Terms] - Search MeSH terms
- [tiab] - Title/Abstract
- [pt] - Publication Type

Example queries:
- "CAR-T[tiab] AND lymphoma[MeSH Terms] AND clinical trial[pt]"
- "(immunotherapy OR checkpoint inhibitor) AND melanoma[tiab]"

Returns a list of studies with PMIDs, titles, abstracts, and metadata.
"""
    args_schema: Type[BaseModel] = PubMedSearchInput
    
    def _run(
        self,
        query: str,
        max_results: int = 100,
        email: str = "slr_agent@example.com",
        date_filter: Optional[str] = None
    ) -> str:
        """Execute PubMed search."""
        if not BIOPYTHON_AVAILABLE:
            return self._mock_search(query, max_results)
        
        try:
            Entrez.email = email
            
            # Build search query with date filter if provided
            search_query = query
            if date_filter:
                search_query = f"({query}) AND ({date_filter}[dp])"
            
            # Search PubMed
            handle = Entrez.esearch(
                db="pubmed",
                term=search_query,
                retmax=min(max_results, 500),
                sort="relevance"
            )
            search_results = Entrez.read(handle)
            handle.close()
            
            pmids = search_results.get("IdList", [])
            total_count = int(search_results.get("Count", 0))
            
            if not pmids:
                return f"No studies found for query: {query}"
            
            # Fetch details for found PMIDs
            handle = Entrez.efetch(
                db="pubmed",
                id=",".join(pmids),
                rettype="xml"
            )
            records = Entrez.read(handle)
            handle.close()
            
            # Parse results
            results = []
            for article in records.get("PubmedArticle", []):
                try:
                    medline = article.get("MedlineCitation", {})
                    article_data = medline.get("Article", {})
                    
                    pmid = str(medline.get("PMID", ""))
                    title = article_data.get("ArticleTitle", "")
                    
                    # Get abstract
                    abstract_parts = article_data.get("Abstract", {}).get("AbstractText", [])
                    if isinstance(abstract_parts, list):
                        abstract = " ".join([str(p) for p in abstract_parts])
                    else:
                        abstract = str(abstract_parts)
                    
                    # Get authors
                    authors_list = article_data.get("AuthorList", [])
                    authors = []
                    for author in authors_list[:3]:  # First 3 authors
                        last = author.get("LastName", "")
                        initials = author.get("Initials", "")
                        if last:
                            authors.append(f"{last} {initials}".strip())
                    authors_str = ", ".join(authors)
                    if len(authors_list) > 3:
                        authors_str += " et al."
                    
                    # Get journal and year
                    journal_info = article_data.get("Journal", {})
                    journal = journal_info.get("Title", "")
                    year = ""
                    pub_date = journal_info.get("JournalIssue", {}).get("PubDate", {})
                    year = pub_date.get("Year", "")
                    
                    results.append({
                        "pmid": pmid,
                        "title": title,
                        "authors": authors_str,
                        "journal": journal,
                        "year": year,
                        "abstract": abstract[:1500] + "..." if len(abstract) > 1500 else abstract,
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    })
                except Exception as e:
                    continue
            
            # Format output
            output_parts = [
                f"# PubMed Search Results",
                f"**Query:** {query}",
                f"**Total found:** {total_count}",
                f"**Returned:** {len(results)}",
                ""
            ]
            
            for i, r in enumerate(results, 1):
                output_parts.extend([
                    f"## {i}. PMID: {r['pmid']}",
                    f"**Title:** {r['title']}",
                    f"**Authors:** {r['authors']}",
                    f"**Journal:** {r['journal']} ({r['year']})",
                    f"**Abstract:** {r['abstract']}",
                    f"**URL:** {r['url']}",
                    ""
                ])
            
            return "\n".join(output_parts)
            
        except Exception as e:
            return f"Error searching PubMed: {str(e)}\n\nFalling back to mock data.\n\n" + self._mock_search(query, max_results)
    
    def _mock_search(self, query: str, max_results: int) -> str:
        """Return mock search results for testing without PubMed access."""
        mock_studies = [
            {
                "pmid": "38123456",
                "title": "Efficacy and Safety of CAR-T Cell Therapy in Relapsed/Refractory B-Cell Lymphoma: A Systematic Review",
                "authors": "Smith J, Wang L, Garcia M et al.",
                "journal": "Blood",
                "year": "2024",
                "abstract": "Background: Chimeric antigen receptor T-cell (CAR-T) therapy has emerged as a promising treatment for relapsed/refractory B-cell lymphomas. This systematic review evaluates the efficacy and safety of CAR-T therapy in this population. Methods: We searched PubMed, EMBASE, and Cochrane databases through December 2023. Studies reporting outcomes of CAR-T therapy in R/R B-cell lymphoma patients were included. Results: A total of 45 studies were included, encompassing 2,847 patients. The pooled overall response rate was 72% (95% CI: 68-76%), with complete response rate of 51% (95% CI: 46-56%). Median progression-free survival ranged from 6 to 14 months. Cytokine release syndrome occurred in 85% of patients, with grade ≥3 in 12%. Neurotoxicity was observed in 45% of patients. Conclusions: CAR-T therapy demonstrates substantial efficacy in R/R B-cell lymphoma with manageable toxicity.",
                "url": "https://pubmed.ncbi.nlm.nih.gov/38123456/"
            },
            {
                "pmid": "38234567",
                "title": "Long-term Outcomes of Axicabtagene Ciloleucel in Large B-Cell Lymphoma: 5-Year Follow-up Analysis",
                "authors": "Johnson K, Chen Y, Brown S et al.",
                "journal": "Journal of Clinical Oncology",
                "year": "2024",
                "abstract": "Purpose: To report 5-year outcomes of axicabtagene ciloleucel (axi-cel) in patients with relapsed/refractory large B-cell lymphoma (LBCL). Patients and Methods: This analysis includes 307 patients treated with axi-cel in the ZUMA-1 trial with 5-year follow-up. Primary endpoints included overall survival (OS) and progression-free survival (PFS). Results: At 5 years, 42% of patients remained in ongoing response. The 5-year OS rate was 47% and PFS rate was 32%. Among patients achieving complete response at 1 year, 80% remained in remission at 5 years. No new late-onset toxicities were observed. Conclusion: Axi-cel provides durable responses in a substantial proportion of patients with R/R LBCL, supporting its role as a potentially curative therapy.",
                "url": "https://pubmed.ncbi.nlm.nih.gov/38234567/"
            },
            {
                "pmid": "38345678",
                "title": "Comparison of CD19 CAR-T Products in Diffuse Large B-Cell Lymphoma: A Network Meta-Analysis",
                "authors": "Williams R, Lee J, Martinez A et al.",
                "journal": "Lancet Haematology",
                "year": "2024",
                "abstract": "Background: Multiple CD19-directed CAR-T products are approved for diffuse large B-cell lymphoma (DLBCL). We performed a network meta-analysis to compare their efficacy and safety. Methods: We searched databases through October 2023 for trials of tisagenlecleucel, axicabtagene ciloleucel, and lisocabtagene maraleucel in DLBCL. Outcomes included overall response rate, complete response rate, and adverse events. Findings: Ten trials with 1,892 patients were included. All three products showed similar ORR (OR range: 0.85-1.18). Axicabtagene ciloleucel had numerically higher CRR but also higher grade ≥3 CRS compared to other products. Lisocabtagene maraleucel showed the lowest neurotoxicity rates. Interpretation: CD19 CAR-T products have comparable efficacy with differences in safety profiles that may guide product selection.",
                "url": "https://pubmed.ncbi.nlm.nih.gov/38345678/"
            },
            {
                "pmid": "38456789",
                "title": "CAR-T Cell Therapy for Multiple Myeloma: Current Evidence and Future Directions",
                "authors": "Davis M, Thompson K, Anderson P et al.",
                "journal": "Blood Cancer Journal",
                "year": "2024",
                "abstract": "Multiple myeloma remains largely incurable despite significant advances in treatment. BCMA-directed CAR-T cell therapy has shown remarkable efficacy in heavily pretreated patients. This review summarizes the current evidence from clinical trials of CAR-T therapy in multiple myeloma. Idecabtagene vicleucel and ciltacabtagene autoleucel have demonstrated overall response rates exceeding 70%, with complete response rates of 30-40%. However, most patients eventually relapse. Strategies to improve durability include combination therapies, dual-targeting CAR-T cells, and manufacturing optimizations. We also discuss ongoing challenges including access, manufacturing time, and cost considerations.",
                "url": "https://pubmed.ncbi.nlm.nih.gov/38456789/"
            },
            {
                "pmid": "38567890",
                "title": "Real-World Outcomes of Commercial CAR-T Therapy in Aggressive B-Cell Lymphoma: A Multi-Center Analysis",
                "authors": "Miller E, Harris N, Wilson D et al.",
                "journal": "Haematologica",
                "year": "2023",
                "abstract": "Background: Real-world data on CAR-T therapy outcomes may differ from clinical trials. We analyzed outcomes of commercially available CAR-T products in routine practice. Methods: Retrospective analysis of 523 patients treated at 15 centers between 2018-2023. Results: ORR was 65%, with CRR of 42%. Median PFS was 8.2 months and OS was 18.5 months. Patients with high tumor burden and elevated LDH had inferior outcomes. Grade ≥3 CRS occurred in 18% and grade ≥3 neurotoxicity in 12%. Treatment-related mortality was 3.2%. Conclusions: Real-world outcomes are modestly lower than clinical trials, highlighting the importance of patient selection and management optimization.",
                "url": "https://pubmed.ncbi.nlm.nih.gov/38567890/"
            }
        ]
        
        # Format output
        output_parts = [
            f"# PubMed Search Results (Mock Data)",
            f"**Query:** {query}",
            f"**Note:** Using mock data for demonstration",
            f"**Total found:** {len(mock_studies)}",
            f"**Returned:** {min(max_results, len(mock_studies))}",
            ""
        ]
        
        for i, r in enumerate(mock_studies[:max_results], 1):
            output_parts.extend([
                f"## {i}. PMID: {r['pmid']}",
                f"**Title:** {r['title']}",
                f"**Authors:** {r['authors']}",
                f"**Journal:** {r['journal']} ({r['year']})",
                f"**Abstract:** {r['abstract']}",
                f"**URL:** {r['url']}",
                ""
            ])
        
        return "\n".join(output_parts)


class FetchAbstractsInput(BaseModel):
    """Input schema for fetching abstracts by PMIDs."""
    pmids: str = Field(
        description="Comma-separated list of PubMed IDs to fetch (e.g., '12345678,23456789')"
    )
    email: str = Field(
        default="slr_agent@example.com",
        description="Email for NCBI API"
    )


class FetchAbstractsTool(BaseTool):
    """Tool for fetching full abstracts for specific PMIDs."""
    
    name: str = "fetch_abstracts"
    description: str = """Fetch full abstracts for specific PubMed IDs.
    
Use this tool when you need complete abstract text for studies you've identified.
Provide comma-separated PMIDs to retrieve their full abstracts.
"""
    args_schema: Type[BaseModel] = FetchAbstractsInput
    
    def _run(self, pmids: str, email: str = "slr_agent@example.com") -> str:
        """Fetch abstracts for given PMIDs."""
        pmid_list = [p.strip() for p in pmids.split(",") if p.strip()]
        
        if not pmid_list:
            return "Error: No valid PMIDs provided."
        
        if not BIOPYTHON_AVAILABLE:
            return f"Biopython not available. Requested PMIDs: {pmids}"
        
        try:
            Entrez.email = email
            
            handle = Entrez.efetch(
                db="pubmed",
                id=",".join(pmid_list),
                rettype="xml"
            )
            records = Entrez.read(handle)
            handle.close()
            
            results = []
            for article in records.get("PubmedArticle", []):
                try:
                    medline = article.get("MedlineCitation", {})
                    article_data = medline.get("Article", {})
                    
                    pmid = str(medline.get("PMID", ""))
                    title = article_data.get("ArticleTitle", "")
                    
                    # Get full abstract
                    abstract_parts = article_data.get("Abstract", {}).get("AbstractText", [])
                    if isinstance(abstract_parts, list):
                        abstract = " ".join([str(p) for p in abstract_parts])
                    else:
                        abstract = str(abstract_parts)
                    
                    results.append({
                        "pmid": pmid,
                        "title": title,
                        "abstract": abstract
                    })
                except:
                    continue
            
            output_parts = [f"# Abstracts for {len(results)} studies\n"]
            for r in results:
                output_parts.extend([
                    f"## PMID: {r['pmid']}",
                    f"**Title:** {r['title']}",
                    f"\n{r['abstract']}\n",
                    "---\n"
                ])
            
            return "\n".join(output_parts)
            
        except Exception as e:
            return f"Error fetching abstracts: {str(e)}"


# =============================================================================
# Eligibility Screening Tools
# =============================================================================

class GenerateCriteriaInput(BaseModel):
    """Input schema for generating eligibility criteria."""
    research_question: str = Field(
        description="The research question for the SLR"
    )
    pico_population: str = Field(
        default="",
        description="Population of interest"
    )
    pico_intervention: str = Field(
        default="",
        description="Intervention of interest"
    )
    pico_comparison: str = Field(
        default="",
        description="Comparator (if applicable)"
    )
    pico_outcomes: str = Field(
        default="",
        description="Outcomes of interest"
    )
    study_types: str = Field(
        default="clinical trials, observational studies",
        description="Types of studies to include"
    )


class GenerateCriteriaTool(BaseTool):
    """Tool for generating eligibility criteria based on PICO elements."""
    
    name: str = "generate_eligibility_criteria"
    description: str = """Generate eligibility criteria for literature screening based on PICO elements.

This tool creates a structured set of inclusion and exclusion criteria
based on the research question and PICO (Population, Intervention, Comparison, Outcome) elements.

The generated criteria can be reviewed and modified before screening.
"""
    args_schema: Type[BaseModel] = GenerateCriteriaInput
    
    def _run(
        self,
        research_question: str,
        pico_population: str = "",
        pico_intervention: str = "",
        pico_comparison: str = "",
        pico_outcomes: str = "",
        study_types: str = "clinical trials, observational studies"
    ) -> str:
        """Generate eligibility criteria."""
        
        criteria_template = f"""
# Eligibility Criteria for Systematic Literature Review

## Research Question
{research_question}

## PICO Elements
- **Population:** {pico_population or "Not specified"}
- **Intervention:** {pico_intervention or "Not specified"}
- **Comparison:** {pico_comparison or "Not specified"}
- **Outcomes:** {pico_outcomes or "Not specified"}

## Suggested Inclusion Criteria

### Population Criteria
C1. Study includes patients with {pico_population or "[target population]"}
C2. Human subjects only

### Intervention Criteria
C3. Study evaluates {pico_intervention or "[target intervention]"}
C4. Intervention is the primary focus of the study

### Outcome Criteria
C5. Study reports on {pico_outcomes or "[target outcomes]"}
C6. Outcomes are clearly defined and measured

### Study Design Criteria
C7. Study type is one of: {study_types}
C8. Original research (not review, commentary, or letter)

### Publication Criteria
C9. Published in peer-reviewed journal
C10. Full text available (or sufficient abstract data)

## Suggested Exclusion Criteria

E1. Animal studies or in vitro studies only
E2. Case reports with fewer than 5 patients
E3. Studies not reporting relevant outcomes
E4. Duplicate publications or overlapping cohorts
E5. Non-English publications without translation
E6. Conference abstracts without full publication

---

**Instructions:** Review and modify these criteria as needed before proceeding with screening.
Use the criterion IDs (C1, C2, E1, etc.) when screening studies.
"""
        return criteria_template


class ScreenStudyInput(BaseModel):
    """Input schema for screening a single study."""
    pmid: str = Field(description="PubMed ID of the study")
    title: str = Field(description="Study title")
    abstract: str = Field(description="Study abstract")
    criteria: str = Field(
        description="List of eligibility criteria to screen against (JSON format or semicolon-separated)"
    )


class ScreenStudyTool(BaseTool):
    """Tool for screening a study against eligibility criteria."""
    
    name: str = "screen_study"
    description: str = """Screen a study against eligibility criteria.

This tool evaluates a study's title and abstract against each eligibility criterion
and provides a structured assessment of eligibility.

Provide the study details and criteria, and receive predictions for each criterion.
"""
    args_schema: Type[BaseModel] = ScreenStudyInput
    
    def _run(
        self,
        pmid: str,
        title: str,
        abstract: str,
        criteria: str
    ) -> str:
        """Screen a study against criteria."""
        
        # This tool returns a template that the LLM will complete
        template = f"""
# Study Eligibility Screening

## Study Information
- **PMID:** {pmid}
- **Title:** {title}

## Abstract
{abstract}

## Screening Template

Please evaluate this study against each criterion below:

{criteria}

### Assessment Format

For each criterion, provide:
| Criterion | Assessment | Evidence | Confidence |
|-----------|------------|----------|------------|
| C1 | ELIGIBLE/NOT_ELIGIBLE/UNCERTAIN | Quote or reasoning | HIGH/MEDIUM/LOW |
| C2 | ... | ... | ... |

### Overall Decision

Based on the individual assessments:
- **Include:** If all inclusion criteria met AND no exclusion criteria violated
- **Exclude:** If any critical inclusion criterion not met OR any exclusion criterion violated
- **Uncertain:** If key information is missing and cannot be determined

**Final Decision:** [INCLUDE/EXCLUDE/UNCERTAIN]
**Reasons:** [Brief explanation]
"""
        return template


# =============================================================================
# Data Extraction Tools
# =============================================================================

class ExtractDataInput(BaseModel):
    """Input schema for data extraction."""
    pmid: str = Field(description="PubMed ID")
    title: str = Field(description="Study title")
    abstract: str = Field(description="Study abstract")
    extraction_fields: str = Field(
        default="study_design,sample_size,population,intervention,comparator,primary_outcome,efficacy_results,safety_results,follow_up",
        description="Comma-separated list of fields to extract"
    )


class ExtractDataTool(BaseTool):
    """Tool for extracting structured data from study abstracts."""
    
    name: str = "extract_study_data"
    description: str = """Extract structured data from a study abstract.

This tool provides a template for extracting key data elements from study abstracts
including study design, sample size, population characteristics, intervention details,
and outcome results.
"""
    args_schema: Type[BaseModel] = ExtractDataInput
    
    def _run(
        self,
        pmid: str,
        title: str,
        abstract: str,
        extraction_fields: str = "study_design,sample_size,population,intervention,comparator,primary_outcome,efficacy_results,safety_results,follow_up"
    ) -> str:
        """Extract data from study abstract."""
        
        fields = [f.strip() for f in extraction_fields.split(",")]
        
        fields_template = "\n".join([f"- **{field}:** [EXTRACT VALUE]" for field in fields])
        
        template = f"""
# Data Extraction Form

## Study Information
- **PMID:** {pmid}
- **Title:** {title}

## Abstract
{abstract}

## Extraction Fields

{fields_template}

## Extraction Instructions

1. For each field, extract the relevant value from the abstract
2. If a value is not reported, mark as "NR" (Not Reported)
3. For numerical values, include units when available
4. For outcomes, include point estimates and confidence intervals when available
5. Note any uncertainty in extraction with [?]

## Extracted Data

Complete the following JSON structure:

```json
{{
    "pmid": "{pmid}",
    "title": "{title}",
    "extracted_fields": {{
        "study_design": "",
        "sample_size": null,
        "population": "",
        "intervention": "",
        "comparator": "",
        "primary_outcome": "",
        "efficacy_results": [],
        "safety_results": [],
        "follow_up": "",
        "quality_notes": ""
    }}
}}
```
"""
        return template


# =============================================================================
# Evidence Synthesis Tools
# =============================================================================

class SynthesizeEvidenceInput(BaseModel):
    """Input schema for evidence synthesis."""
    extracted_data: str = Field(
        description="JSON string containing extracted data from all included studies"
    )
    target_outcomes: str = Field(
        default="overall_response,complete_response,overall_survival,progression_free_survival,adverse_events",
        description="Comma-separated list of target outcomes to synthesize"
    )
    synthesis_type: str = Field(
        default="narrative",
        description="Type of synthesis: 'narrative', 'quantitative', or 'both'"
    )


class SynthesizeEvidenceTool(BaseTool):
    """Tool for synthesizing evidence across included studies."""
    
    name: str = "synthesize_evidence"
    description: str = """Synthesize evidence across multiple studies.

This tool helps aggregate and summarize findings from included studies,
providing both quantitative summaries (when appropriate) and narrative synthesis.
"""
    args_schema: Type[BaseModel] = SynthesizeEvidenceInput
    
    def _run(
        self,
        extracted_data: str,
        target_outcomes: str = "overall_response,complete_response,overall_survival,progression_free_survival,adverse_events",
        synthesis_type: str = "narrative"
    ) -> str:
        """Synthesize evidence from extracted data."""
        
        outcomes = [o.strip() for o in target_outcomes.split(",")]
        
        template = f"""
# Evidence Synthesis Template

## Input Data Summary
The following extracted data will be synthesized:
{extracted_data[:2000]}{"..." if len(extracted_data) > 2000 else ""}

## Target Outcomes
{chr(10).join([f"- {o}" for o in outcomes])}

## Synthesis Framework

### 1. Study Characteristics Summary
Create a summary table of included studies:
| Study | Year | Design | N | Population | Intervention | Follow-up |
|-------|------|--------|---|------------|--------------|-----------|

### 2. Efficacy Outcomes

For each efficacy outcome, synthesize:
- Number of studies reporting
- Range of results across studies
- Pooled estimate (if quantitative synthesis appropriate)
- Heterogeneity assessment
- Quality of evidence

### 3. Safety Outcomes

For each safety outcome, synthesize:
- Frequency of reporting
- Range of incidence rates
- Severity grading when available
- Management strategies if described

### 4. Subgroup Analyses

If data permits, analyze by:
- Disease subtype
- Prior therapies
- Patient characteristics

### 5. Quality Assessment

Assess overall quality considering:
- Study designs included
- Risk of bias
- Consistency of findings
- Precision of estimates
- Publication bias concerns

### 6. Conclusions

Summarize:
- Main findings
- Strength of evidence
- Limitations
- Implications for practice
- Research gaps

## Synthesis Output

Please complete the synthesis based on the extracted data above.
"""
        return template


class GenerateSLRReportInput(BaseModel):
    """Input schema for generating the final SLR report."""
    research_question: str = Field(description="The research question")
    search_summary: str = Field(description="Summary of literature search")
    screening_summary: str = Field(description="Summary of screening process")
    extraction_summary: str = Field(description="Summary of data extraction")
    synthesis_summary: str = Field(description="Evidence synthesis results")


class GenerateSLRReportTool(BaseTool):
    """Tool for generating the final SLR report."""
    
    name: str = "generate_slr_report"
    description: str = """Generate the final systematic literature review report.

This tool assembles all components of the SLR into a structured final report
following PRISMA guidelines.
"""
    args_schema: Type[BaseModel] = GenerateSLRReportInput
    
    def _run(
        self,
        research_question: str,
        search_summary: str,
        screening_summary: str,
        extraction_summary: str,
        synthesis_summary: str
    ) -> str:
        """Generate the final SLR report."""
        
        report = f"""
# Systematic Literature Review Report

## 1. Executive Summary

### Research Question
{research_question}

[Complete executive summary based on key findings]

---

## 2. Introduction

### 2.1 Background
[Background on the topic and rationale for the review]

### 2.2 Objectives
- Primary objective: {research_question}
- Secondary objectives: [List if applicable]

---

## 3. Methods

### 3.1 Literature Search Strategy
{search_summary}

### 3.2 Eligibility Criteria and Screening
{screening_summary}

### 3.3 Data Extraction
{extraction_summary}

### 3.4 Quality Assessment
[Describe quality assessment approach]

### 3.5 Data Synthesis
[Describe synthesis methodology]

---

## 4. Results

### 4.1 Study Selection
[PRISMA flow diagram description]

### 4.2 Study Characteristics
[Summary of included studies]

### 4.3 Evidence Synthesis
{synthesis_summary}

---

## 5. Discussion

### 5.1 Summary of Main Findings
[Key findings interpretation]

### 5.2 Comparison with Existing Literature
[Context with other reviews/studies]

### 5.3 Strengths and Limitations
[Review strengths and limitations]

### 5.4 Implications for Practice
[Clinical/practical implications]

---

## 6. Conclusions

[Final conclusions and recommendations]

---

## 7. References

[List of included studies]

---

*Report generated using TrialMind-SLR Agent*
"""
        return report


# =============================================================================
# Tool Registry
# =============================================================================

def get_search_tools() -> List[BaseTool]:
    """Get tools for the literature search stage."""
    return [
        PubMedSearchTool(),
        FetchAbstractsTool(),
    ]


def get_screening_tools() -> List[BaseTool]:
    """Get tools for the screening stage."""
    return [
        GenerateCriteriaTool(),
        ScreenStudyTool(),
        FetchAbstractsTool(),
    ]


def get_extraction_tools() -> List[BaseTool]:
    """Get tools for the data extraction stage."""
    return [
        ExtractDataTool(),
        FetchAbstractsTool(),
    ]


def get_synthesis_tools() -> List[BaseTool]:
    """Get tools for the evidence synthesis stage."""
    return [
        SynthesizeEvidenceTool(),
        GenerateSLRReportTool(),
    ]


def get_all_trialmind_slr_tools() -> List[BaseTool]:
    """Get all tools for the TrialMind-SLR agent."""
    return [
        PubMedSearchTool(),
        FetchAbstractsTool(),
        GenerateCriteriaTool(),
        ScreenStudyTool(),
        ExtractDataTool(),
        SynthesizeEvidenceTool(),
        GenerateSLRReportTool(),
    ]
