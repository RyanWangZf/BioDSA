# DeepRare migration plan

Baseline: `zifeng/refactor` at `ba74dba0dfaec49f03bad118f90712d814a2f107`.
The migration reference is the local, self-contained implementation under
`rsi-for-science/ai4sci-tasks/rare-disease-diagnosis/.../reference/deeprare`.
It is a reference implementation derived from DeepRare, rather than a claim of
bit-for-bit equivalence with the unrestricted upstream research system.

## Implementation checklist

- [x] Inventory the reference contract, gateways, quotas, retrieval stages,
  prompts, candidate checks, retry, and final evidence validation.
- [x] Create an independently installable `agents/deeprare` package without a
  runtime dependency on the reference checkout.
- [x] Preserve the nine-stage bounded workflow and make model/source gateways
  injectable for deterministic behavior tests.
- [x] Add the shared Harbor batch adapter and retain per-item process,
  workspace, memory, and quota isolation.
- [x] Save diagnoses, evidence, retrieval, checks, raw model output,
  trajectory, failures, and usage as item artifacts.
- [x] Add normal-path and all-rejected retry tests plus a native Harbor fixture.
- [x] Verify clean wheel installation and the installed worker outside the
  repository; attempt Docker Harbor smoke when Docker is available.
- [x] Update the agent catalog and document provenance, preserved behavior,
  differences, configuration, and validation evidence.

No legacy BioDSA package, old runner, Docker-in-Docker path, or new agent
framework will be introduced.

## Validation result

- Workflow tests: 2 passed, covering the normal route, public-field projection,
  evidence filtering, and the all-rejected retry route.
- Integration inventory checks: passed for packaging, native fixture presence,
  and forbidden legacy/cross-agent imports.
- Wheels for the runner and agent built and installed into a clean Python 3.12
  environment. Import and CLI help worked from `/private/tmp`.
- The installed item worker completed the deterministic case with 4 model and
  10 source calls and wrote all declared artifacts.
- Native Harbor Docker smoke was attempted on 2026-09-29 but Docker reported
  that its daemon was not running. No container result is claimed.
