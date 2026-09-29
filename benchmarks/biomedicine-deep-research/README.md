# Biomedical Deep Research dataset tasks

Thirteen dataset-level tasks contain all 517 development and 131 verifier
records from
`zifeng-ai/biomedicine-deep-research` revision
`f3e34ee8ccde8ea15c98f55dae871e63ef8bc5b2`. Labels are stored only in the
separate verifier images. Single-choice, multi-select, and evidence retrieval
answers use their source target forms; citations and traces remain artifacts.

Use `experiments/deepevidence-fit.yaml`, `deepevidence-tune.yaml`, or
`deepevidence-verifier.yaml` to select one split consistently in both the
agent and trusted verifier. The inventory-wide `deepevidence-full.yaml` keeps
split-specific summaries and is not a formal mixed-split accuracy.

Single-choice answers require one legal option ID. Multi-select uses source
set exact match, ignores ordering, and rejects duplicates. The 20
evidence-gap records contain PMID targets but the pinned source supplies no
retrieval metric or ordering rule, so they are reported as `unscorable` rather
than being coerced into choice scoring or an invented retrieval metric. The
verifier-only self-check passes all 628 scoreable choice records.

Malformed JSON lines, duplicate prediction IDs, and unknown prediction IDs are
global grading errors: diagnostics are saved, evaluation exits nonzero, and no
reward is written even if all recognized answers are correct. Choice IDs are
normalized before duplicate detection, so case variants cannot bypass it.
