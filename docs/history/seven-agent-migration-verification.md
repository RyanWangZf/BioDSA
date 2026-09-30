# Seven-agent migration verification — 2026-09-29

Baseline: `bb6cd8e90f741796269cf491ef6264ac54ae3dd6`.

| Agent | Clean wheel install/import/help | Fixed-response behavior contract | Installed worker fixture | Harbor Docker | Benchmark/live |
|---|---:|---:|---:|---:|---|
| ReAct | passed | passed | passed, 4 events | blocked: daemon unavailable | BioDSBench two-item config prepared; not run |
| TrialMind-SLR | passed | passed | passed, 11 events | blocked: daemon unavailable | PubMed live path not run |
| VirtualLab | passed | passed, both modes | passed; two-item batch isolation also passed | blocked: daemon unavailable | BDR adaptation not claimed |
| GeneAgent | passed | passed | passed, 7 events | blocked: daemon unavailable | live databases not run |
| TrialGPT | passed | passed | passed, 6 events | blocked: daemon unavailable | ClinicalTrials.gov live path not run |
| AgentMD | passed | passed | fixed BMI fixture passed, 3 events | blocked: daemon unavailable | full RiskCalcs/MedCPT resources not packaged or validated |
| InformGen | passed | passed | passed, 9 events | blocked: daemon unavailable | live provider not run |

The behavior tests use the same fixed model/tool outcomes encoded from the
committed legacy stage graphs. They check call order, downstream state use,
revisions, eligibility/ranking, and final workflow decisions. The legacy
LangGraph dependency stack was not installed and executed side by side, so the
catalog describes this as a source-derived contract rather than runtime parity.

All eight wheels (runner plus seven agents) were built with Python 3.12, then
installed together into a clean virtual environment under `/private/tmp`.
Imports and `python -m bioagent_<name>.harbor_runner --help` ran from `/private/tmp`
without repository paths. The installed workers processed their public fixture
items and saved final answers, trajectories, results, usage, and agent-specific
artifacts.

Docker validation was attempted first with:

```bash
harbor run -c tests/fixtures/jobs/react.yaml \
  --jobs-dir /private/tmp/seven-agent-harbor-results -y
```

Harbor 0.23 returned `Docker daemon is not running` before creating the ReAct
trial. The other six Docker jobs were therefore not presented as successes.
They remain directly runnable with the corresponding YAML after Docker starts.
No paid model call or full benchmark was launched.

Regression commands:

```bash
for agent in react trialmind_slr virtuallab geneagent trialgpt agentmd informgen; do
  PYTHONPATH="runner/src:agents/$agent/src" \
    python3 -m unittest discover -s "agents/$agent/tests" -p 'test_*.py'
done
python3 -m unittest tests.integration.test_harbor_dataset_tasks
PYTHONPATH=runner/src python3 -m unittest discover -s runner/tests -p 'test_*.py'
```
