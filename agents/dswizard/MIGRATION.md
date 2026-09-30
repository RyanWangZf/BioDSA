# DSWizard migration status

## Provenance

This package was derived from the in-repository BioDSA implementation at commit
`b12439eba3c77a9bab652015b17467c1f5bcf9ce`, primarily
`biodsa/agents/dswizard/`, `biodsa/agents/base_agent.py`, and the sandbox tool
wrappers. It is project code under this repository's license.

## Behavior map

| Behavior | Migrated location | Status |
|---|---|---|
| exploration → plan → implementation → final answer | `agent.py` | Preserved at the phase level |
| LangGraph message/tool loop and conditional retries | `agent.py`, `client.py` | Simplified; equivalence not established |
| source code history injected once into final program | `agent.py`, `harbor_runner.py` | Implemented and regression-tested |
| task-local execution and artifacts | `execution.py`, `harbor_runner.py` | Implemented |

The formal job exists because BioDSBench is the intended leaderboard, but no
formal 118-item result has been produced. The two-item live run completed with
0/2 successful agent executions. Installation and Harbor integration are
verified; upstream behavior comparison remains incomplete.
