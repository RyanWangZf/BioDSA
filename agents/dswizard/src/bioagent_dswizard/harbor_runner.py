from __future__ import annotations
import argparse, json, os, shutil, signal, subprocess, sys
from pathlib import Path
from .agent import DSWizardAgent

def _worker(request: Path)->int:
 d=json.loads(request.read_text()); w,o=Path(d["workspace"]),Path(d["output"]); w.mkdir(parents=True); o.mkdir(parents=True); item=d["item"]
 r=DSWizardAgent(d["config"],w).run(item["instruction"],[str(Path("/app")/p) for p in item.get("input_paths",[])])
 replay=[item.get("code_history","")]+r["generated_code"]
 (o/"final_answer.md").write_text(r["final_answer"]); (o/"analysis_plan.md").write_text(r["analysis_plan"]); (o/"analysis.py").write_text("\n\n".join(x for x in replay if x)); (o/"execution.json").write_text(json.dumps(r["execution_logs"],indent=2))
 for p in w.iterdir():
  if p.is_file(): shutil.copy2(p,o/p.name)
 return 0

def _batch(d:dict)->int:
 app=Path("/app"); item_file=app/"data/items.jsonl"; single_mode=not item_file.is_file(); items=[json.loads(x) for x in item_file.read_text().splitlines() if x.strip()] if not single_mode else [{"item_id":"single","instruction":d["instruction"],"input_paths":[str(p.relative_to(app)) for p in (app/"inputs").rglob("*") if p.is_file()]}]; selected=d.get("item_ids") or []; known={x["item_id"] for x in items}
 if set(selected)-known: raise ValueError(f"unknown item_ids: {sorted(set(selected)-known)}")
 if selected: items=[x for x in items if x["item_id"] in set(selected)]
 sub=app/"submission"; sub.mkdir(exist_ok=True)
 with (sub/"predictions.jsonl").open("w") as stream:
  for item in items:
   i=item["item_id"]; w,o=app/"work/items"/i,sub/"items"/i; req=app/"work/requests"/f"{i}.json"; req.parent.mkdir(parents=True,exist_ok=True); req.write_text(json.dumps({"item":item,"config":d["config"],"workspace":str(w),"output":str(o)}))
   p=subprocess.Popen([sys.executable,"-m","bioagent_dswizard.harbor_runner","--item-worker",str(req)],start_new_session=True); status,error="completed",None
   try:
    code=p.wait(timeout=float(d.get("item_timeout_seconds",300)))
    if code: status,error="agent_error",f"item worker exited {code}"
   except subprocess.TimeoutExpired:
    status,error="timeout","per-item timeout"; os.killpg(p.pid,signal.SIGTERM)
    try: p.wait(timeout=5)
    except subprocess.TimeoutExpired: os.killpg(p.pid,signal.SIGKILL); p.wait()
   except BaseException:
    if p.poll() is None: os.killpg(p.pid,signal.SIGTERM)
    try: p.wait(timeout=5)
    except subprocess.TimeoutExpired: os.killpg(p.pid,signal.SIGKILL); p.wait()
    raise
   finally:
    if p.poll() is None: os.killpg(p.pid,signal.SIGKILL); p.wait()
   answer=(o/"final_answer.md").read_text() if status=="completed" else None; row={"item_id":i,"status":status,"final_answer":answer,"artifacts_dir":f"items/{i}"}
   if error: row["error"]=error
   if single_mode and status=="completed":
    for artifact in o.iterdir():
     if artifact.is_file(): shutil.copy2(artifact,sub/artifact.name)
   stream.write(json.dumps(row)+"\n"); stream.flush(); os.fsync(stream.fileno())
 return 0

def main()->int:
 p=argparse.ArgumentParser(); p.add_argument("request",type=Path); p.add_argument("--item-worker",action="store_true"); a=p.parse_args(); return _worker(a.request) if a.item_worker else _batch(json.loads(a.request.read_text()))
if __name__=="__main__": raise SystemExit(main())
