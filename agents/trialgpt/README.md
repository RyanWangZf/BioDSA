# TrialGPT for Harbor

Install independently with:

```bash
pip install -e runner -e 'agents/trialgpt[harbor]'
```

Use the custom agent class exported by `bioagent_trialgpt.harbor_agent` as shown in `tests/fixtures/jobs/trialgpt.yaml`. The worker accepts dataset items through the shared batch runtime and writes `final_answer.md`, `trajectory.json`, `result.json`, `usage.json`, and workflow-specific artifacts for every item.

The deterministic behavior test is:

```bash
PYTHONPATH=runner/src:agents/trialgpt/src python3 -m unittest discover -s agents/trialgpt/tests
harbor run -c tests/fixtures/jobs/trialgpt.yaml -y
```

See [MIGRATION.md](MIGRATION.md) for provenance, preserved behavior, differences, and resource limitations. Fixture success is not a live-provider or formal benchmark result.
