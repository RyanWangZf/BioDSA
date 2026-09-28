# BioAgent Gym reliability fix plan

Status: implemented

1. Add strict JSON Schemas for agent, benchmark, experiment, and prepared
   manifests. Validate split, benchmark/protocol/version/data revision before
   creating a run, and resolve prepared task/reference paths below the prepared
   root. Support either one declared split or an explicit `splits` mapping.
2. Snapshot the resolved experiment, agent config value, manifests, selected
   TaskSpecs, and prepared metadata. Copy only small references into a private
   run context; retain a versioned external path for large references. Never
   expose evaluator context to an agent workspace.
3. Give each attempt separate input, workspace, output, and logs directories.
   Resolve only the manifest command entry point against agent source. Run local
   processes from the workspace; mount and use `/workspace` for Docker.
4. Make backend start/wait/cancel/cleanup exception-safe. On interruption,
   terminate the process group/container, record cancellation, stop scheduling,
   finalize the run record, and propagate cancellation to the CLI without a
   traceback.
5. Store each scoring pass below `evaluations/<evaluation_id>/`, preserving all
   earlier results. Read TaskSpecs from the run snapshot, check declared data,
   benchmark, and evaluator versions, isolate per-task evaluator failures, and
   report execution/evaluation counts plus metric denominator and coverage.
6. Record wall time as harness-enforced and derive all other budget semantics
   from manifest capabilities. Reject requested unsupported budgets unless the
   experiment explicitly chooses best effort.
7. Extend deterministic fixtures and regression tests for split mismatch,
   version mismatch, strict configuration, workspace isolation, cancellation,
   evaluator failure continuation, aggregation denominators, snapshots, and
   rescore history. Run local smoke, legacy rescore, wheel/out-of-tree CLI, and
   Docker smoke when the daemon is accessible.

This design intentionally does not add whole-dataset hashing or per-run content
scans. Version declarations, immutable run snapshots, evaluation records, and
optional existing checksums provide the reproducibility boundary. If an
external large reference is modified in place without changing its declared
version, BioAgent Gym cannot detect that content change.
