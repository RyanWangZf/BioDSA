from __future__ import annotations
import argparse, json, shutil
from pathlib import Path
from bioagent_harbor_runtime import run_batch
from .agent import CoderAgent

def _worker(request: Path) -> int:
    d=json.loads(request.read_text()); w,o=Path(d["workspace"]),Path(d["output"]); w.mkdir(parents=True); o.mkdir(parents=True)
    r=CoderAgent(d["config"],w).run(d["item"]["instruction"],[str(Path("/app")/p) for p in d["item"].get("input_paths",[])])
    (o/"final_answer.md").write_text(r["final_answer"]); (o/"analysis.py").write_text("\n\n".join(r["generated_code"])); (o/"execution.json").write_text(json.dumps(r["execution_logs"],indent=2))
    for p in w.iterdir():
        if p.is_file() and p.name!="analysis.py": shutil.copy2(p,o/p.name)
    return 0

def _batch(d: dict) -> int:
    return run_batch(d,"bioagent_coder.harbor_runner")

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("request",type=Path); p.add_argument("--item-worker",action="store_true"); a=p.parse_args()
    return _worker(a.request) if a.item_worker else _batch(json.loads(a.request.read_text()))
if __name__=="__main__": raise SystemExit(main())
