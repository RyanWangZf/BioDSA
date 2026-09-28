# Manifest format

Both manifests use `manifest_version: "1.0"`, stable IDs, and argv arrays.
Relative executable/path arguments resolve from the manifest directory. The
harness does not invoke a shell.

An `agent.yaml` declares `agent_id`, `protocol_versions`, `task_types`, a
`local.command`, optional `docker` build/image/default command, required
environment variable *names*, resources, and `budget_capabilities`. Secret
values must not appear in the file.

A `benchmark.yaml` declares `benchmark_id`, version, compatible protocol/task
types, prepare/evaluate argv, input/output schema paths, and numeric metric
aggregation. Benchmark process environments are declared independently from
the agent; phase 1 executes benchmark commands locally.

See the fixture manifests under `agents/fixture_agent` and
`benchmarks/fixture_qa` for complete examples.
