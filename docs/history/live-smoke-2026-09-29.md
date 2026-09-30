# Bounded live smoke — 2026-09-29

These runs used Harbor 0.23.0, `qwen/qwen3.8-flash` through the configured
OpenRouter endpoint, Docker task environments, and the committed `*-live-smoke`
jobs. They are integration diagnostics, not leaderboard results.

## BioDSBench Python

Both agents ran `28481359_0` and `29713087_1`; the latter includes
`import numpy as np` source code history. Both used the same task image,
selection, tables, and verifier.

| Agent | Completed workflow | Scored correct | Observed failures |
|---|---:|---:|---|
| Coder | 1/2 | 0/2 | one submitted program did not define the expected `df_exp`; one candidate failed on an input column lookup |
| DSWizard | 0/2 | 0/2 | one implementation failed during pandas output construction; one exploration omitted the pandas import |

Candidate code, plans, execution results, and structured failures are retained
under each failed item's submission artifacts. For the code-history item, the
saved candidate program starts with the source `import numpy as np`, confirming
that agent execution and verifier replay use the same submitted program.

## Biomedical Deep Research

Two fit items each from HLE Biomedicine, MoA Pathway Reasoning, and Evidence Gap
Discovery completed the full Harbor and verifier path. Choice accuracy was 0/2
for both choice subsets. Evidence retrieval returned 10 and 30 model-selected
PMIDs: the first hit 0/162 references and the second hit 3/12, producing
per-item recall@30 values 0 and 0.25 and a subset mean of 0.125.

The retrieval traces contain model-authored BFS/DFS PubMed queries, tool result
counts, raw synthesis output, final submitted PMID order, and verifier hits.
The query for the second retrieval item obtained 30 results on each route; the
model-selected list exactly matches the saved `BIOMED_FINAL` submission.

An earlier attempt encountered OpenRouter HTTP 429 responses and verbose,
truncated final output. Those failures were retained as agent errors. The final
prompt requests only the required structured final block; the bounded rerun
completed all six items without agent or grading errors.

## Commands

```bash
harbor run -c benchmarks/biodsbench/jobs/dswizard-live-smoke.yaml --env-file .env -y
harbor run -c benchmarks/biodsbench/jobs/coder-live-smoke.yaml --env-file .env -y
harbor run -c benchmarks/biomedicine-deep-research/jobs/deepevidence-live-smoke.yaml --env-file .env -y
```
