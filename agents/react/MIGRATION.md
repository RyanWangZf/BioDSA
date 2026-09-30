# ReAct migration

## Provenance

Behavioral baseline: BioAgent Gym commit `bb6cd8e90f741796269cf491ef6264ac54ae3dd6`. Source: `legacy/biodsa/agents/react_agent.py`. This is in-repository project code under the repository license; no external checkout is a runtime dependency.

## Source map

| Legacy responsibility | Package destination |
|---|---|
| graph/main workflow and state transitions | `src/bioagent_react/workflow.py` |
| prompts | `src/bioagent_react/prompts.py` |
| model/provider boundary | `src/bioagent_react/client.py` |
| tool/environment adaptation and artifacts | workflow plus `harbor_runner.py` |
| dataset-trial adapter | `harbor_agent.py` |

## Behavior map

Preserved flow: **model decision → first code tool call → execution feedback → continue/stop**. The adapter serializes the workflow-owned final decision and never repairs or chooses it. Every dataset item receives a fresh process, workflow object, and workspace. Model/tool calls and state changes are retained in `trajectory.json`.

Environment adaptation: The legacy first-tool-call-only behavior is intentionally retained. The old BaseAgent model factory and Docker sandbox are replaced by package-local model and task-process adapters.

Each code call uses a fresh Python interpreter in the item's persistent
workspace: files persist across calls, Python variables do not. Generated calls
and their exact stdout, stderr, and exit status are saved separately; no
synthetic concatenated `analysis.py` is emitted.
For BioDSBench, source `code_history` is prepended exactly once to every
execution and the task image's `/usr/local/bin/python3` is used rather than the
agent virtual environment.

## Verification status

- Independent package build/install/import: passed from wheels in a clean Python 3.12 environment outside the repository.
- Fixed-response behavior comparison: passed. `tests/test_behavior.py` asserts the source-derived legacy stage ordering and downstream state use; the legacy LangGraph stack was not installed and executed side by side.
- Harbor Docker fixture: prepared at `tests/fixtures/jobs/react.yaml`; not run because the Docker daemon was unavailable on 2026-09-29. The installed item worker processed the same fixture successfully outside Docker.
- Live provider/resources: not run.
- Formal benchmark result: none; no ranked job was added.

The fixed-response test is a behavioral contract against the committed legacy flow, not proof of equivalence to any external paper repository.
