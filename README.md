# BioAgent Gym

BioAgent Gym is a repository of independently installable biomedical agents and
native [Harbor](https://github.com/harbor-framework/harbor) leaderboards.
Harbor 0.23.0 owns Docker environments, trials, timeouts, verification, and
result storage. This repository supplies agents, dataset tasks, scoring code,
and native job YAML.

## Choose an agent

The supported catalog is [agents/README.md](agents/README.md). Install only the
shared item runner and the agent you intend to use:

```bash
python3.12 -m venv .venv-harbor
.venv-harbor/bin/pip install -e . -e runner -e 'agents/dswizard[harbor]'
.venv-harbor/bin/pip install -e 'agents/deepevidence[harbor]'
```

Coder, DSWizard, and DeepEvidence are separate distributions. Their wheels own
only their agent namespace; `bioagent-harbor-runtime` is a separate lightweight
distribution.

## Choose a leaderboard

The current leaderboard catalog is [benchmarks/README.md](benchmarks/README.md):

- [BioDSBench](benchmarks/biodsbench/README.md)
- [Biomedical Deep Research](benchmarks/biomedicine-deep-research/README.md)

Each benchmark directory contains its tasks, jobs, scoring source, preparation
script, and tests. Prepare pinned data once:

```bash
.venv-harbor/bin/python benchmarks/biodsbench/prepare.py
.venv-harbor/bin/python benchmarks/biomedicine-deep-research/prepare.py
```

Preparation writes public items, private verifier references, large external
inputs, and grader deployment copies. It never rewrites committed
`task.toml`, Dockerfiles, instructions, or job YAML.

Run deterministic smoke jobs:

```bash
ROOT="$(pwd)"
.venv-harbor/bin/harbor run \
  -c benchmarks/biodsbench/jobs/dswizard-smoke.yaml \
  --jobs-dir "$ROOT/.harbor/jobs" -y

.venv-harbor/bin/harbor run \
  -c benchmarks/biomedicine-deep-research/jobs/deepevidence-smoke.yaml \
  --jobs-dir "$ROOT/.harbor/jobs" -y
```

Run the formal leaderboard configurations with the required provider secret:

```bash
.venv-harbor/bin/harbor run \
  -c benchmarks/biodsbench/jobs/dswizard.yaml --env-file .env \
  --jobs-dir "$ROOT/.harbor/jobs" -y

.venv-harbor/bin/harbor run \
  -c benchmarks/biomedicine-deep-research/jobs/deepevidence.yaml --env-file .env \
  --jobs-dir "$ROOT/.harbor/jobs" -y

.venv-harbor/bin/python benchmarks/biomedicine-deep-research/summarize.py \
  "$ROOT/.harbor/jobs/<deepevidence-job-directory>"
```

BioDSBench ranks the 118-item Python task; R remains inventoried but unsupported.
Biomedical Deep Research ranks scoreable verifier-split choice items. Fit and
tune are development jobs. The diagnostic job covers the complete inventory,
including evidence-gap records whose pinned source defines no metric.

Use `harbor view .harbor/jobs` to inspect submissions, item artifacts, verifier
logs, and rewards. See [architecture.md](docs/architecture.md),
[adding-agents.md](docs/adding-agents.md), and
[adding-benchmarks.md](docs/adding-benchmarks.md). Historical code is isolated
under [legacy/](legacy/README.md).
