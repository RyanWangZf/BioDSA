# BioAgent Gym naming migration plan

Status: implemented

## Inventory from phase 1

The phase-1 implementation used the distribution name `biodsa-harness`, the
console command `biodsa`, and the Python package `harness`. Versioned protocol
data was shipped through a separate `protocol` Python data package. The file
protocol version is `1.0`; its schemas and manifest/config fields contain no
`biodsa` discriminator, URI, or format name. Fixture Docker resources used the
image `biodsa/fixture-agent:0.1` and container prefix `biodsa-`. Example outputs
were explicitly placed below `.biodsa/`.

No phase-1 framework-specific environment variables or user cache lookup were
implemented. Provider variables such as `OPENAI_API_KEY` are manifest-declared
agent inputs and remain unchanged. The existing legacy `biodsa` package is the
pre-refactor agent framework and is outside this naming migration.

## Public mapping

| Phase-1 name | BioAgent Gym name | Compatibility |
|---|---|---|
| BioDSA harness | BioAgent Gym | Documentation and UI text use the new brand. |
| `biodsa-harness` distribution | `bioagent-gym` | Replaced in package metadata. |
| `harness` import package | `bioagent_gym` | `harness` remains a thin deprecated import shim for phase-1 callers. |
| `biodsa` console script | `bioagent-gym` | Replaced; no competing command is installed. |
| `python -m harness.cli` | `python -m bioagent_gym` | Old module path remains readable through the shim. |
| `.biodsa/` example output | `.bioagent-gym/` | Explicit old paths and existing directories are still accepted and never moved. |
| `biodsa/fixture-agent:0.1` | `bioagent-gym/fixture-agent:0.1` | Manifests select the tag; historical run records retain the old value. |
| `biodsa-<id>` container | `bioagent-gym-<id>` | Runtime-only name; cleanup behavior is unchanged. |
| `protocol` data package | `bioagent_gym.protocol` | Source files remain in `protocol/`, but the wheel exposes them only below the new namespace. |

The project description is: “A modular framework for running and evaluating
biomedical AI agents in reproducible task environments.” The word Gym does not
add a Gymnasium API or an RL training interface.

## Protocol compatibility

Protocol version `1.0`, all common field names, task-type schemas, status
semantics, manifest version `1.0`, and experiment structure remain unchanged.
There is no brand-bearing schema ID or discriminator to translate. New code
uses the same strict schemas, so compatibility does not weaken unknown-field
validation.

Phase-1 requests, results, prepared datasets, agent/benchmark manifests, and run
records are read directly. Rescoring uses the absolute prepared and benchmark
manifest paths already persisted in phase-1 `resolved-experiment.json`; it does
not rerun the agent. Old explicit output/cache paths such as `.biodsa/` continue
to work. New examples and generated default cache locations use
`.bioagent-gym/` and `~/.cache/bioagent-gym/` respectively.

The phase-1 implementation had no framework-prefixed environment variable, so
there is no real old variable requiring fallback or deprecation warning. New
framework settings use `BIOAGENT_GYM_`; provider-standard variables remain
unchanged, and values are never logged.

## Implementation steps

1. Move implementation imports and console entry point to `bioagent_gym`; add
   `__main__` for `python -m bioagent_gym`.
2. Package protocol resources as `bioagent_gym.protocol` and retain their
   version and content.
3. Keep `harness` as dependency-free compatibility shims, with deprecation
   warnings at old public entry points.
4. Change framework cache, generated example paths, Docker image/container
   names, documentation, fixtures, and tests to the new brand.
5. Add tests that read a frozen phase-1 run/config shape and rescore a run from
   an old `.biodsa/` directory without executing the agent.
6. Build and install the wheel into a clean temporary virtual environment, then
   invoke both the console command and module entry point outside the repository.

## Validation

Validation covers strict protocol and artifact checks from phase 1, minimal
dependency metadata, installed invocation outside the source tree, the complete
prepare/run/evaluate fixture flow, phase-1 import and data compatibility,
rescoring an old run, cache/env precedence and deprecation, and a search-based
classification of remaining `biodsa` references.

Docker build/run is attempted only when the daemon is accessible. If it is not,
the result is recorded as unverified rather than successful.

## Historical names intentionally retained

The legacy `biodsa/agents` implementation and its imports remain intact so this
rename does not pull LangChain, LangGraph, model SDKs, or scientific packages
into the new harness. Published names and stable IDs such as `BioDSA-1K` and
`BioDSBench`, paper/BibTeX text, dataset IDs, original data fields, and current
external links remain unchanged.

## Repository rename follow-up

The configured remotes currently point to the valid repositories
`RyanWangZf/BioDSA.git` and `RyanWangZf/BioDSA-dev.git`; this change does not call
GitHub or edit those remotes. After the repository is formally renamed, update
the Git remote URLs, clone commands, repository badges, source/documentation
links, packaging project URLs, release automation, and any external integration
that keys on the repository slug. Do not publish a `bioagent-gym` URL before it
exists.
