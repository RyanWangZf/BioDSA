# Harbor migration plan

## Baseline

- BioAgent Gym HEAD at migration start: `580322917d1fa15ed9b01b57c3339367fe695812`.
- Execution engine: `harbor==0.23.0` (Python 3.12+, task schema 1.4).
- BioDSBench source: `zifeng-ai/BioDSBench` at revision
  `e59af82ee9461db78ed399544ec8520afeb02ce5`.
- Biomedical Deep Research source: `zifeng-ai/biomedicine-deep-research` at
  revision `f3e34ee8ccde8ea15c98f55dae871e63ef8bc5b2`.

Harbor is the only trial runner. BioAgent Gym supplies custom Harbor agents,
native task directories, and static Harbor job YAML. There is no compatibility
layer for the previous CLI, manifests, request/result protocol, or run records.

## Target layout and execution

- `agents/{coder,dswizard,deepevidence,fixture_agent}` retain independent
  packages and expose Harbor `BaseAgent` implementations.
- `benchmarks/fixtures/tasks` contains deterministic adapter smoke tasks.
- `benchmarks/biodsbench/tasks` contains selected Python BioDSBench records and
  their real input tables and executable assertions.
- `benchmarks/biomedicine-deep-research/tasks` contains selected development
  records and answer-key verifiers isolated from the agent phase.
- `experiments/{fixture-smoke,dswizard-mix,deepevidence-mix}.yaml` are native
  Harbor 0.23 job configs with explicit local task paths.

The custom Harbor adapter runs the installed agent package against the Harbor
environment API. Agent code and generated code execute in the trial container;
the task workspace persists within one trial and is fresh across trials. Harbor
owns container creation, network policy, timeout, cancellation, verifier, and
result storage. No Docker socket or nested BioAgent Gym runner is used.

Real agents use the task environment's public network policy for model and
biomedical API calls. Offline fixtures use `network_mode = "none"`. Harbor's
single task container does not provide an agent-online/code-offline split; such
a configuration is rejected/documented rather than weakened. Secrets are
passed with Harbor agent environment configuration and are not stored in tasks.

## Prepared task selection

BioDSBench uses Python tasks only. The initial mix selects four stable record
IDs from study `27959731`: `27959731_0`, `27959731_2`, `27959731_3`, and
`27959731_4`. They cover descriptive statistics and clinical feature
engineering, share a compact real study dataset, and have executable assertions
whose required state can be reconstructed in one submitted Python program.

Biomedical Deep Research selects four labelled development records across two
source categories: two `hle-biomedicine` and two `labbench-litqa2` examples.
Their exact `example_id` values are recorded in each task's provenance file.
They have deterministic option labels, so the verifier does not require an LLM
judge. This mix validates answer correctness, not internal BFS/DFS or memory
artifacts.

## Module disposition

| Current module | Action |
| --- | --- |
| Coder, DSWizard, DeepEvidence workflows/prompts/tools | Keep; add Harbor adapters and remove file-protocol entrypoints after smoke passes. |
| Agent LLM clients, memory, budgets, recovery | Keep inside each independent package. |
| `bioagent_gym/`, `harness/` | Delete after native Harbor trials pass. |
| `protocol/` and old manifest/config schemas | Delete after native Harbor trials pass. |
| old prepared benchmark fixtures and experiment YAML | Replace with native Harbor task directories and job YAML. |
| historical research agents/data | Keep when unrelated to the replaced execution layer. |

## Implementation status

- [x] Inspect repository baseline and Harbor 0.23.0 CLI/types/templates.
- [x] Inspect both required Hugging Face repositories and pin revisions.
- [ ] Add native fixture tasks and Harbor adapters; run Docker end to end.
- [ ] Add and test Coder, DSWizard, DeepEvidence adapters and smoke jobs.
- [ ] Materialize selected BioDSBench tasks, inputs, and executable verifiers.
- [ ] Materialize selected biomedical deep-research tasks and label verifiers.
- [ ] Run both static mixes and live credential-limited smoke where available.
- [ ] Remove superseded runner/protocol code and update README/docs.

Validation results and any blocked live checks will be appended here as work
lands. Dataset content is versioned by the pinned source revisions; this
migration does not add mandatory whole-tree checksums.
