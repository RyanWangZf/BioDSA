# Harbor dataset-task migration plan

## Baseline

- Implementation baseline: `039af0827ce5e22625e1f59240ec50335651ed4e`
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
references/tests or write the Harbor reward. The trusted grader evaluates the
exported values against source assertions. It never imports submitted pickle
or other executable serialized objects. Deep Research grading follows the
source answer form; deterministic labelled choice/retrieval items are scored
without inventing an LLM judge.

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

## Validation in progress

The DeepEvidence two-item HLE smoke completed as one real Docker Harbor trial:
both item processes completed, the trusted denominator was two, and the
deterministic mock scored 1/2 (accuracy 0.5). This demonstrates batch artifact
collection and verifier aggregation; it is not a claim that the full 648-item
suite ran.

The DSWizard two-item BioDSBench smoke also completed as one Docker trial after
the pinned public tables were staged. Both independent item processes completed
and emitted plans/code/artifacts. Both are reported as `unscorable`, with a null
accuracy and reward 0, because safe conversion of their source assertions is an
explicit blocker. A verifier regression confirmed correct/partial/missing
denominators of 2 with accuracies 1.0/0.5/0.0. A malicious submitted program
could neither read root-only references nor overwrite the final reward.
The pre-existing Coder analysis fixture also passed through the new entrypoint
in Docker with reward 1.0, confirming that focused non-dataset Harbor smokes
remain usable while dataset tasks take the batch path.

The complete paid/API-backed full jobs are prepared but are not run
automatically. Validation uses fixed smoke selections and distinguishes source
inclusion, runnable/scorable status, and items actually executed.
