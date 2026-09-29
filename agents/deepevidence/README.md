# DeepEvidence for Harbor

Install independently with `pip install -e 'agents/deepevidence[harbor]'`. Use
`bioagent_deepevidence.harbor_agent:DeepEvidenceHarborAgent`. Orchestration,
BFS/DFS subagents, knowledge-base tools, failure recovery, budgets, task-local
memory, optional generated-code execution, and synthesis remain in this package.

The adapter writes the final answer, citations, evidence, trace, memory graph,
usage, generated code, and execution logs to `/app/submission`. Mock mode stubs
only the LLM and external APIs. Live tools fail explicitly when their required
credential or adapter is unavailable. Trial workspaces and memory are isolated
by Harbor.
