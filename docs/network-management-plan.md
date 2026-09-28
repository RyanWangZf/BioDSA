# Network management implementation plan

Status: implemented and Docker-verified

1. Replace `resources.network` with independently resolved `network.agent` and
   `network.sandbox` policies. Resolution order is framework defaults, agent
   manifest, experiment override, benchmark constraints, then backend
   capability checks. The removed field is rejected by strict schemas.
2. Record the resolved mode, source, backend, shared boundary, applicability,
   and enforcement status in validation output, experiment snapshots, and run
   records. Keep agent and sandbox credential allowlists separate.
3. Apply Docker networking with ordinary bridge networking for `internet` and
   Docker `--network none` for `none`. Equal policies may share the agent
   container; differing policies use a host-managed execution sidecar and a
   file request/response channel. Never mount the Docker socket.
4. Reject local configurations containing `none`, because the local process
   backend cannot enforce network isolation. Local `internet` means only that
   host networking is left available.
5. Update manifests, experiments, docs, and regression tests. Mock fixtures
   declare offline defaults; local mock experiments explicitly override them
   to `internet`. Docker network tests run only when a daemon is available and
   are reported as unverified otherwise.

These policies cover agent execution and generated-code execution. Image
builds, benchmark preparation, and evaluators remain outside this policy.
