# Repository architecture

BioAgent Gym has three current surfaces:

- `agents/`: independently installable agent implementations and Harbor adapters.
- `runner/`: framework-free, container-internal per-item process support.
- `benchmarks/`: leaderboard-owned tasks, jobs, preparation, scoring, and tests.

Harbor 0.23.0 owns the dataset-level trial, environment build, cancellation,
timeout, verifier execution, and result directory. Within a dataset task, the
runner creates a fresh session, child process, and writable workspace per item.
This is process/workspace isolation in one task container, not a per-item
container security boundary.

An agent wheel contains only its own namespace and declares
`bioagent-harbor-runtime` as a dependency. Benchmarks never import agents.
During Harbor setup the adapter creates a reusable agent virtual environment and
installs its declared runtime dependencies. Agent workers use that interpreter;
generated analysis uses the task image's configured interpreter so benchmark
scientific dependencies remain owned by the task.
Historical pre-Harbor code lives under `legacy/` and is outside the current
install, catalog, and execution path.
