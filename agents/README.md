# Supported agents

Only independently installable Harbor agents appear here. Fixture agents live
under `tests/fixtures/agent`; unmigrated implementations live under `legacy/`.

| Agent | Purpose | Independent install | Harbor smoke | Upstream behavior comparison | Formal result |
|---|---|---:|---:|---:|---:|
| [Coder](coder/README.md) | Direct code generation and execution | Passed | Live completed, BioDSBench 0/2 | Not completed | Not run; no formal job |
| [DSWizard](dswizard/README.md) | Planned biomedical data analysis | Passed | Live completed, BioDSBench 0/2 | Not completed | Not run |
| [DeepEvidence](deepevidence/README.md) | Multi-agent biomedical evidence research | Passed | Live completed, BDR 6/6 items scored | Not completed | Not run |

Install with `pip install -e runner -e 'agents/<name>[harbor]'`. “Harbor smoke”
means that the adapter, workflow, tools/code execution, submission, and verifier
ran on the bounded scope; it does not assert scientific correctness or fidelity
to an upstream implementation. See each `MIGRATION.md` and the dated run record
under `docs/history/` for the underlying evidence and known differences.

Each package owns its prompts, workflow, tools, dependencies, tests, and Harbor
adapter. Adapters call `bioagent_harbor_runtime.run_batch` for selection,
isolated child processes, timeouts, workspaces, and incremental predictions.
Harbor owns the dataset-level trial and Docker environment.

During Harbor `setup()`, each adapter creates `/opt/<agent>` inside the task
container, installs that distribution's declared runtime dependencies, and
stages the agent plus shared runner into the environment. Batch workers use the
agent interpreter. Generated analysis code uses the task image's explicit
Python, preserving the dependency boundary between agent logic and benchmark
scientific execution.
