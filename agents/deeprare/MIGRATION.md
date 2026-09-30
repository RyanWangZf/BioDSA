# DeepRare migration

## Baseline and Behavior map

Migrated from the self-contained local reference at
`rsi-for-science/ai4sci-tasks/rare-disease-diagnosis/environment/starter/reference/deeprare`
against BioAgent Gym commit `ba74dba0dfaec49f03bad118f90712d814a2f107`.
The installed package has no dependency on that checkout.

| Reference | Package |
|---|---|
| `deeprare_contract.py` | `contract.py` |
| `deeprare_gateway.py` | `gateway.py` |
| `deeprare_runtime.py` | `runtime.py` |
| `deeprare_retrieval.py` | `retrieval.py` |
| `deeprare_reasoning.py` | `reasoning.py` |
| `runner.py` | `workflow.py`, `harbor_runner.py` |

The public-case projection, source/model quotas, safety prompt, retrieval
tools, all reasoning prompts, candidate normalization, all-rejected retry,
evidence whitelist, and final contract are preserved. Sessions are injectable
for deterministic tests and append structured traces; these are observability
and testability adaptations rather than decision logic. Harbor runs each item
in its own child process and workspace.

This reference describes a curated, gateway-backed DeepRare adaptation. It
does not establish equivalence to private case collections, unrestricted web
retrieval, or every capability of the research system from which it was
derived.
