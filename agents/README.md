# Supported agents

Only independently installable Harbor agents appear here. Fixture agents live
under `tests/fixtures/agent`; unmigrated implementations live under `legacy/`.

| Agent | Purpose | Independent install | Legacy/upstream behavior comparison | Harbor smoke | Formal result |
|---|---|---:|---:|---:|---:|
| [Coder](coder/README.md) | Direct code generation and execution | Passed | Not completed | Live completed, BioDSBench 0/2 | Not run; no formal job |
| [DSWizard](dswizard/README.md) | Planned biomedical data analysis | Passed | Not completed | Live completed, BioDSBench 0/2 | Not run |
| [DeepEvidence](deepevidence/README.md) | Multi-agent biomedical evidence research | Passed | Not completed | Live completed, BDR 6/6 items scored | Not run |
| [ReAct](react/README.md) | Iterative code execution with model feedback | Passed | Source-derived contract passed; side-by-side legacy runtime not run | Docker blocked; installed worker passed | Not run; BioDSBench live config prepared |
| [TrialMind-SLR](trialmind_slr/README.md) | Four-stage systematic literature review | Passed | Source-derived contract passed; side-by-side legacy runtime not run | Docker blocked; installed worker passed | Not run |
| [VirtualLab](virtuallab/README.md) | Team and individual scientific discussion | Passed | Source-derived contract passed; side-by-side legacy runtime not run | Docker blocked; installed worker passed | Not run |
| [GeneAgent](geneagent/README.md) | Gene-set analysis with claim verification | Passed | Source-derived contract passed; side-by-side legacy runtime not run | Docker blocked; installed worker passed | Not run |
| [TrialGPT](trialgpt/README.md) | Patient-to-clinical-trial matching and ranking | Passed | Source-derived contract passed; side-by-side legacy runtime not run | Docker blocked; installed worker passed | Not run |
| [AgentMD](agentmd/README.md) | Medical calculator retrieval and execution | Passed | Source-derived contract passed; full resources blocked | Docker blocked; fixed-calculator worker passed | Not run |
| [InformGen](informgen/README.md) | Reviewed, section-based document generation | Passed | Source-derived contract passed; side-by-side legacy runtime not run | Docker blocked; installed worker passed | Not run |
| [DeepRare](deeprare/README.md) | Bounded phenotype-to-rare-disease diagnosis with public evidence | Passed | Local reference behavior contract passed | Docker smoke attempted; see migration record | Not run |

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
