# Harbor item runner

`bioagent-harbor-runtime` is the small, framework-free runtime shared by agent
adapters. It selects trusted item IDs, starts one process group and workspace per
item, enforces item timeouts, cleans children, and writes incremental
`predictions.jsonl` output.

It does not import agents, manage Docker, schedule Harbor trials, or score
answers. Install it explicitly with the selected agent:

```bash
pip install -e runner -e agents/dswizard
```

Run its tests with `python -m unittest discover -s runner/tests` after an
editable install.
