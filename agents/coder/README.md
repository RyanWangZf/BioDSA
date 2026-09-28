# Standalone CoderAgent

This project preserves the original generate-code → execute → final-answer
workflow and prompt requirements without importing `biodsa` or another agent.
The deterministic mock client drives the real workflow and Python execution.

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/bioagent-coder --help
```

`local_subprocess` is explicit and is not a security boundary. Every execution
uses a fresh interpreter in one task workspace: files persist between calls,
Python variables do not. Docker runs the same executor inside the agent
container; no Docker socket is mounted.

Run through BioAgent Gym after installing this project in its local `.venv`:

```bash
bioagent-gym prepare --benchmark fixture_analysis \
  --config benchmarks/fixture_analysis/prepare-config.json \
  --output .bioagent-gym/analysis-prepared
bioagent-gym run --config experiments/coder-fixture-analysis.yaml
```

For a direct protocol invocation, pass a prepared `request.json` and an output
directory:

```bash
.venv/bin/bioagent-coder --request request.json --output-dir output \
  --config config.mock.json
```

Live use is explicit: copy `config.live.example.json`, select `openai`,
`azure`, `anthropic`, or `google`, set its standard credential environment
variable, and replace the mock config in an experiment. Requests have a
bounded retry count (`max_attempts`, default 3). Provider adapters are retained
for configuration compatibility; this migration verified the deterministic
mock path and did not call a paid endpoint.
