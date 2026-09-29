# Harbor dataset coverage

Counts below come from the complete file inventory at the pinned revisions.
Included means the public item is present in `items.jsonl`; it does not mean the
item was run or passed.

| Source / subset | Splits | Source | Included | Runnable | Scorable | Blocked |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| BioDSBench Python | benchmark | 118 | 118 | 118 | 0 | 118 |
| BioDSBench R | benchmark | 165 | 165 | 0 | 0 | 165 |
| drug-regimen-design | fit/tune/verifier | 25 | 25 | 25 | 25 | 0 |
| evidence-gap-discovery | fit/tune/verifier | 20 | 20 | 20 | 20 | 0 |
| hle-biomedicine | fit/tune/verifier | 40 | 40 | 40 | 40 | 0 |
| hle-medicine | fit/tune/verifier | 30 | 30 | 30 | 30 | 0 |
| in-vivo-metabolic-flux-response | fit/tune/verifier | 25 | 25 | 25 | 25 | 0 |
| labbench-dbqa | fit/tune/verifier | 50 | 50 | 50 | 50 | 0 |
| labbench-litqa2 | fit/tune/verifier | 25 | 25 | 25 | 25 | 0 |
| moa-pathway-reasoning | fit/tune/verifier | 25 | 25 | 25 | 25 | 0 |
| sample-size-estimation | fit/tune/verifier | 25 | 25 | 25 | 25 | 0 |
| supergpqa-hard-medicine | fit/tune/verifier | 172 | 172 | 172 | 172 | 0 |
| surrogate-endpoint-discovery | fit/tune/verifier | 14 | 14 | 14 | 14 | 0 |
| target-identification | fit/tune/verifier | 25 | 25 | 25 | 25 | 0 |
| trqa-lit | fit/tune/verifier | 172 | 172 | 172 | 172 | 0 |

BioDSBench Python execution is runnable after its external tables are staged,
but scientific scoring is currently blocked for all records: the original
assertions have not yet been converted to a trusted JSON-result evaluator. The
grader executes submitted code under an unprivileged, resource-limited process
and reports `unscorable`; it never awards a file-existence score. R is blocked
because the migrated agents and task image do not implement the source R
runtime. Per-item reasons are in each task manifest.

Biomedical Deep Research has 388 fit, 129 tune, and 131 verifier records. All
648 labels are available at this revision and are materialized only into ignored
verifier build contexts by the preparation script. This inventory has been validated for inclusion and deterministic
answer-form scoring. Only the two fixed HLE smoke IDs have been run through a
real Docker Harbor trial in this migration.
