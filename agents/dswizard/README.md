# Standalone DSWizard

This project preserves DSWizard's planning/exploration → implementation → final
answer workflow. The analysis plan is both structured output and a separate
artifact. It does not import the Coder project or legacy `biodsa` package.

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/bioagent-dswizard --help
```

The execution session uses fresh Python processes and a persistent per-task
filesystem, matching the original sandbox semantics. `local_subprocess` is an
explicit development backend. When the agent itself runs in Docker, generated
code normally shares that container and both layers default to `internet`.
Different policies use a host-managed execution sidecar and file channel; no
Docker socket is mounted and there is no silent host fallback. Local `none` is
rejected because it cannot be enforced.

Run through BioAgent Gym after installing this project in its local `.venv`:

```bash
bioagent-gym prepare --benchmark fixture_analysis \
  --config benchmarks/fixture_analysis/prepare-config.json \
  --output .bioagent-gym/analysis-prepared
bioagent-gym run --config experiments/dswizard-fixture-analysis.yaml
```

The deterministic Docker smoke explicitly disables both network layers in
`experiments/dswizard-fixture-analysis-docker-offline.yaml`. The local mock
experiment explicitly uses host networking because local `none` is unsupported.

The direct protocol form is:

```bash
.venv/bin/bioagent-dswizard --request request.json --output-dir output \
  --config config.mock.json
```

Live use is explicit: copy `config.live.example.json`, select `openai`,
`azure`, `anthropic`, or `google`, set its standard credential environment
variable, and reference that config from an experiment. Requests have a
bounded retry count (`max_attempts`, default 3). Provider adapters are retained
for configuration compatibility; the default verification uses the mock
client, real planning and implementation phases, and real Python execution.
