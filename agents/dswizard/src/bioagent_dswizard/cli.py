from __future__ import annotations
import argparse,json,mimetypes,os,shutil,tempfile
from pathlib import Path
from .agent import DSWizardAgent
def atomic(path,value):
 path.parent.mkdir(parents=True,exist_ok=True); fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=".result-")
 with os.fdopen(fd,"w") as h: json.dump(value,h,indent=2); h.flush(); os.fsync(h.fileno())
 os.replace(tmp,path)
def main(argv=None):
 p=argparse.ArgumentParser(prog="bioagent-dswizard"); p.add_argument("--request",required=True); p.add_argument("--output-dir",required=True); p.add_argument("--config",required=True); a=p.parse_args(argv); req=json.loads(Path(a.request).read_text()); config=json.loads(Path(a.config).read_text()); out=Path(a.output_dir).resolve(); out.mkdir(parents=True,exist_ok=True); workspace=Path.cwd()
 if config.get("execution_environment",{}).get("backend") not in ("local_subprocess","file_channel"): raise SystemExit("unsupported execution_environment.backend; no fallback")
 try:
  files=[]
  for asset in req["assets"]:
   source=(Path(a.request).parent/asset["path"]).resolve(); target=workspace/Path(asset["path"]).name; shutil.copy2(source,target); files.append(target.name)
  details="\n".join(f"- {table['asset_id']}: {table['description']} ({', '.join(table.get('columns', []))})" for table in req["input"]["tables"]); requirements="\n".join(f"- {item}" for item in req["input"]["output_requirements"]); task=f"{req['input']['user_task']}\nTables:\n{details}\nOutput requirements:\n{requirements}"
  result=DSWizardAgent(config,workspace).run(task,files); artifacts=[]
  for name in ("analysis_summary.csv",):
   source=workspace/name
   if source.is_file(): shutil.copy2(source,out/name); artifacts.append({"path":name,"type":mimetypes.guess_type(name)[0] or "application/octet-stream","description":"Generated analysis artifact"})
  (out/"analysis_plan.md").write_text(result["analysis_plan"]); artifacts.append({"path":"analysis_plan.md","type":"text/markdown","description":"DSWizard analysis plan"}); (out/"generated_code.py").write_text("\n\n".join(result["generated_code"])); artifacts.append({"path":"generated_code.py","type":"text/x-python","description":"Exploration and implementation code"})
  value={"protocol_version":req["protocol_version"],"run_id":req["run_id"],"attempt_id":req["attempt_id"],"task_id":req["task_id"],"status":"completed","output":result,"artifacts":artifacts,"usage":{"model_calls":4}}
 except Exception as exc: value={"protocol_version":req["protocol_version"],"run_id":req["run_id"],"attempt_id":req["attempt_id"],"task_id":req["task_id"],"status":"failed","artifacts":[],"error":{"code":"agent_error","message":str(exc)}}
 atomic(out/"result.json",value); return 0
if __name__=="__main__": raise SystemExit(main())
