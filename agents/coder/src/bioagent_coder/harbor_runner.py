from __future__ import annotations
import argparse, json, shutil, traceback
from pathlib import Path
from bioagent_harbor_runtime import run_batch
from .agent import CoderAgent

def _worker(request: Path) -> int:
    d=json.loads(request.read_text());w,o=Path(d["workspace"]),Path(d["output"]);w.mkdir(parents=True);o.mkdir(parents=True);item=d["item"]
    data_root=Path("/app/data/inputs")/item["study_id"] if item.get("study_id") else None;links=[Path("/workdir"),w/"workdir"] if data_root and data_root.is_dir() else []
    for link in links:
        if link.is_symlink():link.unlink()
        elif link.exists():raise RuntimeError(f"refusing to replace existing replay path: {link}")
        link.symlink_to(data_root,target_is_directory=True)
    try:r=CoderAgent(d["config"],w).run(item["instruction"],[str(Path("/app")/p) for p in item.get("input_paths",[])],item.get("code_history",""))
    except Exception as exc:
        for path in w.iterdir():
            if path.is_file():shutil.copy2(path,o/path.name)
        (o/"failure.json").write_text(json.dumps({"type":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc()},indent=2));raise
    finally:
        for link in links:
            if link.is_symlink():link.unlink()
    (o/"final_answer.md").write_text(r["final_answer"]); (o/"analysis.py").write_text(r["final_program"]); (o/"generated_code.py").write_text("\n\n".join(r["generated_code"])); (o/"execution.json").write_text(json.dumps(r["execution_logs"],indent=2))
    for p in w.iterdir():
        if p.is_file() and p.name!="analysis.py": shutil.copy2(p,o/p.name)
    return 0

def _batch(d: dict) -> int:
    return run_batch(d,"bioagent_coder.harbor_runner")

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("request",type=Path); p.add_argument("--item-worker",action="store_true"); a=p.parse_args()
    return _worker(a.request) if a.item_worker else _batch(json.loads(a.request.read_text()))
if __name__=="__main__": raise SystemExit(main())
