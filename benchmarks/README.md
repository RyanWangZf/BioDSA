# BioDSA Benchmarks

This directory contains benchmark datasets for evaluating biomedical data science agents. The benchmarks cover a range of tasks from data analysis coding to literature research and evidence synthesis.

## Overview

| Benchmark | Type | # Tasks | Description |
|-----------|------|---------|-------------|
| [BioDSA-1K](#biodsa-1k) | Hypothesis Validation | 1,029 | Real biomedical hypothesis validation from published studies |
| [BioDSBench-Python](#biodsbench-python) | Code Generation | 128 | Python coding tasks for biomedical data analysis |
| [BioDSBench-R](#biodsbench-r) | Code Generation | 165 | R coding tasks for biomedical data analysis |
| [DeepEvidence](#deepevidence) | Evidence Synthesis | Multiple | Knowledge graph research and evidence gap analysis |
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

Comprehensive benchmark for evidence synthesis and knowledge graph research tasks, including:

- **Cohort**: Cohort optimization for clinical trial design
- **Criteria**: Safety exclusion criteria generation
- **Dose**: Drug regimen design
- **DrugDiscovery**: Target identification and preclinical research QA
- **DrugRepurposing**: Drug repurposing candidate identification
- **Endpoint**: Surrogate endpoint selection
- **Evidence**: Evidence gap analysis and synthesis from Cochrane reviews
- **SampleSize**: Sample size estimation

**Structure**:
```
DeepEvidence/
├── Cohort/
│   └── cohort_optimization_tasks.jsonl
├── Criteria/
│   └── safety_exclusion_criteria_tasks.jsonl
├── Dose/
│   └── drug_regimen_design_tasks.jsonl
├── DrugDiscovery/
│   ├── target_identification_all.jsonl
│   ├── preclinical_research_all.jsonl
│   └── in_vivo_flux_response_all.jsonl
├── Endpoint/
│   └── surrogate_endpoint_tasks.jsonl
├── Evidence/
│   ├── evidence_gap_20.csv
│   └── evidence_synthesis_42.csv
├── SampleSize/
│   └── sample_size_estimation_25.csv
└── data_processing/
    └── [task generation scripts]
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

