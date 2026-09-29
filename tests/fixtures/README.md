# Harbor test fixtures

These deterministic tasks validate the custom-agent boundary and Harbor verifier
without model credentials or external APIs. Their task environment is explicitly
offline.

The fixture agent is under `agent/`, tasks under `tasks/`, and the native smoke
job under `jobs/fixture-smoke.yaml`. None appears in the supported agent or
leaderboard catalogs.
