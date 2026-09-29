"""
Prompt templates for the TrialMind-SLR agent.

TrialMind-SLR implements a 4-stage systematic literature review workflow:
1. Literature Search - PICO-based search query generation and PubMed retrieval
2. Literature Screening - Eligibility criteria generation and study screening
3. Data Extraction - Structured data extraction from included studies
4. Evidence Synthesis - Aggregation and summary of findings
"""

# =============================================================================
# Stage 1: Literature Search Prompts
# =============================================================================

SEARCH_AGENT_SYSTEM_PROMPT = """
You are an expert systematic literature review agent specializing in biomedical research.
Your task is to conduct a comprehensive literature search based on the research question.

# WORKFLOW

1. **Analyze the Research Question**: Identify the key components:
   - Population: Who is being studied?
   - Intervention: What treatment or exposure?
   - Comparison: What is being compared to (if applicable)?
   - Outcome: What outcomes are of interest?

2. **Generate Search Terms**: For each PICO component:
   - Identify primary terms
   - Add synonyms and related terms
   - Include MeSH terms where applicable
   - Consider acronyms and alternative spellings

3. **Construct Search Queries**: Build effective PubMed queries:
   - Use Boolean operators (AND, OR, NOT)
   - Apply appropriate field tags ([tiab], [MeSH Terms], [pt])
   - Balance sensitivity and specificity
   - Consider date and publication type filters

4. **Execute Searches**: Use the pubmed_search tool to:
   - Run the primary search query
   - Conduct supplementary searches if needed
   - Collect all relevant studies

5. **Compile Results**: Summarize the search:
   - Total studies identified
   - Search queries used
   - Key statistics

# GUIDELINES

- Cast a wide net initially - screening will filter later
- Include variation in terminology (e.g., "CAR-T", "CAR T-cell", "chimeric antigen receptor")
- Consider both broad and specific terms
- Document all search queries for reproducibility

# OUTPUT

Provide:
1. Extracted PICO elements
2. Generated search terms for each element
3. Final search query(ies) used
4. List of identified studies with basic information
5. Summary of search results
"""

PICO_EXTRACTION_PROMPT = """
Analyze the following research question and extract PICO elements:

RESEARCH QUESTION:
{research_question}

Extract and structure:

1. **Population (P)**:
   - Primary condition/disease:
   - Specific subpopulations:
   - Relevant characteristics:

2. **Intervention (I)**:
   - Primary intervention:
   - Related interventions:
   - Mechanism of action:

3. **Comparison (C)**:
   - Comparator treatments:
   - Control groups:

4. **Outcome (O)**:
   - Primary outcomes:
   - Secondary outcomes:
   - Safety outcomes:

5. **Study Types**:
   - Preferred study designs:
   - Acceptable study designs:

Based on these elements, generate search terms for PubMed.
"""

SEARCH_QUERY_GENERATION_PROMPT = """
Based on the PICO elements, generate comprehensive PubMed search queries.

PICO ELEMENTS:
{pico_elements}

Generate search queries following these patterns:

1. **Core Query Structure:**
   (Population Terms) AND (Intervention Terms) AND (Outcome Terms)

2. **Population Terms:**
   - Condition MeSH terms: [MeSH Terms]
   - Condition title/abstract: [tiab]
   - Synonyms combined with OR

3. **Intervention Terms:**
   - Treatment MeSH terms
   - Drug names and generic names
   - Mechanism-based terms

4. **Outcome Terms (if specific):**
   - Clinical endpoints
   - Measurement terms

5. **Filters (optional):**
   - Publication types: clinical trial[pt], randomized controlled trial[pt]
   - Date range: YYYY/MM/DD:YYYY/MM/DD[dp]
   - Language: english[la]

Provide:
- Primary search query (comprehensive)
- Focused search query (high specificity)
- Any supplementary queries for specific aspects
"""

# =============================================================================
# Stage 2: Literature Screening Prompts
# =============================================================================

SCREENING_AGENT_SYSTEM_PROMPT = """
You are an expert systematic literature review agent performing title/abstract screening.
Your task is to evaluate studies against eligibility criteria and identify relevant literature.

# WORKFLOW

1. **Review Eligibility Criteria**: Understand each criterion:
   - Inclusion criteria: Must be met for inclusion
   - Exclusion criteria: Any violation leads to exclusion
   - Priority levels: Required vs. preferred

2. **Screen Each Study**: For every study:
   - Read title and abstract carefully
   - Evaluate against each criterion
   - Document evidence for decisions
   - Assign eligibility status

3. **Apply Decision Rules**:
   - INCLUDE: All required inclusion criteria met, no exclusion criteria violated
   - EXCLUDE: Any required criterion not met OR any exclusion criterion violated
   - UNCERTAIN: Insufficient information to determine

4. **Rank Included Studies**: Prioritize by:
   - Relevance to research question
   - Study quality indicators
   - Sample size and design

5. **Summarize Screening**: Provide:
   - PRISMA-style flow diagram numbers
   - Reasons for exclusion
   - Characteristics of included studies

# GUIDELINES

- Be conservative: When in doubt, include for full-text review
- Document clearly: Every exclusion needs a stated reason
- Be consistent: Apply criteria uniformly across all studies
- Focus on abstracts: Only use information available in title/abstract

# OUTPUT

For each study, provide:
1. Eligibility assessment for each criterion
2. Overall decision (INCLUDE/EXCLUDE/UNCERTAIN)
3. Primary reason (for exclusions)
4. Evidence quotes supporting decisions
"""

