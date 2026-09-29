# Adding an agent

Create `agents/<name>/` with its own `pyproject.toml`, source namespace,
dependencies, README, tests, and `harbor_agent.py`. Declare
`bioagent-harbor-runtime` when the adapter uses dataset batch execution.
Implement a thin `run_item(item, config, workspace, output_dir)` integration and
pass it to the shared runner; keep prompts and algorithms in the agent.

Add `benchmarks/<leaderboard>/jobs/<agent>.yaml` referencing existing tasks.
Do not copy tasks or add a registry. Update `agents/README.md` after independent
wheel/install and Harbor smoke verification.
