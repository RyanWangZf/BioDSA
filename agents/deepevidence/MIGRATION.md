# DeepEvidence migration status

## Provenance

This package was derived from the in-repository BioDSA implementation at commit
`b12439eba3c77a9bab652015b17467c1f5bcf9ce`, primarily
`biodsa/agents/deepevidence/`, the memory graph, and biomedical tool wrappers.
It is project code under this repository's license.

## Behavior map

| Behavior | Migrated location | Status |
|---|---|---|
| orchestrator, BFS/DFS routing, stopping budgets | `workflow.py`, `prompts.py` | Phase names retained; upstream decision loop equivalence not established |
| knowledge-base clients and error handling | `tools.py` | Selected clients migrated; full upstream tool parity not established |
| evidence memory write/retrieve | `memory.py`, `workflow.py` | Stored and traced; retrieved memory is not yet fed back into synthesis |
| final choice/PMID decision | `client.py`, `workflow.py` | Model decision is preserved by adapter |
| citations, trace, memory graph, failure artifacts | `harbor_runner.py` | Implemented |

The bounded live BDR run produced six structurally valid, scored submissions,
including model-selected retrieval PMIDs. It did not compare call order, state
transitions, or tool policy against the legacy graph. In particular, `_search`
still iterates configured tools and records BFS/DFS prompts without reproducing
the original independent model-driven subworkflows. This package must not be
described as behavior-equivalent until that comparison and the missing memory
feedback path are addressed.
