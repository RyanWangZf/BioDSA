# BioAgent Gym

BioAgent Gym maintains biomedical agents and ready-to-run native
[Harbor](https://github.com/harbor-framework/harbor) tasks. Harbor is the only
trial engine: it builds environments, runs agents, enforces timeouts, invokes
verifiers, and stores submissions, logs, and rewards.

This revision is fixed to `harbor==0.23.0` and Python 3.12+. Docker is required
for the examples.

## Install

Create an environment and install Harbor plus the agents you want to run:

```bash
python3.12 -m venv .venv-harbor
.venv-harbor/bin/pip install -e .
.venv-harbor/bin/pip install -e 'agents/fixture_agent[harbor]'
.venv-harbor/bin/pip install -e 'agents/coder[harbor]'
.venv-harbor/bin/pip install -e 'agents/dswizard[harbor]'
.venv-harbor/bin/pip install -e 'agents/deepevidence[harbor]'
```

The agents are separate distributions. The repository package installs Harbor;
it does not install agent model frameworks or a second runner.

Use an absolute Harbor results directory with 0.23.0. This avoids a Docker
Compose path-resolution issue when a relative results directory is interpreted
from a task build context.

## Deterministic smoke

```bash
ROOT="$(pwd)"
.venv-harbor/bin/harbor run \
  -c experiments/fixture-smoke.yaml \
  --jobs-dir "$ROOT/.harbor/jobs" -y

.venv-harbor/bin/harbor run \
  --path "$ROOT/benchmarks/fixtures/tasks/analysis-smoke" \
  --agent bioagent_coder.harbor_agent:CoderHarborAgent \
  --ak provider=mock --ak timeout_seconds=30 \
  --jobs-dir "$ROOT/.harbor/jobs" --job-name coder-mock -y

.venv-harbor/bin/harbor run \
  --path "$ROOT/benchmarks/fixtures/tasks/analysis-smoke" \
  --agent bioagent_dswizard.harbor_agent:DSWizardHarborAgent \
  --ak provider=mock --ak timeout_seconds=30 \
  --jobs-dir "$ROOT/.harbor/jobs" --job-name dswizard-mock -y

.venv-harbor/bin/harbor run \
  --path "$ROOT/benchmarks/fixtures/tasks/evidence-smoke" \
  --agent bioagent_deepevidence.harbor_agent:DeepEvidenceHarborAgent \
  --ak provider=mock --ak tool_mode=stub \
  --ak 'knowledge_bases=["pubmed_papers","clinical_trials"]' \
  --ak 'routes=["bfs","dfs"]' --ak code_execution=true \
  --jobs-dir "$ROOT/.harbor/jobs" --job-name deepevidence-mock -y
```

Mocking replaces model/API responses only. The actual agent workflow, generated
Python process, task-local files, Harbor container, artifact transfer, and
verifier all run.

## DSWizard BioDSBench datasets

Prepare the pinned source inventories and public tables once. Small inventories
are committed; large tables and verifier-only references remain outside Git:

```bash
.venv-harbor/bin/python scripts/prepare_harbor_dataset_tasks.py
```

Run a fixed two-item mock smoke, or the full Python and R task set:

```bash
ROOT="$(pwd)"
.venv-harbor/bin/harbor run \
  -c experiments/dswizard-smoke.yaml \
  --jobs-dir "$ROOT/.harbor/jobs" -y

.venv-harbor/bin/harbor run \
  -c experiments/dswizard-full.yaml --env-file .env \
  --jobs-dir "$ROOT/.harbor/jobs" -y
```

The two Harbor tasks contain all 118 Python and 165 R source records. All 118
Python records have real assertion-based scoring through an isolated JSON
result boundary. The verifier-only reference check passes 112; six source
reference implementations fail for the concrete reasons recorded in the task
manifest. R execution remains unsupported and unchanged.

## DeepEvidence biomedical research mix

```bash
ROOT="$(pwd)"
.venv-harbor/bin/harbor run \
  -c experiments/deepevidence-smoke.yaml \
  --jobs-dir "$ROOT/.harbor/jobs" -y

.venv-harbor/bin/harbor run \
  -c experiments/deepevidence-verifier.yaml --env-file .env \
  --jobs-dir "$ROOT/.harbor/jobs" -y
```

Use `deepevidence-fit.yaml` and `deepevidence-tune.yaml` for development. The
formal configuration is `deepevidence-verifier.yaml`; it selects only the 131
verifier records. `deepevidence-full.yaml` is an inventory-wide diagnostic over
all 648 records and reports fit/tune/verifier separately. Labels are present
only in separate offline verifier images. The 20 evidence-gap records remain
explicitly unscorable because the pinned source does not define a retrieval
metric.

Recreate the verifier-only standard submissions and run every grader image:

```bash
scripts/verify_grader_oracles.sh
```

Each Harbor trial installs the agent once, then runs selected items in fresh
child processes and workspaces. Per-item retry/scheduling remains inside the
batch artifacts rather than Harbor trials. Edit the `tasks` list in native
Harbor YAML to change a static mix. No
prepare, export, or config compiler command is required.

Coder, DSWizard, and DeepEvidence package the same small
`bioagent_harbor_runtime` implementation for item selection, process-group
timeouts, workspace layout, incremental predictions, and continue-after-error
behavior. It imports no agent framework and does not manage Docker or scoring.
Benchmark grader sources remain under `scripts/`; dataset preparation places
deployment copies into each Harbor 0.23 verifier context with private labels.

## Results and adding tasks

Harbor writes one directory per job and trial. Inspect `result.json`, the
trial's `artifacts/`, `agent/`, `verifier/`, and `trial.log`, or run:

```bash
.venv-harbor/bin/harbor view .harbor/jobs
```

A new task needs `instruction.md`, `task.toml`, `environment/Dockerfile`, and
`tests/test.sh`; add `solution/solve.sh` when a reference implementation exists.
The verifier must evaluate the actual submission and write
`/logs/verifier/reward.txt` or `reward.json`.

Agent and task environment network policy is declared in `task.toml`. Real
agent tasks use `public`; deterministic fixtures use `no-network`. Image builds
and external data preparation are separate from runtime network policy. Harbor's
single task container cannot represent online-agent/offline-generated-code as
two independent boundaries; this repository does not silently weaken that
unsupported topology.

See [the migration record](docs/harbor-migration-plan.md) for pinned dataset
revisions, task provenance, design choices, and validation results.
