# DeepRare

Independent Harbor adapter for the bounded DeepRare rare-disease diagnostic
workflow. It accepts phenotype-only cases, gathers public evidence, performs
independent and central candidate generation, checks similar cases and each
candidate, retries once when all candidates are rejected, then emits up to five
identifier-grounded diagnoses.

Install from a checkout:

```bash
python -m pip install ./runner './agents/deeprare[harbor]'
```

Production mode uses the verifier-owned HTTP gateways configured by
`RDD_MODEL_GATEWAY_URL`, `RDD_MODEL_GATEWAY_TOKEN`, `RDD_SOURCE_GATEWAY_URL`,
and `RDD_SOURCE_GATEWAY_TOKEN`. Secrets remain environment variables. Fixture
mode injects deterministic model and source responses through task data.

The reference-compatible single-case entry point is:

```bash
bioagent-deeprare case.json result.txt [--config config.json]
```

Run the deterministic native Harbor fixture:

```bash
harbor run -c tests/fixtures/jobs/deeprare.yaml
```

The item directory contains the final contract output plus diagnoses,
retrieval, evidence, similar-case checks, candidate judgements, complete model
and source trajectory, and usage. This output is research evaluation data and
is not clinical advice.
