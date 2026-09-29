# Adding an agent

Create `agents/<name>/` with its own `pyproject.toml`, source namespace,
dependencies, README, tests, and `harbor_agent.py`. Declare
`bioagent-harbor-runtime` when the adapter uses dataset batch execution.
Expose an item-worker module accepting
`--item-worker <request.json>`. The request contains `item`, `config`,
`workspace`, and `output`; the worker writes `final_answer.md`, optional
`usage.json`, and artifacts to `output`. The thin dataset entrypoint calls
`run_batch(request, "your_package.worker_module", ...)`. Keep prompts and
algorithms in the agent.

The Harbor adapter stages the installed agent and shared runner, creates one
agent virtual environment during `setup()`, installs the distribution's declared
runtime dependencies there, and launches the batch worker with that Python.
Generated task code uses the task image's explicitly configured Python. Agent
setup runs once per dataset trial and the environment is reused for all items.

Add `benchmarks/<leaderboard>/jobs/<agent>.yaml` referencing existing tasks.
Do not copy tasks or add a registry. Update `agents/README.md` after independent
wheel/install and Harbor smoke verification.
