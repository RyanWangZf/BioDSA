from __future__ import annotations
import re
from pathlib import Path
from .client import MockClient, OpenAICompatibleClient
from .execution import PythonExecutionSession

SYSTEM_PROMPT="""# TASK: Given the user's ask, you must write python code which will be executed to answer the user's question.

# IMPORTANT: CODE OUTPUT REQUIREMENTS
You must import all the necessary libraries at the beginning of your code.
You must use explicit print() statements for ALL outputs you want to see or analyze. Expressions such as df.head() alone will not appear in the execution log.
Every intermediate result and final output must be wrapped in a print() statement. Avoid comments in the code to reduce its size.

# Available data:
{datasets}

## Output
Return Markdown with generated code wrapped in ```python tags."""
FINAL_PROMPT="# TASK: Please try to answer the user's question based on the code execution results."

class CoderAgent:
    def __init__(self, config, workspace: Path):
        self.config,self.workspace=config,workspace
        provider=config.get("provider","mock"); self.client=MockClient() if provider=="mock" else OpenAICompatibleClient(config)
    def run(self, task: str, data_files: list[str]):
        if isinstance(self.client,MockClient): code=self.client.code(task,data_files[0])
        else:
            text=self.client.complete([{"role":"system","content":SYSTEM_PROMPT.format(datasets="\n".join(data_files))},{"role":"user","content":task}]); blocks=re.findall(r"```python(.*?)```",text,re.S|re.I); code="\n\n".join(b.strip() for b in blocks)
        with PythonExecutionSession(self.workspace,float(self.config["execution_environment"]["timeout_seconds"])) as session: execution=session.execute(code)
        if execution.timed_out: raise TimeoutError("generated code timed out")
        if execution.exit_code != 0: raise RuntimeError(f"generated code failed: {execution.stderr}")
        final=self.client.final(task,execution.stdout) if isinstance(self.client,MockClient) else self.client.complete([{"role":"system","content":FINAL_PROMPT},{"role":"user","content":task+"\nExecution:\n"+execution.stdout}])
        return {"final_answer":final,"generated_code":[code],"execution_logs":[execution.json()]}
