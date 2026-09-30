from __future__ import annotations
import argparse, json, traceback
from pathlib import Path
from bioagent_harbor_runtime import run_batch
from .workflow import DeepEvidenceAgent

def _worker(request:Path)->int:
 d=json.loads(request.read_text()); w,o=Path(d["workspace"]),Path(d["output"]); w.mkdir(parents=True); o.mkdir(parents=True)
 item=d["item"];config={**d["config"],"task_type":item.get("task_type")};agent=DeepEvidenceAgent(config,w)
 try:r=agent.run(item["instruction"])
 except Exception as exc:
  (o/"trace.json").write_text(json.dumps(agent.trace,indent=2));(o/"memory_graph.json").write_text(json.dumps(agent.memory.data,indent=2));(o/"failure.json").write_text(json.dumps({"type":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc()},indent=2));raise
 usage=r.pop("usage")
 (o/"final_answer.md").write_text(r["final_answer"])
 for name,key in (("citations.json","citations"),("evidence.json","evidence"),("trace.json","trace"),("memory_graph.json","memory_graph"),("execution.json","execution_logs")): (o/name).write_text(json.dumps(r[key],indent=2))
 (o/"generated_code.py").write_text("\n\n".join(r["generated_code"])); (o/"usage.json").write_text(json.dumps(usage,indent=2)); return 0

def _batch(d:dict)->int:
 return run_batch(d,"bioagent_deepevidence.harbor_runner",single_inputs=False,valid_splits={"fit","tune","verifier"})

def main()->int:
 p=argparse.ArgumentParser(); p.add_argument("request",type=Path); p.add_argument("--item-worker",action="store_true"); a=p.parse_args(); return _worker(a.request) if a.item_worker else _batch(json.loads(a.request.read_text()))
if __name__=="__main__": raise SystemExit(main())
