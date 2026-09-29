from __future__ import annotations
import argparse, json, os, signal, subprocess, sys
from pathlib import Path
from .workflow import DeepEvidenceAgent

def _worker(request:Path)->int:
 d=json.loads(request.read_text()); w,o=Path(d["workspace"]),Path(d["output"]); w.mkdir(parents=True); o.mkdir(parents=True)
 r=DeepEvidenceAgent(d["config"],w).run(d["item"]["instruction"]); usage=r.pop("usage")
 (o/"final_answer.md").write_text(r["final_answer"])
 for name,key in (("citations.json","citations"),("evidence.json","evidence"),("trace.json","trace"),("memory_graph.json","memory_graph"),("execution.json","execution_logs")): (o/name).write_text(json.dumps(r[key],indent=2))
 (o/"generated_code.py").write_text("\n\n".join(r["generated_code"])); (o/"usage.json").write_text(json.dumps(usage,indent=2)); return 0

def _batch(d:dict)->int:
 app=Path("/app"); item_file=app/"data/items.jsonl"; single_mode=not item_file.is_file(); items=[json.loads(x) for x in item_file.read_text().splitlines() if x.strip()] if not single_mode else [{"item_id":"single","instruction":d["instruction"],"input_paths":[]}]
 split=d.get("split")
 if split not in {None,"fit","tune","verifier"}: raise ValueError(f"unsupported split: {split}")
 if split: items=[x for x in items if x.get("source_split")==split]
 selected=d.get("item_ids") or []; known={x["item_id"] for x in items}
 if selected:
  relevant=set(selected)&known
  if not relevant: raise ValueError(f"no selected item belongs to this dataset task and split {split}")
  items=[x for x in items if x["item_id"] in relevant]
 sub=app/"submission"; sub.mkdir(exist_ok=True)
 with (sub/"predictions.jsonl").open("w") as stream:
  for item in items:
   i=item["item_id"]; w,o=app/"work/items"/i,sub/"items"/i; req=app/"work/requests"/f"{i}.json"; req.parent.mkdir(parents=True,exist_ok=True); req.write_text(json.dumps({"item":item,"config":d["config"],"workspace":str(w),"output":str(o)}))
   p=subprocess.Popen([sys.executable,"-m","bioagent_deepevidence.harbor_runner","--item-worker",str(req)],start_new_session=True); status,error="completed",None
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
   if (o/"usage.json").is_file(): row["usage"]=json.loads((o/"usage.json").read_text())
   if error: row["error"]=error
   if single_mode and status=="completed":
    for artifact in o.iterdir():
     if artifact.is_file(): __import__("shutil").copy2(artifact,sub/artifact.name)
   stream.write(json.dumps(row)+"\n"); stream.flush(); os.fsync(stream.fileno())
 return 0

def main()->int:
 p=argparse.ArgumentParser(); p.add_argument("request",type=Path); p.add_argument("--item-worker",action="store_true"); a=p.parse_args(); return _worker(a.request) if a.item_worker else _batch(json.loads(a.request.read_text()))
if __name__=="__main__": raise SystemExit(main())
