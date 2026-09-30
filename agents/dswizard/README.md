# DSWizard for Harbor

Install independently with `pip install -e 'agents/dswizard[harbor]'`. Use
`bioagent_dswizard.harbor_agent:DSWizardHarborAgent`. The real exploration,
planning, implementation, generated-code execution, and final-answer stages run
inside the Harbor trial. Submissions include `analysis_plan.md`, `analysis.py`,
`execution.json`, `final_answer.md`, and generated files.

`provider=mock` exercises all stages without credentials. The formal job is
under `benchmarks/biodsbench/jobs/`; bounded mock and live configs are under
`benchmarks/biodsbench/tests/jobs/`.

See [MIGRATION.md](MIGRATION.md) for provenance and the behavior still requiring
comparison with the legacy graph. A Harbor smoke does not establish fidelity.
