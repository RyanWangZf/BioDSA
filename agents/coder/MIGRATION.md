# Coder migration status

## Provenance

This package was derived from the in-repository BioDSA implementation at commit
`b12439eba3c77a9bab652015b17467c1f5bcf9ce`, primarily
`biodsa/agents/coder_agent.py`, `biodsa/agents/base_agent.py`, and the sandbox
tool wrappers. It is project code under this repository's license, rather than
a pinned external upstream checkout.

## Behavior map

| Behavior | Migrated location | Status |
|---|---|---|
| prompt → Python code → execution → final response | `agent.py` | Preserved at the phase level |
| code parsing and execution repair | `agent.py`, `client.py` | Simplified; upstream-equivalence test absent |
| task-local generated files and execution log | `execution.py`, `harbor_runner.py` | Implemented |
| Harbor input/output serialization | `harbor_runner.py` | Adapter-only |

The bounded BioDSBench live run completed the workflow but scored 0/2. This
proves the execution path, not behavioral equivalence or benchmark readiness.
No formal Coder job is published until a fixed-response comparison and a
correct bounded benchmark submission pass.
