from __future__ import annotations
import re
from pathlib import Path
from .client import MockClient,OpenAICompatibleClient
from .execution import PythonExecutionSession
PLAN_PROMPT="""You are an expert data analysis agent. Create a step-by-step natural-language analysis plan that can be faithfully implemented as Python code.

First understand the request and explore the available datasets with code to collect schema, value-range, and package information. Then create a plan containing the analysis steps and quality-control steps. Review it for missing steps or ambiguous dataset choices before completing it. Use explicit print() statements for every code output.

# Available data:
{datasets}"""
CODE_PROMPT="""You are a code generation agent. Convert the detailed ANALYSIS_PLAN into correct and complete Python code and use the execution results to answer the request.

Review the plan and inspect the feasibility of its key steps. Explore further with code if needed, then perform the final execution. Import all libraries at the beginning and use explicit print() statements for every visible result.

# Available data:
{datasets}

ANALYSIS_PLAN:
{plan}"""
class DSWizardAgent:
 def __init__(self,config,workspace:Path): self.config,self.workspace=config,workspace; self.client=MockClient() if config.get("provider","mock")=="mock" else OpenAICompatibleClient(config)
 def run(self,task,data_files):
  logs=[]; codes=[]; timeout=float(self.config["execution_environment"]["timeout_seconds"])
  with PythonExecutionSession(self.workspace,timeout) as session:
   if isinstance(self.client,MockClient): explore=self.client.exploration_code(data_files[0])
   else:
    response=self.client.complete([{"role":"system","content":PLAN_PROMPT.format(datasets="\n".join(data_files))},{"role":"user","content":task+"\nReturn one exploratory ```python block."}]); explore="\n".join(x.strip() for x in re.findall(r"```python(.*?)```",response,re.S|re.I))
   exploration=session.execute(explore); logs.append(exploration.json()); codes.append(explore)
   if exploration.timed_out or exploration.exit_code!=0: raise RuntimeError("planning exploration failed: "+exploration.stderr)
   plan=self.client.plan(task,exploration.stdout) if isinstance(self.client,MockClient) else self.client.complete([{"role":"system","content":PLAN_PROMPT.format(datasets="\n".join(data_files))},{"role":"user","content":task+"\nExploration:\n"+exploration.stdout+"\nReturn the final plan."}])
   if isinstance(self.client,MockClient): implementation=self.client.implementation_code(task,data_files[0])
   else:
    response=self.client.complete([{"role":"system","content":CODE_PROMPT.format(datasets="\n".join(data_files),plan=plan)},{"role":"user","content":task+"\nReturn one ```python block."}]); implementation="\n".join(x.strip() for x in re.findall(r"```python(.*?)```",response,re.S|re.I))
   executed=session.execute(implementation); logs.append(executed.json()); codes.append(implementation)
   if executed.timed_out or executed.exit_code!=0: raise RuntimeError("implementation failed: "+executed.stderr)
  final=self.client.final(task,executed.stdout) if isinstance(self.client,MockClient) else self.client.complete([{"role":"system","content":"Answer from execution results."},{"role":"user","content":executed.stdout}])
  return {"final_answer":final,"analysis_plan":plan,"generated_code":codes,"execution_logs":logs}
