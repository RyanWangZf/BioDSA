# Harbor test fixtures

These deterministic tasks validate the custom-agent boundary and Harbor verifier
without model credentials or external APIs. Their task environment is explicitly
offline.

The fixture agent is under `agent/`, tasks under `tasks/`, and the native smoke
job under `jobs/fixture-smoke.yaml`. None appears in the supported agent or
leaderboard catalogs.

`benchmarks/biomedicine-deep-research/jobs/deepevidence-fixture-smoke.yaml`
uses the deterministic fixture as a second BDR-compatible batch adapter. It
checks that the leaderboard task and verifier are not coupled to DeepEvidence;
its score is not a scientific agent result.
