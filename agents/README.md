# Supported agents

Only independently installable Harbor agents appear here. Fixture agents live
under `tests/fixtures/agent`; unmigrated implementations live under `legacy/`.

| Agent | Purpose | Install with runner | Verified leaderboard |
|---|---|---|---|
| [Coder](coder/README.md) | Direct code generation and execution | `pip install -e runner -e 'agents/coder[harbor]'` | Fixture analysis tasks |
| [DSWizard](dswizard/README.md) | Planned biomedical data analysis | `pip install -e runner -e 'agents/dswizard[harbor]'` | BioDSBench Python |
| [DeepEvidence](deepevidence/README.md) | Multi-agent biomedical evidence research | `pip install -e runner -e 'agents/deepevidence[harbor]'` | Biomedical Deep Research |

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
