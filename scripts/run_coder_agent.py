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

results =agent.go(
"abcd"
)

print(results)
results.to_json(...)
results.to_pdf(...)
```
"""