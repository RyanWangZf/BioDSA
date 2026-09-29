# Phase 3: sandbox completion and DeepEvidence migration

Status: implemented

## 1. Sandbox and existing-agent closeout

1. Apply sandbox-specific CPU, memory, and GPU limits to independent execution
   containers. Agent `resources` remain agent-runtime limits; new
   `sandbox.resources` apply only when the boundary is separate.
2. Add an atomic worker-ready marker, bounded startup wait, container liveness
   checks, structured per-request errors, and captured worker logs. A failed or
   exited worker must stop the task before the agent starts or fail an active
   request without waiting for the generic response timeout.
3. Preserve the observed execution semantics: every code call starts a fresh
   interpreter; the task workspace persists files across calls; attempts do
   not share workspaces. Always remove agent and sandbox containers on normal
   completion, failure, timeout, and cancellation.
4. Exercise shared-online, shared-offline, and online-agent/offline-sandbox
   Docker paths against a controlled endpoint. Verify environment allowlists,
   container resource settings, artifacts, startup failure, and cleanup.
5. Run bounded CoderAgent and DSWizard live tasks only with an already declared
   environment credential and model configuration. Mock tests remain default.

## 2. DeepEvidence migration map

| Legacy component | Independent project destination |
| --- | --- |
| orchestrator and BFS/DFS graph | `bioagent_deepevidence.workflow` |
| orchestrator/BFS/DFS prompts | `bioagent_deepevidence.prompts` |
| message, trace, budget state | `bioagent_deepevidence.models` |
| knowledge-base selection | `bioagent_deepevidence.tools.registry` |
| PubMed, trials, genes, diseases, drugs, targets, variants, web, compounds, pathways | project-local lazy tool adapters under `tools/` |
| evidence-memory graph and retrieval | `bioagent_deepevidence.memory` |
| generated-code execution | existing BioAgent Gym file-channel/local execution interface copied as a thin project adapter |
| TaskRequest/AgentResult conversion and artifacts | `bioagent_deepevidence.cli` |

The old `BaseAgent`, global `biodsa.agents` imports, and eager import of every
provider/tool are not migrated. Tool capabilities remain represented in the
registry. Each adapter declares its optional dependency or credential; an
enabled unavailable tool fails during configuration instead of disappearing.
Small execution/client adapters may remain duplicated until another migration
proves a stable shared package boundary.

The migrated project preserves the hierarchical orchestrator/BFS/DFS topology,
knowledge-base selection, search/action budgets, task memory graph, generated
code path, structured trace, citations, and artifacts. Its runtime uses a thin
standard-library model client rather than the legacy BaseAgent/LangGraph class
hierarchy. The registry retains PubMed, gene, disease, drug, variant, clinical
trials, web search, target, pathway, and compound capabilities with lazy
adapters. Live HTTP adapters are implemented for PubMed, MyGene, OLS, ChEMBL,
MyVariant, ClinicalTrials.gov, Reactome, and PubChem. Target GraphQL and
provider-specific web search require explicit adapters and fail early when
selected in live mode; stub mode covers their workflow integration.

## 3. Protocol and verification

1. Add the minimal `research.evidence_synthesis.v1` input/output schemas and a
   deterministic fixture benchmark whose evaluator checks output structure and
   artifacts without assigning a scientific-correctness score.
2. Package DeepEvidence independently with manifest, Dockerfile, lockfile,
   configs, examples, README, CLI, and tests. Default network modes are
   `internet`; task memory is isolated unless an explicit cache path is set.
3. Mock LLM and stub APIs must drive the real orchestrator, BFS and DFS routes,
   tool results, memory writes/retrieval, optional code execution, budgets,
   failures, and final synthesis. Test two sequential tasks for isolation.
4. Verify a clean wheel install and CLI outside the repository, harness local
   execution, Docker execution when available, and one bounded PubMed live
   task when the existing provider credential and network are usable.

Image-build, prepare, and evaluator networking remain outside agent/sandbox
network policy. This phase does not migrate other agents or claim that a single
PubMed smoke validates every knowledge base.

## Verification status

- Coder mock/local/Docker paths pass. Live PubMed produced a three-row CSV;
  live CSV analysis produced correct group means and a valid SVG artifact.
- DSWizard mock/local/Docker planning and implementation paths pass. Its
  OpenRouter/Qwen live tasks reached the 360-second per-task limit before the
  four serial model calls completed, so live behavior remains unverified.
- DeepEvidence clean wheel install, repository-external import/CLI, unit tests,
  local harness, Docker harness, and bounded PubMed live synthesis pass. The
  structural fixture intentionally returns `not_applicable` with no score.
