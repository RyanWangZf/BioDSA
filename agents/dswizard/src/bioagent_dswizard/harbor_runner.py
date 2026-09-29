from __future__ import annotations
import argparse, json, shutil
from pathlib import Path
from bioagent_harbor_runtime import run_batch
from .agent import DSWizardAgent

def _worker(request: Path)->int:
 d=json.loads(request.read_text()); w,o=Path(d["workspace"]),Path(d["output"]); w.mkdir(parents=True); o.mkdir(parents=True); item=d["item"]
 data_root=Path("/app/data/inputs")/item["study_id"] if item.get("study_id") else None; links=[Path("/workdir"),w/"workdir"] if data_root and data_root.is_dir() else []
 for link in links:
  if link.is_symlink():link.unlink()
  elif link.exists():raise RuntimeError(f"refusing to replace existing replay path: {link}")
  link.symlink_to(data_root,target_is_directory=True)
 try:r=DSWizardAgent(d["config"],w).run(item["instruction"],[str(Path("/app")/p) for p in item.get("input_paths",[])],item.get("code_history", ""))
 finally:
  for link in links:
   if link.is_symlink():link.unlink()
 (o/"final_answer.md").write_text(r["final_answer"]); (o/"analysis_plan.md").write_text(r["analysis_plan"]); (o/"exploration.py").write_text(r["exploration_code"]); (o/"analysis.py").write_text(r["final_program"]); (o/"execution.json").write_text(json.dumps(r["execution_logs"],indent=2))
 for p in w.iterdir():
  if p.is_file(): shutil.copy2(p,o/p.name)
 return 0

def _batch(d:dict)->int:
 return run_batch(d,"bioagent_dswizard.harbor_runner")

def main()->int:
 p=argparse.ArgumentParser(); p.add_argument("request",type=Path); p.add_argument("--item-worker",action="store_true"); a=p.parse_args(); return _worker(a.request) if a.item_worker else _batch(json.loads(a.request.read_text()))
if __name__=="__main__": raise SystemExit(main())