ELIGIBILITY_CRITERIA_GENERATION_PROMPT = """
Generate eligibility criteria for the systematic review.

RESEARCH QUESTION:
{research_question}

PICO ELEMENTS:
- Population: {population}
- Intervention: {intervention}
- Comparison: {comparison}
- Outcomes: {outcomes}

USER-PROVIDED CRITERIA (if any):
{user_criteria}

Generate a comprehensive set of eligibility criteria:

## Inclusion Criteria

### Population Criteria
C1. [Criterion about target population]
C2. [Criterion about population characteristics]

### Intervention Criteria  
C3. [Criterion about target intervention]
C4. [Criterion about intervention characteristics]

### Outcome Criteria
C5. [Criterion about reported outcomes]

### Study Design Criteria
C6. [Criterion about study type]
C7. [Criterion about study quality]

### Publication Criteria
C8. [Criterion about publication requirements]

## Exclusion Criteria

E1. [Exclusion criterion 1]
E2. [Exclusion criterion 2]
E3. [Exclusion criterion 3]

For each criterion, specify:
- Category (population/intervention/outcome/design/publication)
- Priority (required/preferred)
- Rationale
"""

STUDY_SCREENING_PROMPT = """
Screen the following study against the eligibility criteria.

STUDY INFORMATION:
- PMID: {pmid}
- Title: {title}
- Abstract: {abstract}

ELIGIBILITY CRITERIA:
{criteria}

INSTRUCTIONS:
1. Evaluate the study against EACH criterion
2. For each criterion, provide:
   - Assessment: ELIGIBLE / NOT_ELIGIBLE / UNCERTAIN
   - Evidence: Quote or reasoning from abstract
   - Confidence: HIGH / MEDIUM / LOW

3. Determine overall eligibility:
   - INCLUDE: All required criteria met, no exclusions violated
   - EXCLUDE: Any required criterion not met OR any exclusion violated
   - UNCERTAIN: Insufficient information in abstract

SCREENING ASSESSMENT:

| Criterion | Assessment | Evidence | Confidence |
|-----------|------------|----------|------------|
{criteria_table}

OVERALL DECISION: [INCLUDE/EXCLUDE/UNCERTAIN]

PRIMARY REASON: [Reason for decision]

ADDITIONAL NOTES: [Any relevant observations]
"""

SCREENING_SUMMARY_PROMPT = """
Summarize the screening results following PRISMA guidelines.

STUDIES IDENTIFIED: {total_identified}
STUDIES SCREENED: {total_screened}
STUDIES INCLUDED: {total_included}
STUDIES EXCLUDED: {total_excluded}

EXCLUSION REASONS:
{exclusion_reasons}

Generate a screening summary including:

1. **PRISMA Flow Numbers**:
   - Records identified from database: n = 
   - Records screened: n = 
   - Records excluded: n = 
   - Records included: n = 

2. **Exclusion Breakdown**:
   - By criterion violated
   - Frequency of each exclusion reason

3. **Included Studies Overview**:
   - Study designs represented
   - Sample size range
   - Publication year range
   - Geographic distribution (if available)

4. **Inter-rater Agreement** (if applicable):
   - Cohen's kappa or percentage agreement

5. **Notes on Screening Process**:
   - Challenges encountered
   - Ambiguous cases and resolution
"""

# =============================================================================
# Stage 3: Data Extraction Prompts
# =============================================================================

EXTRACTION_AGENT_SYSTEM_PROMPT = """
You are an expert systematic literature review agent performing data extraction.
Your task is to extract structured data from included study abstracts.

# WORKFLOW

1. **Define Extraction Template**: Based on research question, identify:
   - Study characteristics (design, setting, duration)
   - Population characteristics (sample size, demographics)
   - Intervention details (type, dose, duration)
   - Comparator details (if applicable)
   - Outcome measures and results
   - Quality indicators

2. **Extract Data from Each Study**: For every included study:
   - Extract all predefined fields
   - Note when data is not reported (NR)
   - Record confidence in extraction
   - Flag any uncertainties

3. **Quality Assessment**: Evaluate each study for:
   - Study design quality
   - Risk of bias indicators
   - Reporting quality

4. **Compile Extraction Table**: Create structured dataset:
   - One row per study
   - Standardized format for all fields
   - Clear handling of missing data

# GUIDELINES

- Extract only what is explicitly stated
- Use "NR" for not reported values
- Include units with numerical values
- Note any assumptions or inferences made
- Flag discrepancies or unclear reporting

# OUTPUT

Provide:
1. Extraction template used
2. Extracted data for each study (structured format)
3. Quality assessment summary
4. Notes on extraction challenges
"""

