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

Manifests are documented in [`manifests.md`](manifests.md). Protocol objects
have an explicit `extensions` object; unknown common fields are rejected.
