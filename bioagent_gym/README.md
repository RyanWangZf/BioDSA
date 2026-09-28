# BioAgent Gym

BioAgent Gym is a modular framework for running and evaluating biomedical AI
agents in reproducible task environments. Install the lightweight package in an
isolated environment with `pip install -e .`, or run it from the checkout as
`python -m bioagent_gym`.

```bash
bioagent-gym list agents
bioagent-gym list benchmarks
bioagent-gym prepare --benchmark fixture_qa \
  --config experiments/fixture-prepare.json \
  --output .bioagent-gym/fixture-prepared
bioagent-gym validate --config experiments/fixture-qa.yaml
bioagent-gym run --config experiments/fixture-qa.yaml
bioagent-gym evaluate --run .bioagent-gym/fixture-run
```

`run` evaluates after agent execution unless `--no-evaluate` is supplied.
Local execution is for development and does not sandbox untrusted code. Docker
execution uses the image and command declared by the agent manifest and mounts
only the per-attempt input (read-only) and output directories.
