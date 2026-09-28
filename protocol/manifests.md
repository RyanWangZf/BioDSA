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

See the fixture manifests under `agents/fixture_agent` and
`benchmarks/fixture_qa` for complete examples.