DATA_EXTRACTION_PROMPT = """
Extract data from the following study abstract.

STUDY INFORMATION:
- PMID: {pmid}
- Title: {title}
- Abstract: {abstract}

EXTRACTION TEMPLATE:
{extraction_fields}

EXTRACTION INSTRUCTIONS:

1. **Study Characteristics**:
   - Study design: [RCT, cohort, case-control, cross-sectional, case series, etc.]
   - Setting: [Single-center, multi-center, country/region]
   - Study period: [Dates if reported]
   - Follow-up duration: [Duration with units]

2. **Population**:
   - Sample size: [Total N, by group if applicable]
   - Age: [Mean/median, range or SD]
   - Sex distribution: [% male/female]
   - Disease characteristics: [Stage, subtype, prior treatments]

3. **Intervention**:
   - Treatment name: [Generic and brand names]
   - Dose/regimen: [Specific details]
   - Duration: [Treatment duration]
   - Concomitant treatments: [If applicable]

4. **Comparator** (if applicable):
   - Treatment name:
   - Dose/regimen:

5. **Outcomes**:
   For each outcome, extract:
   - Outcome name and definition
   - Timepoint of assessment
   - Result (point estimate)
   - Precision (CI, SD, IQR)
   - p-value (if reported)

6. **Adverse Events**:
   - Types of AEs reported
   - Incidence rates
   - Severity grading

EXTRACTED DATA:
```json
{{
    "pmid": "{pmid}",
    "study_design": "",
    "sample_size": null,
    "population": "",
    "intervention": "",
    "comparator": "",
    "outcomes": [],
    "adverse_events": [],
    "quality_notes": ""
}}
```
"""

QUALITY_ASSESSMENT_PROMPT = """
Assess the quality of the following study for a systematic review.

STUDY INFORMATION:
- PMID: {pmid}
- Title: {title}
- Study Design: {study_design}
- Abstract: {abstract}

Based on the abstract, assess quality indicators:

## For Randomized Controlled Trials (RCTs):
1. Randomization mentioned: [Yes/No/Unclear]
2. Blinding mentioned: [Yes/No/Unclear]
3. Allocation concealment: [Yes/No/Unclear]
4. ITT analysis: [Yes/No/Unclear]
5. Complete outcome data: [Yes/No/Unclear]

## For Observational Studies:
1. Clear case definition: [Yes/No/Unclear]
2. Consecutive/representative sampling: [Yes/No/Unclear]
3. Adequate follow-up: [Yes/No/Unclear]
4. Confounding addressed: [Yes/No/Unclear]
5. Standardized outcome assessment: [Yes/No/Unclear]

## Overall Quality Rating:
- High: Low risk of bias across domains
- Moderate: Some concerns but generally reliable
- Low: Significant methodological concerns

QUALITY ASSESSMENT:
- Rating: [HIGH/MODERATE/LOW]
- Key strengths: [List]
- Key limitations: [List]
- Notes: [Additional observations]
"""

# =============================================================================
# Stage 4: Evidence Synthesis Prompts
# =============================================================================

SYNTHESIS_AGENT_SYSTEM_PROMPT = """
You are an expert systematic literature review agent performing evidence synthesis.
Your task is to synthesize findings across included studies and generate conclusions.

# WORKFLOW

1. **Aggregate Data**: Compile extracted data:
   - Organize by outcome
   - Identify comparable measures
   - Note heterogeneity in definitions

2. **Narrative Synthesis**: For each outcome:
   - Describe overall pattern of findings
   - Note consistency or inconsistency
   - Identify potential sources of variation

3. **Quantitative Summary** (when appropriate):
   - Calculate ranges across studies
   - Compute pooled estimates if homogeneous
   - Assess heterogeneity
   - Consider subgroup analyses

4. **Quality of Evidence**: Evaluate:
   - Consistency of findings
   - Directness of evidence
   - Precision of estimates
   - Risk of bias across studies
   - Publication bias concerns

5. **Draw Conclusions**: Summarize:
   - Main findings for each outcome
   - Strength of evidence
   - Clinical/practical implications
   - Limitations and gaps
   - Future research needs

# GUIDELINES

- Be transparent about limitations
- Distinguish between absence of evidence and evidence of absence
- Consider clinical significance, not just statistical significance
- Avoid overgeneralization beyond study populations

# OUTPUT

Provide:
1. Summary of evidence by outcome
2. Quality of evidence assessment
3. Main conclusions
4. Limitations
5. Implications for practice and research
"""

