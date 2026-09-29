# Biomedical Deep Research dataset tasks

Thirteen dataset-level tasks contain all 517 development and 131 verifier
records from
`zifeng-ai/biomedicine-deep-research` revision
`f3e34ee8ccde8ea15c98f55dae871e63ef8bc5b2`. Labels are stored only in the
separate verifier images. Single-choice, multi-select, and evidence retrieval
answers use their source target forms; citations and traces remain artifacts.

Run `python3 benchmarks/biomedicine-deep-research/prepare.py` to refresh pinned
public items, private references, manifests, and grader deployment copies. It
does not rewrite committed task definitions or jobs.

Use `jobs/deepevidence-fit.yaml` or `jobs/deepevidence-tune.yaml` for
development. `jobs/deepevidence.yaml` is the formal verifier-split job,
including evidence-gap retrieval.
`jobs/deepevidence-diagnostic.yaml` covers all splits and all 13 subsets for
inventory diagnostics; `jobs/deepevidence-smoke.yaml` is deterministic and
bounded. Diagnostic and development results do not enter the formal ranking.
`jobs/deepevidence-fixture-smoke.yaml` exercises the same task and verifier with
a second deterministic test adapter to check agent/leaderboard decoupling; it is
test infrastructure and never a ranked result.

Single-choice answers require one legal option ID. Multi-select uses source
set exact match, ignores ordering, and rejects duplicates. Evidence-gap agents
return at most 30 unique bare PMID strings in ranked order as
`{"proposed_pmids":[...]}`. Its item score is
`recall@30 = |predicted top-30 PMIDs intersect ground truth PMIDs| / |ground truth PMIDs|`.
There is no precision component or partial credit based on text similarity.

Formal results separately report choice micro accuracy and mean evidence-gap
recall@30, plus each subset and a clearly named mean item score across all 131
verifier items. Missing/failed model predictions remain
in that denominator. A grading/infrastructure error invalidates the run rather
than shrinking the denominator. Harbor task rewards must therefore be read with
the per-item and per-subset summaries; they are not averaged into a macro score.

After Harbor finishes, produce the leaderboard result with:

```bash
python3 benchmarks/biomedicine-deep-research/summarize.py /path/to/harbor/job
```

The summarizer requires all 13 formal subset trials, verifier split, the fixed
131-item denominator, complete per-item IDs, and error-free grading. It reports
agent/model identity, choice accuracy, evidence-gap recall@30, each subset, and failure counts. Missing
trials, Harbor exceptions, denominator drift, unscorable items, or grading
errors invalidate the entire result and yield exit code 2.

Malformed JSON lines, duplicate prediction IDs, and unknown prediction IDs are
global grading errors: diagnostics are saved, evaluation exits nonzero, and no
reward is written even if all recognized answers are correct. Choice IDs are
normalized before duplicate detection, so case variants cannot bypass it.

Canonical scoring source is maintained only in `scoring/`; `prepare.py` copies
it into each Harbor verifier context.
