# BioDSBench dataset tasks

The Python and R dataset tasks contain all 118 and 165 records respectively
from pinned revision `e59af82ee9461db78ed399544ec8520afeb02ce5`.
Run `python3 scripts/prepare_harbor_dataset_tasks.py` to refresh the exact
inventories and stage large public tables from the external cache.

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
