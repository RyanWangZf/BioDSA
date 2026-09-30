# Harbor test fixtures

These deterministic tasks validate the custom-agent boundary and Harbor verifier
without model credentials or external APIs. Their task environment is explicitly
offline.

The fixture agent is under `agent/`, tasks under `tasks/`, and the native smoke
job under `jobs/fixture-smoke.yaml`. None appears in the supported agent or
leaderboard catalogs.

`benchmarks/biomedicine-deep-research/tests/jobs/fixture.yaml`
uses the deterministic fixture as a second BDR-compatible batch adapter. It
checks that the leaderboard task and verifier are not coupled to DeepEvidence;
its score is not a scientific agent result.

The seven migration fixtures are native dataset tasks named
`tasks/<agent>-workflow` with matching `jobs/<agent>.yaml`. Their public item
contains fixed model/tool responses but still invokes the installed agent's
real workflow and batch worker. Verifiers inspect ordered trajectory events and
required outputs. VirtualLab contains both a team item and an individual item in
one dataset trial, which also exercises per-item process/workspace isolation.
These fixtures verify deterministic behavior contracts; they are not live API
or scientific benchmark results.
