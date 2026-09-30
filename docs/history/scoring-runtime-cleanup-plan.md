# Scoring correctness and runtime cleanup

Baseline: `5fa4f93149ffd38d79e558d1c6b308d5cd0b05f5` on
`zifeng/refactor`. The dataset-level Harbor task/trial structure is retained.
R support and additional agents are outside this change.

## Implementation checklist

- [x] Make malformed, duplicate, and unknown DeepEvidence predictions fatal to
  grading and normalize choice IDs before duplicate detection.
- [x] Compile BioDSBench boolean logic, chained comparisons, membership checks,
  and table-value constraints into trusted predicates; block any unmapped or
  empty test instead of accepting it.
- [x] Restore Python comparison short-circuit behavior and ordinary NaN
  equality semantics in the finite observation executor/checker.
- [x] Execute DSWizard's exact submitted `analysis.py` during implementation;
  keep exploration code in a separate artifact and inject code history once.
- [x] Introduce `bioagent_harbor_runtime`, a framework-free batch process
  runner packaged into each independent agent wheel.
- [x] Standardize strict item selection and use explicit per-dataset selection
  for multi-task DeepEvidence smoke jobs.
- [x] Keep benchmark grader implementations only under `scripts/`; preparation
  materializes task-local entrypoints alongside private references because
  Harbor 0.23 fixes the separate verifier build context to each task's
  `tests/` directory.
- [x] Re-run unit, wheel, differential assertion, verifier-negative, and Harbor
  Docker smoke checks; record the final counts below.

Generated task-local `grade.py` and BioDSBench `run_submission.py` files are
ignored. They are deployment copies, not maintained sources. This is necessary
with Harbor 0.23 because a separate verifier image cannot use a build context
outside its task. `scripts/prepare_harbor_dataset_tasks.py` writes them from the
single canonical implementations at the same time it prepares private labels
and large external data.

## Validation results

- 15 focused inventory/grader tests pass. They cover fatal global prediction
  errors, case-normalized duplicate options, trusted chained/boolean predicates,
  empty/unknown test blocking, short-circuit behavior, all 118 pinned mappings,
  and strict per-dataset batch selection.
- Independent wheels for Coder, DSWizard, and DeepEvidence contain the same
  `bioagent_harbor_runtime` source. Installed-wheel DSWizard tests (2) and
  DeepEvidence tests (5) pass from `/tmp`, outside the repository.
- The isolated BioDSBench reference run still accepts 112/118. The same six
  pinned reference implementations fail for the already documented source or
  browser reasons. It has no unscorable or grading-error items.
- For every one of the 118 items, a deterministic mutation replaces one
  submitted result variable with `None`. Both the original source assertions
  and the new checker reject all 118 mutations; the checker reports accuracy
  0.0 with no grading infrastructure errors.
- DeepEvidence Docker regressions using a correct answer plus a duplicate ID or
  unknown ID both exit 2, report `accuracy: null`, and produce no reward.
- Harbor Docker smoke passes through the shared runtime for DSWizard and three
  DeepEvidence dataset tasks. DSWizard's saved `analysis.py` byte-for-byte
  matches the program in its final execution log; exploration is separate.
  DeepEvidence choice mocks are validly scored and the retrieval trial remains
  explicitly rewardless (`RewardFileNotFoundError`) because no source metric is
  defined.
