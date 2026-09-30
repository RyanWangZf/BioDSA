# Adding an agent

## Fix the source before porting

Clone the official implementation into the gitignored
`reference_repo/<agent>/` directory and check out an exact commit. This checkout
is read-only migration input: it must not be placed on `PYTHONPATH`, imported by
the migrated package, copied into a Harbor image, or required after migration.
Respect the upstream license and preserve required attribution.

Commit `agents/<name>/MIGRATION.md` with:

- upstream repository URL, exact commit, license, and relevant source paths;
- a source-to-destination file map;
- a behavior map covering the main loop and stop condition, every prompt and
  tool contract, state/memory reads and writes, retry/budget behavior, and the
  source of the final answer;
- necessary adapter or environment changes and every known behavior difference;
- evidence for independent installation, deterministic behavior comparison,
  bounded Harbor smoke, and formal evaluation as four separate statuses.

Prefer the upstream implementation and its own dependencies. Do not replace a
framework or algorithm merely to keep another package lightweight. The Harbor
adapter may translate task inputs, configure resources, call the workflow, and
serialize its actual decision; it must not choose, repair, reorder, or synthesize
the answer on the workflow's behalf.

Behavior comparison uses the same fixed model and tool responses against the
upstream and migrated implementations. Compare call order, state transitions,
retry/termination behavior, tool arguments, memory consumption, and final
decision. Exact prose need not match when semantics and ordering are preserved.
An adapter smoke proves execution only; it does not prove migration fidelity.

## Package and Harbor contract

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
Only add a formal job after the agent's benchmark behavior has been validated;
bounded live/mock jobs belong under that benchmark's `tests/jobs/`. Do not copy
tasks or add a registry. Update the four status columns in `agents/README.md`
from concrete evidence rather than a single ambiguous “verified” label.
