# BioAgent Gym file protocol 1.0

Implementations communicate using UTF-8 JSON files. The common envelopes live
in [`schemas/1.0`](schemas/1.0); a benchmark supplies schemas for each task
type's `input` and `output` payload.

An agent command has this shape:

```bash
agent-command --request request.json --output-dir output [--config agent.json]
```

It must atomically publish `output/result.json`. Files named in `artifacts` are
relative to `output`, must exist, and may not traverse or symlink outside it.
`completed` describes execution only. Omit unavailable usage values rather than
writing zero. Credentials are environment variables, never protocol fields.

A benchmark prepare command emits `manifest.json`, `tasks.jsonl`, optional
public `assets/`, and evaluator-only `private/`. A benchmark evaluate command
accepts `--request evaluation-request.json --output-dir evaluation-dir` and
atomically publishes `evaluation-dir/result.json`.

`TaskSpec` is static prepared data. The harness creates `TaskRequest` at run
time by adding `run_id`, `attempt_id`, budget, seed, and resolved public assets.
Private paths are only included in `EvaluationRequest`.

Prepared manifests declare either one `split` plus `tasks_file`, or a `splits`
mapping with one task file per split. The harness checks protocol, benchmark,
benchmark version, requested split, and an explicitly requested data revision
before starting an agent. All prepared file locations are contained relative
paths.

New runs snapshot the resolved experiment, agent config value, manifests,
prepared metadata, and selected TaskSpecs under `context/`. Small references are
copied into `context/evaluator/`; large references remain versioned external
paths. Neither location is exposed to the agent. Every scoring pass creates a
new `evaluations/<evaluation_id>/` tree and preserves earlier results. Legacy
runs without context snapshots remain readable with an explicit warning.

Version declarations and snapshots are the reproducibility boundary. BioAgent
Gym does not scan or hash all dataset content on every run, so it cannot detect
an external file changed in place without a corresponding version change.

Manifests are documented in [`manifests.md`](manifests.md). Protocol objects
have an explicit `extensions` object; unknown common fields are rejected.
