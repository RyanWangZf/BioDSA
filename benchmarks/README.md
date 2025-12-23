# BioDSA Benchmarks

This directory contains benchmark datasets for evaluating biomedical data science agents. The benchmarks cover a range of tasks from data analysis coding to literature research and evidence synthesis.

## Overview

| Benchmark | Type | # Tasks | Description |
|-----------|------|---------|-------------|
| [BioDSA-1K](#biodsa-1k) | Hypothesis Validation | 1,029 | Real biomedical hypothesis validation from published studies |
| [BioDSBench-Python](#biodsbench-python) | Code Generation | 128 | Python coding tasks for biomedical data analysis |
| [BioDSBench-R](#biodsbench-r) | Code Generation | 165 | R coding tasks for biomedical data analysis |
| [DeepEvidence](#deepevidence) | Deep Research | 7 tasks | Deep knowledge graph research for biomedical discovery |
| [HLE-Biomedicine](#hle-biomedicine) | Reasoning | 102 | Hard biomedicine questions from Humanity's Last Exam |
| [HLE-Medicine](#hle-medicine) | Reasoning | 30 | Hard medicine questions from Humanity's Last Exam |
| [LabBench](#labbench) | Literature QA | 75 | Literature and database question answering |
| [SuperGPQA](#supergpqa) | Expert QA | 264 | Expert-level biology and medicine questions |
| [TrialGPT](#trialgpt) | Clinical Trials | Varies | Clinical trial matching and analysis |
| [TrialPanoramaBench](#trialpanoramabench) | Evidence Synthesis | 50+ | Sample size estimation and evidence synthesis |
| [TRQA-lit](#trqa-lit) | Literature QA | 172 | Translational research question answering |

---

## BioDSA-1K

**Location**: `BioDSA-1K/`

1,029 hypothesis validation tasks derived from real biomedical studies. Each task includes a hypothesis statement, supporting evidence, data tables, analysis plan, and ground truth labels.

📄 **Paper**: [BioDSA-1K: Benchmarking Data Science Agents for Biomedical Research](https://arxiv.org/abs/2505.16100)

🤗 **Full Dataset**: [HuggingFace - zifeng-ai/BioDSA-1K](https://huggingface.co/datasets/zifeng-ai/BioDSA-1K)

**Structure**:
```
BioDSA-1K/
├── dataset/
│   └── biodsa_1k_hypothesis.parquet
└── README.md
```

---

## BioDSBench-Python

**Location**: `BioDSBench-Python/`

128 Python coding tasks for biomedical data analysis, including data preprocessing, statistical analysis, and visualization.

📄 **Paper**: [Can Large Language Models Replace Data Scientists in Biomedical Research?](https://arxiv.org/abs/2410.21591)

🤗 **Full Dataset**: [HuggingFace - zifeng-ai/BioDSBench](https://huggingface.co/datasets/zifeng-ai/BioDSBench)

**Structure**:
```
BioDSBench-Python/
├── dataset/
│   ├── python_tasks_with_class.jsonl
│   └── python_task_table_schemas.jsonl
└── README.md
```

---

## BioDSBench-R

**Location**: `BioDSBench-R/`

165 R coding tasks for biomedical data analysis with similar task types to BioDSBench-Python.

🤗 **Full Dataset**: [HuggingFace - zifeng-ai/BioDSBench](https://huggingface.co/datasets/zifeng-ai/BioDSBench)

**Structure**:
```
BioDSBench-R/
├── dataset/
│   ├── R_tasks_with_class.jsonl
│   └── R_task_table_schemas.jsonl
└── README.md
```

---

## DeepEvidence

**Location**: `DeepEvidence/`

Comprehensive benchmark for deep knowledge graph research tasks spanning the biomedical discovery pipeline. Each task requires agents to search and synthesize evidence from multiple biomedical knowledge bases.

📄 **Paper**: DeepEvidence: Empowering Biomedical Discovery with Deep Knowledge Graph Research (In submission)

🤗 **Full Dataset**: [HuggingFace - zifeng-ai/DeepEvidence](https://huggingface.co/datasets/zifeng-ai/DeepEvidence)

**Task Types**:

| Task | File | Description |
|------|------|-------------|
| Target Identification | `target_identification.parquet` | Identify therapeutic targets for diseases |
| MoA Pathway Reasoning | `moa_pathway_reasoning.parquet` | Reason about drug mechanism of action pathways |
| In Vivo Metabolic Flux Response | `in_vivo_metabolic_flux_response.parquet` | Predict metabolic responses in preclinical models |
| Drug Regimen Design | `drug_regimen_design.parquet` | Design drug dosing regimens based on safety data |
| Surrogate Endpoint Discovery | `surrogate_endpoint_discovery.parquet` | Identify surrogate endpoints for clinical trials |
| Sample Size Estimation | `sample_size_estimation.parquet` | Estimate required sample sizes for trials |
| Evidence Gap Discovery | `evidence_gap_discovery.parquet` | Identify gaps in existing clinical evidence |

**Dataset Structure** (HuggingFace):
```
DeepEvidence/
├── target_identification.parquet
├── moa_pathway_reasoning.parquet
├── in_vivo_metabolic_flux_response.parquet
├── drug_regimen_design.parquet
├── surrogate_endpoint_discovery.parquet
├── sample_size_estimation.parquet
└── evidence_gap_discovery.parquet
```

---

## HLE-Biomedicine

**Location**: `HLE-biomedicine/`

102 hard biomedicine questions from [Humanity's Last Exam](https://lastexam.ai/), filtered for questions that don't require images.

**Files**:
- `hle_biomedicine_40.csv` - 40 selected biomedicine questions
- `hle_biomedicine_62.csv` - 62 selected biomedicine questions
- `hle_raw_no_image.csv` - All non-image biomedicine questions

---

## HLE-Medicine

**Location**: `HLE-medicine/`

30 hard medicine questions from Humanity's Last Exam.

**Files**:
- `hle_medicine_30.csv` - 30 selected medicine questions

---

## LabBench

**Location**: `LabBench/`

Literature and database question answering benchmark.

**Files**:
- `LitQA2_25.csv` - 25 literature QA questions
- `DBQA_50.csv` - 50 database QA questions

---

## SuperGPQA

**Location**: `SuperGPQA/`

Expert-level graduate and professional level questions in biology and medicine from [SuperGPQA](https://huggingface.co/datasets/m-a-p/SuperGPQA).

**Files**:
- `SuperGPQA-hard-biology-92.csv` - 92 hard biology questions
- `SuperGPQA-hard-medicine-172.csv` - 172 hard medicine questions
- `SuperGPQA-all.jsonl` - All questions

---

## TrialGPT

**Location**: `TrialGPT/`

Clinical trial matching benchmark.

**Files**:
- `trialgpt_raw.csv` - Full TrialGPT dataset
- `trialgpt_raw_sampled.csv` - Sampled subset

---

## TrialPanoramaBench

**Location**: `TrialPanoramaBench/`

Benchmark for clinical trial design tasks.

**Files**:
- `evidence_synthesis_50.csv` - 50 evidence synthesis tasks
- `sample_size_estimation.jsonl` - Sample size estimation tasks

---

## TRQA-lit

**Location**: `TRQA-lit/`

Translational research question answering based on literature.

**Files**:
- `TRQA-lit-choice-172.csv` - 172 multiple-choice questions
- `TRQA-lit-choice-coreset.csv` - Core subset

---

## Usage

### Loading Parquet Files

```python
import pandas as pd

# BioDSA-1K
df = pd.read_parquet("BioDSA-1K/dataset/biodsa_1k_hypothesis.parquet")
```

### Loading JSONL Files

```python
import json

tasks = []
with open("BioDSBench-Python/dataset/python_tasks_with_class.jsonl") as f:
    for line in f:
        tasks.append(json.loads(line))
```

### Loading CSV Files

```python
import pandas as pd

df = pd.read_csv("SuperGPQA/SuperGPQA-hard-biology-92.csv")
```

---

## Citation

If you use these benchmarks, please cite the relevant papers:

```bibtex
@article{wang2025biodsa1k,
  title={BioDSA-1K: Benchmarking Data Science Agents for Biomedical Research},
  author={Wang, Zifeng and Danek, Benjamin and Sun, Jimeng},
  journal={arXiv preprint arXiv:2505.16100},
  year={2025}
}

@article{wang2024llm,
  title={Can Large Language Models Replace Data Scientists in Biomedical Research?},
  author={Wang, Zifeng and Danek, Benjamin and Yang, Ziwei and Chen, Zheng and Sun, Jimeng},
  journal={arXiv preprint arXiv:2410.21591},
  year={2024}
}
```