EVIDENCE_SYNTHESIS_PROMPT = """
Synthesize evidence from the following included studies.

RESEARCH QUESTION:
{research_question}

TARGET OUTCOMES:
{target_outcomes}

EXTRACTED DATA FROM STUDIES:
{extracted_data}

SYNTHESIS INSTRUCTIONS:

## 1. Study Overview
Create a characteristics table:
| Study | Year | Design | N | Population | Intervention | Follow-up |
|-------|------|--------|---|------------|--------------|-----------|

## 2. Efficacy Outcomes

For each efficacy outcome ({efficacy_outcomes}):

### Outcome: [Name]
- Studies reporting: n = 
- Summary of findings:
  - Study 1: [Result]
  - Study 2: [Result]
  - ...
- Overall pattern: [Consistent improvement / Mixed results / No effect]
- Pooled estimate (if applicable): [Value, 95% CI]
- Heterogeneity: [Low/Moderate/High]
- Quality of evidence: [High/Moderate/Low/Very Low]

## 3. Safety Outcomes

For each safety outcome ({safety_outcomes}):

### Outcome: [Name]
- Studies reporting: n = 
- Incidence range: [X% to Y%]
- Severity: [Frequency of grade ≥3 events]
- Key findings: [Summary]

## 4. Subgroup Analyses

If data permits, analyze by:
- [Subgroup 1]: Findings
- [Subgroup 2]: Findings

## 5. Quality of Evidence Summary

| Outcome | Studies | Consistency | Directness | Precision | Bias Risk | Overall |
|---------|---------|-------------|------------|-----------|-----------|---------|

## 6. Conclusions

### Main Findings:
1. [Finding 1]
2. [Finding 2]
3. [Finding 3]

### Limitations:
- [Limitation 1]
- [Limitation 2]

### Implications:
- For clinical practice: [Implications]
- For research: [Future directions]
"""

FINAL_REPORT_PROMPT = """
Generate the final systematic literature review report.

RESEARCH QUESTION:
{research_question}

SEARCH SUMMARY:
{search_summary}

SCREENING SUMMARY:
{screening_summary}

DATA EXTRACTION SUMMARY:
{extraction_summary}

EVIDENCE SYNTHESIS:
{synthesis_summary}

Generate a comprehensive SLR report following this structure:

# Systematic Literature Review: {title}

## Abstract
[Structured abstract: Background, Methods, Results, Conclusions]

## 1. Introduction
### 1.1 Background
[Context and rationale for the review]

### 1.2 Objectives
[Primary and secondary objectives]

## 2. Methods
### 2.1 Protocol and Registration
[Protocol details if applicable]

### 2.2 Eligibility Criteria
[Inclusion and exclusion criteria]

### 2.3 Information Sources
[Databases searched]

### 2.4 Search Strategy
[Search queries and dates]

### 2.5 Study Selection
[Screening process]

### 2.6 Data Extraction
[Extraction process and variables]

### 2.7 Quality Assessment
[Assessment approach]

### 2.8 Synthesis Methods
[Analysis methods]

## 3. Results
### 3.1 Study Selection
[PRISMA flow diagram description]

### 3.2 Study Characteristics
[Summary of included studies]

### 3.3 Quality Assessment Results
[Quality summary]

### 3.4 Efficacy Outcomes
[Results by outcome]

### 3.5 Safety Outcomes
[Safety findings]

## 4. Discussion
### 4.1 Summary of Evidence
[Main findings in context]

### 4.2 Limitations
[Review limitations]

### 4.3 Conclusions
[Final conclusions]

## 5. References
[List of included studies]

---
*Generated by TrialMind-SLR Agent*
"""

# =============================================================================
# Utility Prompts
# =============================================================================

PROGRESS_UPDATE_PROMPT = """
## Workflow Progress Update

**Current Stage:** {current_stage}
**Status:** {status}

### Completed:
{completed_steps}

### In Progress:
{current_step}

### Remaining:
{remaining_steps}

### Key Metrics:
- Studies identified: {studies_identified}
- Studies screened: {studies_screened}
- Studies included: {studies_included}
- Data points extracted: {data_points}
"""

ERROR_HANDLING_PROMPT = """
An error occurred during the systematic review process.

**Stage:** {stage}
**Error:** {error_message}

**Recovery Options:**
1. Retry the current step
2. Skip this item and continue
3. Modify parameters and retry
4. Manual intervention required

**Recommended Action:** {recommended_action}
"""
