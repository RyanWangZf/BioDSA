from __future__ import annotations
import argparse,json,mimetypes,os,shutil,tempfile
from pathlib import Path
from .workflow import DeepEvidenceAgent
def atomic(path,value):
 path.parent.mkdir(parents=True,exist_ok=True); fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=".result-")
 with os.fdopen(fd,"w") as handle: json.dump(value,handle,indent=2); handle.flush(); os.fsync(handle.fileno())
 os.replace(tmp,path)
def main(argv=None):
 parser=argparse.ArgumentParser(prog="bioagent-deepevidence"); parser.add_argument("--request",required=True); parser.add_argument("--output-dir",required=True); parser.add_argument("--config",required=True); args=parser.parse_args(argv); request=json.loads(Path(args.request).read_text()); config=json.loads(Path(args.config).read_text()); out=Path(args.output_dir).resolve(); out.mkdir(parents=True,exist_ok=True); workspace=Path.cwd()
 if config.get("execution_environment",{}).get("backend") not in ("local_subprocess","file_channel"): raise SystemExit("unsupported execution_environment.backend; no fallback")
 try:
  for asset in request.get("assets",[]): shutil.copy2((Path(args.request).parent/asset["path"]).resolve(),workspace/Path(asset["path"]).name)
  if "tool_calls" in request.get("budget",{}): config["tool_call_budget"]=min(int(config.get("tool_call_budget",request["budget"]["tool_calls"])),int(request["budget"]["tool_calls"]))
  payload=request["input"]; result=DeepEvidenceAgent(config,workspace).run(payload["research_question"],payload.get("background","") ); usage=result.pop("usage"); artifacts=[]
  for name,value,description in (("evidence_graph.json",result["memory_graph"],"Evidence memory graph"),("trace.json",result["trace"],"Orchestrator and subagent execution trace"),("citations.json",result["citations"],"Structured citations")):
   (out/name).write_text(json.dumps(value,indent=2)); artifacts.append({"path":name,"type":"application/json","description":description})
  input_names={Path(x["path"]).name for x in request.get("assets",[])}
  for source in workspace.iterdir():
   if source.is_file() and source.name not in input_names and source.name!="evidence_graph.json": shutil.copy2(source,out/source.name); artifacts.append({"path":source.name,"type":mimetypes.guess_type(source.name)[0] or "application/octet-stream","description":"DeepEvidence generated artifact"})
  value={"protocol_version":request["protocol_version"],"run_id":request["run_id"],"attempt_id":request["attempt_id"],"task_id":request["task_id"],"status":"completed","output":result,"artifacts":artifacts,"usage":usage}
 except Exception as exc: value={"protocol_version":request["protocol_version"],"run_id":request["run_id"],"attempt_id":request["attempt_id"],"task_id":request["task_id"],"status":"failed","artifacts":[],"error":{"code":"deepevidence_error","message":str(exc)}}
 atomic(out/"result.json",value); return 0
if __name__=="__main__": raise SystemExit(main())
