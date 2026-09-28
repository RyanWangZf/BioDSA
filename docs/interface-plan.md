# BioAgent Gym interface refactor: phase 1 plan

Status: implemented (phase 1)

## Scope and invariants

This phase adds a small, dependency-light execution plane beside the existing
`biodsa` package. Existing agents and their algorithms are not migrated. The
new harness never imports agent, prepare, or evaluator implementations. It
discovers YAML manifests and communicates with each implementation through
versioned JSON files and argv-based commands.

The boundary is deliberately process-shaped:

1. A benchmark prepare command emits a prepared dataset (`manifest.json`,
   `tasks.jsonl`, public `assets/`, and evaluator-only `private/`).
2. The harness turns each static `TaskSpec` into a runtime `TaskRequest`, adds
   run/attempt identity, budget, seed, and resolved public assets, and launches
   one agent process per task.
3. The agent atomically writes `result.json`; the harness validates the common
   result schema, the task-type output schema, identity fields, and artifact
   containment.
4. Evaluation is a separate process. It receives an `EvaluationRequest` that
   points to the validated agent result/artifacts and private reference. It
   writes an `EvaluationResult`, which the harness validates and aggregates.

`completed` means the agent process produced a valid result, not that its answer
was correct. A missing `usage` remains unknown. Secrets are named in manifests
but are only inherited from the environment; their values are never copied to
requests, resolved configuration, or run records.

## Repository layout

```text
protocol/                    JSON Schemas, examples, and protocol documentation
harness/                     stdlib-oriented CLI and orchestration package
agents/fixture_agent/        deterministic standalone fixture project
benchmarks/fixture_qa/       standalone prepare/evaluate fixture project
experiments/                 runnable experiment examples
tests/harness/               protocol, process, timeout, and end-to-end tests
```

The installable distribution, renamed to `bioagent-gym`, contains only the
`bioagent_gym` harness and protocol data; it does
not depend on the legacy `biodsa` package, model SDKs, LangChain, LangGraph, or
scientific Python. Its direct runtime dependencies are PyYAML and jsonschema.

## Protocol and compatibility

Phase 1 uses protocol version `1.0`. Manifests declare a list of supported
protocol versions and task types. Before execution, the harness requires an
intersection between the experiment/protocol, agent, benchmark, and prepared
dataset, and requires the selected task type in both manifests.

Common envelopes have versioned schemas in `protocol/schemas/1.0/`. Task input
and output schemas belong to the benchmark and are referenced by its manifest;
this permits QA, data analysis, and structured prediction to use different
payloads. Paths in manifests resolve relative to the manifest. Paths in
protocol messages are relative to their declared root unless a field explicitly
documents an absolute harness-owned location.

Extensions are allowed only in the explicit `extensions` object. Common schema
objects otherwise reject unknown fields so accidental protocol drift fails
early. Checksums use `sha256:<hex>`.

## Manifests

Agent manifests declare identity, compatibility, local argv, Docker build/run
metadata, required environment-variable names, resource requests, and which
usage budgets the agent can count. Benchmark manifests similarly declare
prepare/evaluate argv, runtime metadata, schemas, and simple aggregation rules.
Commands are arrays; no shell interpolation is performed.

Discovery scans configured roots for `agent.yaml` and `benchmark.yaml`.
Duplicate IDs are errors. The phase-1 CLI defaults to repository-local
`agents/` and `benchmarks/`, with repeatable root flags for other locations.

## Execution and records

The backend abstraction exposes start, wait, cancel, log collection, and
cleanup. The local backend starts a new process group, redirects stdout/stderr
to files, terminates the group on timeout/cancellation, then escalates to kill.
It is a development convenience and provides no security isolation.

The Docker backend uses the Docker CLI and a uniquely named, disposable
container. Agent input is mounted read-only and output read-write; neither the
repository, prepared `private/`, nor the Docker socket is mounted. The image
comes from the agent manifest or is built explicitly. CPU, memory, and GPU
settings are translated from the manifest. Agent and generated-code network
policies use the current `network.agent` and `network.sandbox` interface
documented in `protocol/manifests.md`. Cleanup force-removes the
named container. Benchmark runtime/container isolation is a manifest boundary
in phase 1; prepare and evaluate execute locally.

The harness enforces wall time. Model-call, token, and tool-call budgets are
passed to the agent and recorded as agent-enforced/self-reported capabilities;
the harness does not claim to enforce them. Every attempt gets a separate
working directory and `attempt_id`. `run-record.json` is authoritative for
process state, timing, exit code, timeout/cancellation, validation failures,
protocol/manifests, Git commit, data revision, and available image identity.
Forced termination is recorded by the harness regardless of agent output.

Atomic writes use a sibling temporary file, flush/fsync, and `os.replace`.
Artifact paths must be relative, must remain below the task output directory
after resolution, and must identify existing files. Symlink escapes fail.

## Run directory

```text
run/
  resolved-experiment.json
  manifests/{agent,benchmark}.json
  context/{experiment,agent-manifest,benchmark-manifest,prepared-manifest,tasks,metadata}.json
  context/evaluator/reference.json
  run-record.json
  tasks/<task-id>/attempt-0001/
    input/request.json
    workspace/
    output/result.json
    logs/{stdout,stderr}.log
    validated-result.json
  evaluations/<evaluation-id>/
    evaluation-record.json
    tasks/<task-id>/attempt-0001/{request,result,status}.json
    summary.json
  latest-evaluation.json
```

Evaluation reads validated results and snapshotted TaskSpecs, so `bioagent-gym
evaluate --run ...` never reruns an agent. Small references are saved in the
evaluator-only context; large references retain a versioned external path.
Neither is placed in the agent input or workspace.

## CLI and phase-1 aggregation

The implemented commands are `list agents`, `list benchmarks`, `validate`,
`prepare`, `run`, and `evaluate`. `run` performs agent execution and then
evaluation by default. Every `evaluate` invocation adds an immutable evaluation
record and summary from already validated agent results.

Generic aggregation supports `mean`, `sum`, `min`, `max`, and `count` for named
numeric metrics, plus task status counts. More complex aggregation remains in a
benchmark-owned command in a later phase; it is never selected by benchmark ID
inside the harness.

## Optional shared LLM boundary

`protocol/llm-client.md` defines framework-neutral request/response, timeout,
retry, and error semantics. `bioagent_gym.llm.FakeClient` provides deterministic
tests and examples. Adoption is optional: neither agent conformance nor
benchmark integration depends on this Python interface.

## Verification plan

Tests cover manifest/protocol/task-schema compatibility, subprocess execution,
invalid or missing results, timeout process-group cleanup, artifact traversal
and symlink escape, absence of private references from agent requests, and
rescoring without agent execution. A full fixture smoke prepares data, runs two
tasks, creates artifacts, scores them, and writes a mean summary. If Docker is
available, a container smoke is run; otherwise the verification report marks it
unverified rather than successful.

## Deferred work

Distributed scheduling, retries, resume/checkpoint semantics, remote sandbox
services, credential validation, provider LLM clients, benchmark-specific
complex aggregation, and migration of existing agents are outside phase 1.
The independent task and attempt identifiers, backend lifecycle interface, and
manifest runtime blocks leave room for those additions without changing the
agent file protocol.
