# AgentMD: Clinical Risk Prediction Agent

AgentMD is an LLM-based autonomous agent for clinical risk prediction using a large-scale toolkit of clinical calculators (RiskCalcs).

## Overview

AgentMD empowers language models to:
1. **Curate** clinical calculators from medical literature (Tool Maker)
2. **Apply** relevant calculators to patient data (Tool User)
3. **Interpret** results with clinical context

This implementation is based on the research paper:

> Jin, Q., Wang, Z., Yang, Y., et al. (2024). AgentMD: Empowering Language Agents for Risk Prediction with Large-Scale Clinical Tool Learning. arXiv:2402.13225

## Features

- **Risk Triage**: Automatically identifies relevant risk categories from patient presentations
- **Calculator Retrieval**: Semantic search over clinical calculators using embeddings
- **Calculator Selection**: LLM-guided selection of appropriate tools
- **Risk Computation**: Safe execution of calculator code with patient data
- **Result Interpretation**: Clinical contextualization of calculated risks

## Installation

AgentMD is part of the BioDSA package. Ensure you have the required dependencies:

```bash
pip install langchain langchain-openai langgraph pydantic
# For semantic search (optional but recommended)
pip install sentence-transformers faiss-cpu
```

## Quick Start

```python
from biodsa.agents.agentmd import AgentMD

# Initialize the agent
agent = AgentMD(
    model_name="gpt-4o",
    api_type="azure",  # or "openai"
    api_key="your-api-key",
    endpoint="your-endpoint"
)

# Patient clinical note
patient_note = """
65-year-old male presenting with acute chest pain for the past 2 hours.
History: Hypertension, Type 2 Diabetes, former smoker.
Vitals: BP 145/90, HR 88, RR 18, SpO2 98% on room air.
ECG: ST depression in leads V4-V6.
Labs: Troponin I 0.08 ng/mL (elevated), BUN 22 mg/dL, Cr 1.1 mg/dL.
"""

# Run risk assessment
results = agent.go(patient_note)
print(results.final_response)
```

## Available Calculators

The built-in calculator library includes:

### Cardiovascular
- **HEART Score**: Risk stratification for chest pain (MACE prediction)
- **CHA2DS2-VASc**: Stroke risk in atrial fibrillation
- **Wells' PE Criteria**: Pulmonary embolism probability

### Mortality/Severity
- **qSOFA**: Sepsis screening
- **CURB-65**: Pneumonia severity
- **MELD**: Liver disease severity

### Renal
- **eGFR (CKD-EPI 2021)**: Kidney function estimation

### Bleeding
- **HAS-BLED**: Bleeding risk with anticoagulation

## Custom Calculators

You can extend the calculator library:

```python
from biodsa.tools.risk_calculators import Calculator, COMMON_CALCULATORS

# Define a new calculator
my_calculator = Calculator(
    id="my_calc",
    name="My Custom Calculator",
    category="custom",
    purpose="Description of what it does",
    variables=[
        {"name": "var1", "type": "float", "description": "..."},
        {"name": "var2", "type": "bool", "description": "..."},
    ],
    formula='''
def calculate_my_calc(var1, var2):
    # Your calculation logic
    result = var1 * 2 if var2 else var1
    return {"score": result}
''',
    interpretation={
        "<10": "Low risk",
        ">=10": "High risk"
    },
    reference="Citation here"
)

# Add to library
COMMON_CALCULATORS["my_calc"] = my_calculator
```

## RiskQA Benchmark

AgentMD can be evaluated on the RiskQA benchmark:

```python
# Evaluate on a RiskQA question
result = agent.evaluate_riskqa(
    question="A 55-year-old woman with new-onset atrial fibrillation...",
    choices={
        "A": "No anticoagulation needed",
        "B": "Low stroke risk",
        "C": "Moderate stroke risk",
        "D": "High stroke risk"
    },
    calculator_code=CHA2DS2_VASC_CODE
)

print(f"Answer: {result['answer']}")
print(f"Reasoning: {result['reasoning']}")
```

## Workflow Architecture

```
Patient Note
     │
     ▼
┌─────────────┐
│ Risk Triage │  → Identify relevant risk categories
└─────────────┘
     │
     ▼
┌───────────────────┐
│ Calculator Search │  → Retrieve relevant calculators
└───────────────────┘
     │
     ▼
┌─────────────────────┐
│ Calculator Selection│  → Choose best calculator(s)
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ Risk Computation    │  → Execute with patient data
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ Result Summary      │  → Clinical interpretation
└─────────────────────┘
```

## Tools

AgentMD uses the following tools:

| Tool | Description |
|------|-------------|
| `search_calculators` | Semantic search for relevant calculators |
| `get_calculator_details` | Get full calculator specification |
| `run_calculator` | Execute a calculator with inputs |
| `execute_calculation` | Run custom Python code |
| `list_calculators` | List all available calculators |

## Disclaimer

**Important**: AgentMD is a clinical decision SUPPORT tool for research purposes. It is NOT intended for:
- Direct diagnostic use
- Medical decision-making without physician oversight
- Replacement of clinical judgment

Always consult qualified healthcare professionals for medical decisions.

## Citation

```bibtex
@article{jin2025agentmd,
  title={Agentmd: Empowering language agents for risk prediction with large-scale clinical tool learning},
  author={Jin, Qiao and Wang, Zhizheng and Yang, Yifan and Zhu, Qingqing and Wright, Donald and Huang, Thomas and Khandekar, Nikhil and Wan, Nicholas and Ai, Xuguang and Wilbur, W John and others},
  journal={Nature Communications},
  volume={16},
  number={1},
  pages={9377},
  year={2025},
  publisher={Nature Publishing Group UK London}
}
```

## License

This implementation follows the licensing of the BioDSA project.
