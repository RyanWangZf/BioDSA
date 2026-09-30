# Adding a leaderboard

Create `benchmarks/<name>/` with a scope README, committed Harbor tasks, static
jobs, one canonical grader under `scoring/`, a data-only `prepare.py`, and
inventory/oracle/grading tests under `tests/`.

Preparation may download pinned data, write public items and private references,
and copy canonical scoring code into verifier build contexts. It must not
generate or overwrite task definitions, Dockerfiles, instructions, or job YAML.
The verifier derives its denominator from trusted references and invalidates a
result when scoring infrastructure fails.
