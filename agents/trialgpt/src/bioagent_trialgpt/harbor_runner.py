from __future__ import annotations
import argparse,json,traceback
from pathlib import Path
from bioagent_harbor_runtime import run_batch
from .workflow import TrialGPTAgent

def worker(path:Path)->int:
 d=json.loads(path.read_text());o=Path(d["output"]);w=Path(d["workspace"]);o.mkdir(parents=True,exist_ok=True);w.mkdir(parents=True,exist_ok=True)
 config={**d["config"],**d["item"].get("agent_config",{})}
 agent=TrialGPTAgent(config,w)
 try:r=agent.run(d["item"])
 except Exception as exc:
  (o/"trajectory.json").write_text(json.dumps(agent.trajectory,indent=2));(o/"failure.json").write_text(json.dumps({"type":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc()},indent=2));raise
 (o/"final_answer.md").write_text(r["final_answer"]);(o/"trajectory.json").write_text(json.dumps(r["trajectory"],indent=2));(o/"result.json").write_text(json.dumps(r,indent=2));(o/"usage.json").write_text(json.dumps(r.get("usage",{}),indent=2))
 for name,value in r.get("artifacts",{}).items():(o/name).write_text(value if isinstance(value,str) else json.dumps(value,indent=2))
 return 0

def main()->int:
 p=argparse.ArgumentParser();p.add_argument("request",type=Path);p.add_argument("--item-worker",action="store_true");a=p.parse_args()
 return worker(a.request) if a.item_worker else run_batch(json.loads(a.request.read_text()),"bioagent_trialgpt.harbor_runner",single_inputs=False)
if __name__=="__main__":raise SystemExit(main())
