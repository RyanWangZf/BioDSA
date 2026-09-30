# AgentMD for Harbor

Install independently with:

```bash
pip install -e runner -e 'agents/agentmd[harbor]'
```

Use the custom agent class exported by `bioagent_agentmd.harbor_agent` as shown in `tests/fixtures/jobs/agentmd.yaml`. The worker accepts dataset items through the shared batch runtime and writes `final_answer.md`, `trajectory.json`, `result.json`, `usage.json`, and workflow-specific artifacts for every item.

The deterministic behavior test is:

```bash
PYTHONPATH=runner/src:agents/agentmd/src python3 -m unittest discover -s agents/agentmd/tests
harbor run -c tests/fixtures/jobs/agentmd.yaml -y
```

See [MIGRATION.md](MIGRATION.md) for provenance, preserved behavior, differences, and resource limitations. Fixture success is not a live-provider or formal benchmark result.
