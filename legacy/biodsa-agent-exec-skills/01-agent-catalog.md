# 01 — Agent Catalog

This guide helps you pick the right BioDSA agent for a user's task.

> **Model reminder**: All examples below use `"gpt-5"` as the default. Always use **frontier-tier models** (`gpt-5`, `claude-opus-4-20250514`, `gemini-2.5-pro`). Weaker models like `gpt-4o` or `gpt-4o-mini` produce significantly worse results for complex biomedical tasks.

---

## Decision Guide

| User Wants To… | Use This Agent |
|----------------|---------------|
| Analyze a biomedical dataset (CSV/tables) with code | **DSWizardAgent** |
| Write and execute Python code on data files | **CoderAgent** |
| Answer a question using tool-calling (general) | **ReactAgent** |
| Deep research across multiple knowledge bases | **DeepEvidenceAgent** |
| Conduct a systematic literature review | **TrialMindSLRAgent** |
| Systematic review + meta-analysis with forest plots | **SLRMetaAgent** |
| Generate a clinical or regulatory document | **InformGenAgent** |
| Match a patient to clinical trials | **TrialGPTAgent** |
| Predict clinical risk from a patient note | **AgentMD** |
| Analyze a gene set (GO enrichment, verification) | **GeneAgent** |
| Run a multi-agent scientific discussion | **VirtualLabAgent** |

---

## Agent Details

### DSWizardAgent

**Purpose**: Two-phase data science agent (planning → implementation) for biomedical data analysis.

```python
from biodsa.agents import DSWizardAgent

agent = DSWizardAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

# REQUIRED: register the dataset directory
agent.register_workspace("./biomedical_data/cBioPortal/datasets/acbc_mskcc_2015")

results = agent.go("Perform survival analysis for TP53 mutant vs wild-type patients")
```

**`go()` signature**: `go(input_query: str, verbose: bool = True) -> ExecutionResults`

**Needs workspace**: Yes — the agent writes and executes code on the registered CSV files.

---

### DeepEvidenceAgent

**Purpose**: Hierarchical multi-agent system for deep research across 17+ biomedical knowledge bases.

```python
from biodsa.agents import DeepEvidenceAgent

agent = DeepEvidenceAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

results = agent.go(
    "What are resistance mechanisms to EGFR inhibitors in lung cancer?",
    knowledge_bases=["pubmed_papers", "gene", "disease", "drug"],
)
```

**`go()` signature**: `go(input_query: str, knowledge_bases: List[str] = None, verbose: bool = True, clear_evidence_graph_cache: bool = True) -> DeepEvidenceExecutionResults`

**Needs workspace**: No — it searches external knowledge bases.

**Available knowledge bases**: `"pubmed_papers"`, `"gene"`, `"disease"`, `"drug"`, `"compound"`, `"target"`, `"pathway"`, `"clinical_trials"`, and more. Pass `None` for the agent to auto-select.

**Special output**: `DeepEvidenceExecutionResults` — extends `ExecutionResults` with evidence graph data. Call `results.export_evidence_graph_html("graph.html")` for interactive visualization.

---

### CoderAgent

**Purpose**: Direct code generation and execution in a sandboxed environment.

```python
from biodsa.agents import CoderAgent

agent = CoderAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

agent.register_workspace("./data")

results = agent.go("Create a bar plot of sample distribution across cancer types")
```

**`go()` signature**: `go(input_query: str, verbose: bool = True) -> ExecutionResults`

**Needs workspace**: Optional — register data files for analysis tasks.

---

### ReactAgent

**Purpose**: General-purpose ReAct agent with tool-calling for multi-step reasoning.

```python
from biodsa.agents import ReactAgent

agent = ReactAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

agent.register_workspace("./data")

results = agent.go("Analyze the mutation patterns in the dataset")
```

**`go()` signature**: `go(input_query: str, verbose: bool = True) -> ExecutionResults`

**Needs workspace**: Optional.

---

### TrialMindSLRAgent

**Purpose**: Systematic literature review with 4-stage workflow (search → screen → extract → synthesize).

```python
from biodsa.agents.trialmind_slr import TrialMindSLRAgent

agent = TrialMindSLRAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

results = agent.go(
    research_question="What is the efficacy of immunotherapy in NSCLC?",
    target_outcomes=["overall survival", "progression-free survival"],
    pico_elements={
        "population": ["NSCLC patients"],
        "intervention": ["immunotherapy", "checkpoint inhibitors"],
        "comparison": ["chemotherapy"],
        "outcome": ["overall survival"],
    },
)
```

