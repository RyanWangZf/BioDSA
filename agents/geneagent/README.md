# GeneAgent for Harbor

Install independently with:

```bash
pip install -e runner -e 'agents/geneagent[harbor]'
```

Use the custom agent class exported by `bioagent_geneagent.harbor_agent` as shown in `tests/fixtures/jobs/geneagent.yaml`. The worker accepts dataset items through the shared batch runtime and writes `final_answer.md`, `trajectory.json`, `result.json`, `usage.json`, and workflow-specific artifacts for every item.

The deterministic behavior test is:

```bash
PYTHONPATH=runner/src:agents/geneagent/src python3 -m unittest discover -s agents/geneagent/tests
harbor run -c tests/fixtures/jobs/geneagent.yaml -y
```

See [MIGRATION.md](MIGRATION.md) for provenance, preserved behavior, differences, and resource limitations. Fixture success is not a live-provider or formal benchmark result.
