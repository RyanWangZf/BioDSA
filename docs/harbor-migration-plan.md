# Harbor dataset-task migration plan

## Baseline

- Scoring-reliability baseline: `46522017d452c7775c051fe49b2551d792ae7a17`
  on `zifeng/refactor`.
- Execution engine: `harbor==0.23.0` (task schema 1.4).
- BioDSBench source: `zifeng-ai/BioDSBench` revision
  `e59af82ee9461db78ed399544ec8520afeb02ce5`.
- Biomedical Deep Research source: `zifeng-ai/biomedicine-deep-research`
  revision `f3e34ee8ccde8ea15c98f55dae871e63ef8bc5b2`.

Harbor remains the only container, trial, timeout, verifier, and result engine.
This change replaces one-record Harbor tasks with dataset-level tasks. The
agent package is installed once per Harbor trial; a thin batch entrypoint runs
the selected items sequentially with a fresh child process, agent/session, and
workspace for every item. Harbor owns the dataset-level lifecycle, while
per-item status and artifacts live below `/app/submission`.

## Source inventory and task boundaries

The pinned BioDSBench source contains 118 Python records from 13 studies and
165 R records from 25 studies. It becomes two tasks:

- `benchmarks/biodsbench/tasks/biodsbench-python`
- `benchmarks/biodsbench/tasks/biodsbench-r`

Every source record is registered. Python records are runnable; individual
tests that cannot be reproduced through the safe JSON result boundary are
reported as blocked rather than weakened. R records remain included but are
blocked until the migrated agents and execution image support R faithfully.

The pinned Biomedical Deep Research source contains 517 labelled development
records (fit and tune) and 131 verifier records across 13 benchmark subsets.
Each source subset becomes one dataset task. Development and verifier splits
remain explicit in item IDs and manifests; private verifier labels are copied
only into the verifier image. The observed task types are `single_choice`,
`multi_select`, and `evidence_gap_retrieval`.

Coverage manifests record source repository/revision, subset/split, original
record IDs, and source/included/runnable/scorable/blocked counts. Inclusion is
not presented as execution. Missing labels, unsupported runtimes, missing data,
or unsupported assertion semantics remain visible per-item blocking reasons.

## Dataset task contract

Each task contains one Docker environment and one verifier:

```text
<dataset-task>/
  instruction.md
  task.toml
  data/items.jsonl
  data/manifest.json
  environment/Dockerfile
  environment/data/...
  tests/test.sh
  tests/grade.py
  tests/references/...
```

`items.jsonl` contains only public instructions, permitted code history, and
input paths. References and hidden tests exist only in the verifier build
context. Large BioDSBench tables are downloaded once into the pinned cache and
staged by a purpose-specific preparation script; no general builder API is
introduced.

The batch entrypoint writes `predictions.jsonl` after every item and item
artifacts below `items/<item-id>/`. It uses a process group per item so timeout
or cancellation terminates generated child processes before the next item.
Conversation, workflow memory, and writable files are never reused across
items. Read-only source data and API client construction may be reused. This is
process/session/workspace isolation inside one task container, not a separate
container security boundary for each item.

## Selection, budgets, and scoring

Full jobs reference every dataset task and have no item limit. Smoke jobs pass
a fixed item-ID list to both the agent options and verifier environment. The
verifier treats its trusted selection as the denominator and rejects duplicate
or unknown prediction IDs; an absent prediction remains `missing`.

Per-item timeout/model/tool budgets are agent options. The Harbor agent timeout
covers the complete dataset trial, including package setup and artifact writes.
Verifier timeout covers the full selected dataset and is sized separately.

Dataset graders write `per_item_results.jsonl`, `summary.json`, and Harbor's
reward file. Summaries report total, attempted, completed, scored, missing,
timeout, agent_error, grading_error, and unscorable. Metrics are marked partial
unless the trusted selection is completely scoreable and free of grading
errors.

BioDSBench submissions execute as an unprivileged process with time/resource
limits and a JSON-only result export. That process cannot read verifier
references/tests or write the Harbor reward. A pinned mapping covers the
actual scalar, DataFrame, Series, ndarray, collection, finite predicate, and
model-attribute operations used by all 118 Python records. The trusted grader
applies the source checks and requires all assertions to pass. It never imports
submitted code, pickle, or another executable serialization.

Deep Research grading follows each source answer form. Single choice accepts
exactly one valid option; multi-select uses source set exact-match with no
partial credit and rejects duplicates. Evidence-gap retrieval has PMID targets
but no metric or ranking semantics in the pinned source, so its 20 records are
explicitly unscorable. No semantic judge is invented.

## Files replaced

- Delete the four BioDSBench and four Deep Research record-level task dirs.
- Replace hard-coded four-record staging with one pinned, source-specific
  preparation script.
- Replace `dswizard-mix.yaml` and `deepevidence-mix.yaml` with full/smoke jobs.
- Extend Coder, DSWizard, and DeepEvidence Harbor adapters with the dataset
  batch contract; retain their workflow implementations.
- Keep fixture tasks and agent integration tests as focused regressions.

## Implementation status

- [x] Inspect HEAD, Harbor 0.23 types, pinned source files, configs, and splits.
- [x] Record complete source counts and dataset-level boundaries.
- [x] Materialize public inventories, private references, and coverage manifests.
- [x] Implement isolated per-item batch runners and selection propagation.
- [x] Implement trusted dataset graders and BioDSBench execution isolation.
- [x] Add full/smoke native Harbor jobs.
- [x] Run unit/config checks and real Docker Harbor batch smoke.
- [x] Delete replaced record-level tasks/scripts; update README and coverage report.

## Scoring repair implementation and validation

The DeepEvidence two-item HLE smoke completed as one real Docker Harbor trial:
both item processes completed, the trusted denominator was two, and the
deterministic mock scored 1/2 (accuracy 0.5). This demonstrates batch artifact
collection and verifier aggregation; it is not a claim that the full 648-item
suite ran.

The BioDSBench verifier now scores real results instead of returning a fixed
zero. The full verifier-only oracle used the same non-root replay and JSON
boundary as agent submissions. It verified 112 of 118 references. Six source
references fail in their own implementation: four items read gene-oriented
tables as though genes were columns (`28481359_4`, `_5`, `_7`, `_8`), one uses
`pd` without importing pandas (`28472509_4`), and one Plotly reference cannot
start Chromium after verifier privilege dropping (`37699004_1`). These remain
concrete oracle failures; their scoring mappings are retained because a valid
agent implementation can still satisfy the source assertions. Negative checks
cover wrong values, columns, shapes, and missing variables through the same
boundary.

Deep Research was recounted directly from the fixed revision: fit 388, tune
129, verifier 131, with disjoint IDs. Across all splits there are 367
single-choice, 261 multi-select, and 20 evidence-gap retrieval records. Standard
submissions passed the real parser and grader for all 628 scoreable choice
records across all 13 task images. The 20 retrieval records produced the
expected incomplete-evaluation status and no reward. Dedicated fit, tune, and
verifier jobs propagate the split to both agent and trusted verifier; the full
job is inventory-wide and reports each split separately.
The pre-existing Coder analysis fixture also passed through the new entrypoint
in Docker with reward 1.0, confirming that focused non-dataset Harbor smokes
remain usable while dataset tasks take the batch path.

The complete paid/API-backed full jobs are prepared but are not run
automatically. Validation uses fixed smoke selections and distinguishes source
inclusion, runnable/scorable status, and items actually executed.
