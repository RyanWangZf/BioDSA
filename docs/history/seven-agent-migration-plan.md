# Seven-agent migration plan

Baseline: `bb6cd8e90f741796269cf491ef6264ac54ae3dd6` on
`zifeng/refactor`. The committed legacy tree is the behavioral reference.

## Implementation order

1. ReAct: preserve the model/tool/feedback loop, first-tool-call behavior, and
   per-call execution records.
2. TrialMind-SLR: preserve search, screening, extraction, and synthesis stage
   boundaries with their intermediate records.
3. VirtualLab: preserve team/member/leader rounds and individual
   agent/critic/revision rounds.
4. GeneAgent: preserve baseline analysis, topic claims, per-claim verification,
   topic update, analysis claims, and final update.
5. TrialGPT: preserve patient-driven retrieval, trial details, eligibility
   matching, and ranking.
6. AgentMD: preserve calculator retrieval, details/selection, and calculation;
   keep full RiskCalcs/MedCPT availability separate from the fixed fixture.
7. InformGen: preserve multi-section drafting, review, revision, completion,
   and assembly.

Each package owns its workflow, prompts/model client, tools, adapter, worker,
dependencies, tests, README, and migration map. It uses the shared batch runner
only for item selection, child-process timeout, workspace isolation, and
prediction persistence. No migrated source imports `legacy` or another agent.

## Verification

- Build and install every wheel outside the repository, then import it and show
  its worker help without repository `PYTHONPATH`.
- Run fixed-response behavior tests for stage order, state propagation, retries
  or revisions, and final workflow-owned decisions.
- Run one native Harbor Docker fixture per package and verify its trajectory and
  required artifacts. Live/provider and large-resource checks remain distinct.
- Add no formal leaderboard job until benchmark-specific behavior is validated.

## Status

- [x] ReAct
- [x] TrialMind-SLR
- [x] VirtualLab
- [x] GeneAgent
- [x] TrialGPT
- [x] AgentMD
- [x] InformGen
- [x] catalog and verification record

## Verification result (2026-09-29)

All seven wheels built and installed together in a clean Python 3.12 virtual
environment under `/private/tmp`; imports and worker help succeeded outside the
repository. All fixed-response behavior tests and installed-worker fixture runs
passed. Harbor 0.23 imported every adapter. Docker Harbor execution was attempted
in the required order and stopped before ReAct because the Docker daemon was not
running; none of the seven Docker fixtures is reported as passed. No live paid
model call or formal benchmark run was performed.
