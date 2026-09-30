# Legacy research code

This directory preserves pre-Harbor agents, tools, sandboxes, tutorials,
historical benchmark snapshots, launch scripts, dependency files, and tests.
They remain available for migration reference and publication provenance.

Legacy modules are not installed by the current root package, do not appear in
the supported catalogs, and have no compatibility entry point. A component
returns to the current surface only after it becomes an independently installable
agent or a native Harbor leaderboard dependency.

## Contents

- `biodsa/`, `biodsa_env/`, and related dependency files preserve the old
  framework, sandbox, and monolithic environment.
- `scripts/` contains the old `biodsa` launch examples, including agents that
  have since gained independent Harbor packages. They remain historical usage
  examples and are not maintained entrypoints.
- `biomedical_data/` contains local snapshots used by the old tools. The
  AgentMD RiskCalcs file and OpenTargets parquet are not installed or mounted by
  current agents automatically; current runs must opt into an explicit data
  path.
- `artifacts/` contains historical work directories, reports, test datasets,
  and packaged tool snapshots. Nothing under it is a test oracle for the
  current Harbor tasks.
- `assets/` contains historical visual assets not referenced by the current
  project documentation.

Current repository-root entrypoints are limited to project metadata and the
`agents/`, `benchmarks/`, `runner/`, `tests/`, and `docs/` maintenance surfaces.
