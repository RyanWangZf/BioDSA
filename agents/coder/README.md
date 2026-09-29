# CoderAgent for Harbor

Install independently with `pip install -e 'agents/coder[harbor]'`. Use the
custom agent path `bioagent_coder.harbor_agent:CoderHarborAgent` in a Harbor job
or `--agent`. The adapter installs the package into the trial container, invokes
the existing code-generation workflow, and writes `final_answer.md`,
`analysis.py`, execution logs, and generated artifacts under `/app/submission`.

`provider=mock` is deterministic. OpenAI-compatible live jobs accept `model_name`,
`endpoint`, `api_key_env`, `max_attempts`, `max_tokens`, `reasoning_effort`, and
`timeout_seconds` through Harbor agent kwargs. Secrets belong in Harbor agent
environment configuration.
