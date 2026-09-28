# Manifest format

Both manifests use `manifest_version: "1.0"`, stable IDs, and argv arrays.
The command entry point (argv element zero) resolves within the manifest
directory when relative; remaining arguments stay literal. The harness does not
invoke a shell. Agents resolve their own source-relative files from the entry
point location because every task starts in a distinct workspace.

An `agent.yaml` declares `agent_id`, `protocol_versions`, `task_types`, a
`local.command`, optional `docker` build/image/default command, required
environment variable *names*, resources, and `budget_capabilities`. Secret
values must not appear in the file.

Network policy is independent for the agent and its generated-code sandbox:

```yaml
network:
  agent: {mode: internet}
  sandbox: {mode: internet}
```

Both modes default to `internet`; supported values are `internet` and `none`.
Experiments can partially override either layer under `execution.network`.
Benchmarks can restrict acceptable modes with `network_constraints`. Resolution
is strict: defaults, agent manifest, experiment override, benchmark constraint,
then backend capability validation. The removed `resources.network` field is
invalid and has no compatibility mapping.

An agent that executes generated code declares a `sandbox` Docker runtime,
its own `resources`, and its own `required_env` allowlist. Agent `resources`
limit the agent runtime; `sandbox.resources` limit a separate sandbox. Equal agent/sandbox policies may share one
container. Different policies use a host-managed sidecar and a file channel;
the Docker socket is never mounted. Docker `none` is enforced with
`--network none`; `internet` uses ordinary container networking without host
networking or published ports. Local execution cannot enforce `none` and
rejects it. Credentials are allowlisted separately and their values are never
written to requests, snapshots, or logs.

`budget_capabilities` maps `model_calls`, `tokens`, or `tool_calls` to
`agent_enforced` or `reported_only`. A legacy list is read as reported-only.
Wall time is harness-enforced. Requested unsupported budgets fail validation
unless the experiment explicitly selects `budget_policy: best_effort`, in which
case the RunRecord says `unsupported`.

A `benchmark.yaml` declares `benchmark_id`, version, compatible protocol/task
types, prepare/evaluate argv, input/output schema paths, and numeric metric
aggregation. Benchmark process environments are declared independently from
the agent; phase 1 executes benchmark commands locally.

Metric aggregation declares whether agent execution failures are excluded or
counted as zero. Evaluator infrastructure failures are always reported
separately and never converted to incorrect answers.

These network fields govern agent execution and generated-code execution only.
Image builds, data preparation, and evaluators have independent runtime policy.

See the fixture manifests under `agents/fixture_agent` and
`benchmarks/fixture_qa` for complete examples.
