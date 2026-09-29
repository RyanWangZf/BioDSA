# BioDSBench dataset tasks

The Python and R dataset tasks contain all 118 and 165 records respectively
from pinned revision `e59af82ee9461db78ed399544ec8520afeb02ce5`.
Run `python3 scripts/prepare_harbor_dataset_tasks.py` to refresh the exact
inventories and stage large public tables from the external cache.

Per-item outputs live below `/app/submission/items`. Submitted Python executes
away from hidden references and reward files. Unsupported R execution and
assertions that cannot cross the safe JSON boundary are explicit manifest
blockers rather than file-existence passes.
