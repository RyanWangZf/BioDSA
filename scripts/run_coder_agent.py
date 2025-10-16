# TODO:
# make the agent can execute code to answer a question in a easy way.
"""
e.g.,

```python

from biodsa.agents import CoderAgent

agent = CoderAgent(
    model_name="gpt-4o",
    api_type="azure",
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

agent.register_dataset(
"./biomedical_data/cBioPortal/datasets/acbc_mskcc_2015"
)
execution_results = agent.go(
"abcd"
)
print(execution_results)
execution_results.to_json(...)
execution_results.to_pdf(...)
execution_results.download_artifacts(...) # path the path of the artifact in the sandbox and download it to the local machine
```
"""