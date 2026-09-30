# BioDSBench dataset tasks

The Python and R dataset tasks contain all 118 and 165 records respectively
from pinned revision `e59af82ee9461db78ed399544ec8520afeb02ce5`.
Run `python3 benchmarks/biodsbench/prepare.py` to refresh the exact inventories,
stage large public tables, private references, and verifier deployment copies.
The script verifies committed task definitions exist and does not rewrite
instructions, `task.toml`, Dockerfiles, or jobs.
Without `--skip-large-data`, missing archives or ambiguous/missing table matches
make preparation fail with a concrete file list. The flag is the only supported
way to prepare inventory metadata without asserting that tables are complete.

## Jobs and ranking scope

- `jobs/dswizard.yaml` is the formal 118-item Python leaderboard job.
- `tests/jobs/dswizard-mock.yaml` is a fixed two-item deterministic workflow check.
- `tests/jobs/dswizard-live.yaml` and `tests/jobs/coder-live.yaml` run the same
  two Python items through the same verifier. One includes source code history.
  They are bounded integration checks, not leaderboard results.

`jobs/` contains only ranked entrypoints, one file per supported agent. Coder
does not yet have a formal job because its two-item live behavior validation did
not produce a correct submission. Local development copies belong in the
gitignored `local-jobs/` directory.

The R task preserves all 165 source records and its native task definition, but
no migrated agent/runtime currently supports it. It is therefore absent from
the formal job and does not contribute to ranking.

Per-item outputs live below `/app/submission/items`. Submitted Python executes
as an unprivileged, resource-limited process away from hidden references and
reward files. A finite observation wrapper exports only the scalar, table,
array, collection, and model attributes used by the 118 pinned source tests;
the trusted grader applies the original assertions and requires every assertion
for an item to pass. It never imports submitted code or executable serialized
objects.

All 118 Python items have scoring mappings. The verifier-only reference run
passes 112. Six pinned reference implementations fail before reaching a clean
oracle result (`28481359_4`, `28481359_5`, `28481359_7`, `28481359_8`,
`28472509_4`, and `37699004_1`); the manifest records them separately from
scoring support. Unsupported R execution remains explicit and is unchanged.

Boolean composition, chained comparisons, membership checks, and finite table
value constraints are decided by the trusted grader. The unprivileged process
exports operands rather than final assertion booleans. Unsupported statements
or an empty assertion mapping block an item. A differential regression mutates
one real output variable per item; both the original source tests and the new
checker reject all 118 mutations.

Canonical scoring source is maintained only in `scoring/`. `prepare.py` copies
it into the Harbor 0.23 verifier build context. Regression and oracle helpers
live in `tests/`.
