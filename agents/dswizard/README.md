# DSWizard for Harbor

Install independently with `pip install -e 'agents/dswizard[harbor]'`. Use
`bioagent_dswizard.harbor_agent:DSWizardHarborAgent`. The real exploration,
planning, implementation, generated-code execution, and final-answer stages run
inside the Harbor trial. Submissions include `analysis_plan.md`, `analysis.py`,
`execution.json`, `final_answer.md`, and generated files.

`provider=mock` exercises all stages without credentials. The bounded OpenRouter
formal and smoke jobs are maintained with the leaderboard under
`benchmarks/biodsbench/jobs/`.
