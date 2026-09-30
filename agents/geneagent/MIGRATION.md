# GeneAgent migration

## Provenance

Behavioral baseline: BioAgent Gym commit `bb6cd8e90f741796269cf491ef6264ac54ae3dd6`. Source: `legacy/biodsa/agents/geneagent/{agent,prompt,state,tools}.py`. This is in-repository project code under the repository license; no external checkout is a runtime dependency.

## Source map

| Legacy responsibility | Package destination |
|---|---|
| graph/main workflow and state transitions | `src/bioagent_geneagent/workflow.py` |
| prompts | `src/bioagent_geneagent/prompts.py` |
| model/provider boundary | `src/bioagent_geneagent/client.py` |
| tool/environment adaptation and artifacts | workflow plus `harbor_runner.py` |
| dataset-trial adapter | `harbor_agent.py` |

## Behavior map

Preserved flow: **baseline → topic claims → verification → topic update → analysis claims → verification → final update**. The adapter serializes the workflow-owned final decision and never repairs or chooses it. Every dataset item receives a fresh process, workflow object, and workspace. Model/tool calls and state changes are retained in `trajectory.json`.

Environment adaptation: fixture evidence covers the database tool contract and
`tools.py` provides live g:Profiler, STRING, and NCBI clients. Full live
Reactome/complex/domain parity is not validated; verification outputs
demonstrably feed later decisions.

## Verification status

- Independent package build/install/import: passed from wheels in a clean Python 3.12 environment outside the repository.
- Fixed-response behavior comparison: passed. `tests/test_behavior.py` asserts the source-derived legacy stage ordering and downstream state use; the legacy LangGraph stack was not installed and executed side by side.
- Harbor Docker fixture: prepared at `tests/fixtures/jobs/geneagent.yaml`; not run because the Docker daemon was unavailable on 2026-09-29. The installed item worker processed the same fixture successfully outside Docker.
- Live provider/resources: not run.
- Formal benchmark result: none; no ranked job was added.

The fixed-response test is a behavioral contract against the committed legacy flow, not proof of equivalence to any external paper repository.
