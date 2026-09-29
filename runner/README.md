# Harbor item runner

`bioagent-harbor-runtime` is the small, framework-free runtime shared by agent
adapters. It selects trusted item IDs, starts one process group and workspace per
item, enforces item timeouts, cleans children, and writes incremental
`predictions.jsonl` output.

Each item worker must write `final_answer.md`; it may write a JSON object in
`usage.json`. Missing or malformed outputs become that item's `agent_error` and
later items continue. Explicit empty selections are rejected. Cleanup targets
the worker process group even after its leader exits.

It does not import agents, manage Docker, schedule Harbor trials, or score
answers. Install it explicitly with the selected agent:

```bash
pip install -e runner -e agents/dswizard
```

Run its tests with `python -m unittest discover -s runner/tests` after an
editable install.
