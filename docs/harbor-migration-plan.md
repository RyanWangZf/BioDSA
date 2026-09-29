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
- [x] Add native fixture tasks and Harbor adapters; run Docker end to end.
- [x] Add and test Coder, DSWizard, DeepEvidence adapters and smoke jobs.
- [x] Materialize selected BioDSBench tasks, inputs, and executable verifiers.
- [x] Materialize selected biomedical deep-research tasks and label verifiers.
- [x] Validate both static mix configs and attempt a credential-limited live smoke.
- [x] Remove superseded runner/protocol code and update README/docs.

## Validation record

All commands used Harbor 0.23.0 with absolute `--jobs-dir` paths:

- fixture Docker job: 2/2 rewards 1.0; one validated adapter artifacts and one
  attempted HTTPS from a `no-network` agent phase and verified it was blocked.
- Coder mock analysis trial: reward 1.0; generated code executed and CSV was
  collected.
- DSWizard mock analysis trial: reward 1.0; exploration, plan, implementation,
  and execution artifacts were collected.
- DeepEvidence mock trial: reward 1.0; BFS/DFS dispatch, stub tools, memory,
  code execution, citations, trace, and usage were verified.
- complete BioDSBench Oracle mix: 4/4 trials, reward 1.0 each, against the real
  downloaded tables and source assertions.
- complete biomedical Deep Research Oracle mix: 4/4 trials, reward 1.0 each;
  a separate `nop` trial confirmed a missing submission receives reward 0.0.
- DSWizard/Qwen live attempt 1 reached Harbor's 300-second limit. A bounded
  retry exposed a model response with no content after its output budget was
  spent on reasoning. The final retry used `reasoning_effort=none`, reached
  OpenRouter, and was rejected with HTTP 429. Live DSWizard therefore remains
  unverified; it is not reported as a mock success.
- The public-network live attempts reached OpenRouter (the final response was
  HTTP 429), independently confirming public egress. No key value appeared in
  the Harbor job configs or logs scanned after the attempts.

Task schemas and both four-task job YAMLs load successfully through Harbor's
actual Pydantic models. Dataset content is versioned by the pinned source
revisions; this migration does not add mandatory whole-tree checksums.

Harbor 0.23.0 currently resolves relative result paths from Docker Compose build
contexts during some copy operations. Commands use an absolute `--jobs-dir` as
a documented workaround. Per-phase network policies are enforced by Harbor.
Online-agent/offline-generated-code requires two execution boundaries, which
these single-container adapters do not implement; no configuration claims that
topology is supported.
