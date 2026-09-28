# Phase 2: CoderAgent and DSWizard migration plan

Status: implemented

1. Add the minimal `data.analysis.python.v1` input/output schemas and a tiny
   CSV benchmark fixture. The task carries the user request, asset metadata,
   optional table descriptions, and output requirements.
2. Migrate CoderAgent first into `agents/coder` as an independently installable
   project. Keep its code-generation → execution → final-response workflow and
   prompts, with a thin protocol adapter and deterministic mock LLM.
3. Add a per-task Python execution session inside the agent runtime. Each call
   starts a fresh Python process in one persistent task workspace, matching the
   old sandbox's file persistence without claiming variable persistence.
4. Migrate DSWizard independently into `agents/dswizard`. Preserve explicit
   planning/exploration and implementation phases, and publish the analysis
   plan as a separate artifact. It must not import the Coder project.
5. Give each project its own package metadata, dependency lock, Dockerfile,
   manifest, configs, tests, and README. The harness remains free of both
   packages and their optional live-model dependencies.
6. Verify standalone installs in separate temporary virtual environments,
   direct CLI help, actual mock-driven workflow/code execution, artifact
   collection, workspace isolation, timeout cleanup, and full harness runs on
   the CSV fixture. Provide live-model commands as explicit opt-in only.

The execution backend is explicit in agent config. `local_subprocess` is used
for deterministic local tests and is not a security boundary. In Docker mode
the same subprocess runs inside the host-harness-managed agent container; the
agent never receives the host Docker socket. No silent Docker-to-host fallback
is allowed.

## Implemented migration map

| Legacy responsibility | Coder project | DSWizard project |
| --- | --- | --- |
| workflow and prompts | `bioagent_coder.agent` | `bioagent_dswizard.agent` |
| request/result adapter | `bioagent_coder.cli` | `bioagent_dswizard.cli` |
| model initialization and retry | `bioagent_coder.client` | `bioagent_dswizard.client` |
| code execution | `bioagent_coder.execution` | `bioagent_dswizard.execution` |
| result export | protocol adapter and atomic `result.json` write | protocol adapter and atomic `result.json` write |

The old `BaseAgent` was not copied. The two projects deliberately own their
small adapters and execution wrappers, so neither project depends on the
other or on the legacy `biodsa` package. No LangChain or model SDK enters the
harness dependency set. A shared package can be extracted later if more
agents prove that these small interfaces are stable.

## Execution boundary

The host harness creates one attempt directory with separate input, workspace,
output, and log locations. An agent starts generated Python from that workspace
in a new process group. Repeated executions within a task share files but do
not share Python variables, matching the observed legacy sandbox behavior.
Timeout closes the process group with TERM followed by KILL. The adapter copies
only declared input assets into the workspace and collects declared output
files; benchmark references never enter the agent request or workspace.

`local_subprocess` is a development execution environment, not a sandbox. With
the harness Docker backend, it executes inside the task's agent container. The
host harness owns container startup and cleanup and does not mount the Docker
socket. There is no Docker-to-host fallback.

## Compatibility and verification scope

The additive task type is `data.analysis.python.v1`; existing protocol object
fields and protocol version remain unchanged. The fixture benchmark exercises
two CSV tasks and emits `analysis_summary.csv`; DSWizard additionally emits
`analysis_plan.md`. Optional checksums remain optional.

Deterministic mock clients drive the real workflow and real Python subprocesses
without paid API calls. The live adapters accept OpenAI, Azure OpenAI,
Anthropic, and Google-style configuration and preserve bounded retry behavior,
but live provider calls are not part of the default verification. The mock,
local execution, package isolation, and harness paths are verified. Docker is
verified only when a daemon is available.
