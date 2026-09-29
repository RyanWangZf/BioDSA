# Standalone DeepEvidence

This project migrates the legacy hierarchical DeepEvidence topology into an
independent BioAgent Gym agent: an orchestrator dispatches breadth-first and
depth-first subagents, knowledge-base tools feed an evidence memory graph, and
the final synthesis exports citations, trace, memory, generated code, and code
execution logs. It does not import `biodsa`, CoderAgent, or DSWizard.

```bash
python -m venv .venv
.venv/bin/pip install -e .
.venv/bin/bioagent-deepevidence --help
```

Default tests use a deterministic mock model and stub APIs while exercising the
real workflow. `tool_mode: live` enables project-local HTTP adapters for PubMed,
MyGene, OLS, ChEMBL, MyVariant, ClinicalTrials.gov, Reactome, and PubChem.
Knowledge bases requiring an unfinished provider adapter or missing credential
fail during configuration; they are never silently removed. The current target
GraphQL and provider-specific web-search adapters require explicit follow-up
configuration.

Compared with the legacy implementation, the prompts retain the orchestrator,
breadth-first, depth-first, memory-protocol, and budget roles while the runtime
state machine is project-local and standard-library based. Legacy PDF/report
rendering and interactive graph visualization are not part of the minimal
protocol adapter; their raw trace, evidence graph, citations, code, and logs are
preserved as portable artifacts.

Memory defaults to the task workspace. Cross-task memory requires
`memory.mode: shared` and an explicit absolute `memory.path`. Generated code
uses the same local/file-channel execution boundary as the other migrated
agents: fresh interpreter per call, persistent files within one task.

Direct mock run:

```bash
bioagent-deepevidence --request examples/request.json --output-dir output \
  --config configs/mock.json
```

Harness run:

```bash
bioagent-gym prepare --benchmark fixture_evidence \
  --config benchmarks/fixture_evidence/prepare-config.json \
  --output .bioagent-gym/evidence-prepared
bioagent-gym run --config experiments/deepevidence-fixture.yaml
```

The OpenRouter PubMed config is an explicit, bounded live smoke. It reads
`OPENROUTER_API_KEY` from the environment and does not persist the value.