**`go()` signature**: `go(research_question: str, target_outcomes: List[str] = None, pico_elements: Dict[str, List[str]] = None, user_eligibility_criteria: List[Dict[str, str]] = None, verbose: bool = True) -> TrialMindSLRExecutionResults`

**Needs workspace**: No.

**Special output**: `TrialMindSLRExecutionResults` — includes `identified_studies`, `included_studies`, and systematic review metadata.

---

### SLRMetaAgent

**Purpose**: Systematic review + meta-analysis with quantitative synthesis and forest plots.

```python
from biodsa.agents import SLRMetaAgent

agent = SLRMetaAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

results = agent.go(
    research_question="What is the efficacy of GLP-1 agonists for weight loss in type 2 diabetes?",
    target_outcomes=["body weight change", "HbA1c reduction"],
)
```

**`go()` signature**: `go(research_question: str, target_outcomes: List[str] = None, verbose: bool = True) -> SLRMetaExecutionResults`

**Needs workspace**: No.

**Special output**: `SLRMetaExecutionResults` — includes `identified_pubmed`, `identified_ctgov`, `included_studies`, `final_report`.

---

### InformGenAgent

**Purpose**: Clinical/regulatory document generation with iterative write-review-revise workflow.

```python
from biodsa.agents.informgen import InformGenAgent

agent = InformGenAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

# Register source documents
agent.register_workspace(workspace_dir="./source_docs")

document_template = [
    {"section_title": "Introduction", "instructions": "Summarize the background..."},
    {"section_title": "Methods", "instructions": "Describe the methodology..."},
    {"section_title": "Results", "instructions": "Present key findings..."},
]

results = agent.go(
    document_template=document_template,
    source_documents=["background.txt", "findings.txt"],
)
```

**`go()` signature**: `go(document_template: List[Dict[str, str]], source_documents: Optional[List[str]] = None, verbose: bool = True) -> InformGenExecutionResults`

**Needs workspace**: Yes — register source documents the agent reads from.

**Special output**: `InformGenExecutionResults` — includes `completed_sections`, `final_document`, token usage stats.

---

### TrialGPTAgent

**Purpose**: Patient-to-clinical-trial matching with retrieval and eligibility scoring.

```python
from biodsa.agents.trialgpt import TrialGPTAgent

agent = TrialGPTAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

patient_note = """
65-year-old male with stage IIIB non-small cell lung cancer.
ECOG performance status 1. No prior immunotherapy.
"""

results = agent.go(patient_note=patient_note)
```

**`go()` signature**: `go(patient_note: str, verbose: bool = True) -> ExecutionResults`

**Needs workspace**: No — searches ClinicalTrials.gov directly.

---

### AgentMD

**Purpose**: Clinical risk prediction using 2,164+ medical calculators.

```python
from biodsa.agents.agentmd import AgentMD

agent = AgentMD(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

results = agent.go(
    patient_note="72F, HTN, DM2, BMI 32, Cr 1.4, presenting with chest pain",
    query="What is the 10-year cardiovascular risk?",
)
```

**`go()` signature**: `go(patient_note: str, query: Optional[str] = None, tool_pmid: Optional[str] = None, verbose: bool = True) -> ExecutionResults`

**Needs workspace**: No.

---

### GeneAgent

**Purpose**: Gene set analysis with self-verification against databases.

```python
from biodsa.agents.geneagent import GeneAgent

agent = GeneAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

results = agent.go(gene_set=["BRCA1", "TP53", "EGFR", "KRAS", "PIK3CA"])
```

**`go()` signature**: `go(gene_set: Union[str, List[str]], verbose: bool = True) -> ExecutionResults`

**Needs workspace**: No.

---

### VirtualLabAgent

**Purpose**: Multi-agent meeting system for AI-powered scientific discussions.

```python
from biodsa.agents import VirtualLabAgent

agent = VirtualLabAgent(
    model_name="gpt-5",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

results = agent.go(
    input_query="Design a CRISPR experiment to study TP53 in lung cancer organoids",
    meeting_type="team",
)
```

**`go()` signature**: `go(input_query: str, previous_results: Optional[Union[ExecutionResults, List[ExecutionResults]]] = None, meeting_type: Literal["team", "individual"] = "individual", **kwargs) -> ExecutionResults`

**Needs workspace**: No.

**Special**: Can chain meetings by passing `previous_results` from prior runs.
