from __future__ import annotations
import json, os, shutil, signal, subprocess, sys
from pathlib import Path

def _terminate(process: subprocess.Popen) -> None:
    if process.poll() is not None:return
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL);process.wait()

def _load_items(request: dict, app: Path, single_inputs: bool, valid_splits: set[str] | None):
    item_file=app/"data/items.jsonl"; single_mode=not item_file.is_file()
    if single_mode:
        paths=[str(path.relative_to(app)) for path in (app/"inputs").rglob("*") if path.is_file()] if single_inputs and (app/"inputs").exists() else []
        return [{"item_id":"single","instruction":request["instruction"],"input_paths":paths}],True
    items=[json.loads(line) for line in item_file.read_text().splitlines() if line.strip()]
    split=request.get("split")
    if split is not None:
        if valid_splits is None or split not in valid_splits:raise ValueError(f"unsupported split: {split}")
        items=[item for item in items if item.get("source_split")==split]
    selected=request.get("item_ids") or []
    by_dataset=request.get("item_ids_by_dataset") or {}
    if by_dataset:
        manifest=json.loads((app/"data/manifest.json").read_text());subset=manifest["subset"]
        if subset not in by_dataset:raise ValueError(f"item_ids_by_dataset has no selection for {subset}")
        selected=by_dataset[subset]
    known={item["item_id"] for item in items}; unknown=set(selected)-known
    if unknown:raise ValueError(f"unknown item_ids: {sorted(unknown)}")
    if selected:items=[item for item in items if item["item_id"] in set(selected)]
    if (request.get("item_ids") or by_dataset) and not items:raise ValueError("trusted selection is empty for this dataset task")
    return items,False

def run_batch(request: dict, worker_module: str, *, single_inputs: bool=True, valid_splits: set[str] | None=None) -> int:
    app=Path("/app");items,single_mode=_load_items(request,app,single_inputs,valid_splits);submission=app/"submission";submission.mkdir(exist_ok=True)
    with (submission/"predictions.jsonl").open("w") as stream:
        for item in items:
            item_id=item["item_id"];workspace=app/"work/items"/item_id;output=submission/"items"/item_id;request_path=app/"work/requests"/f"{item_id}.json";request_path.parent.mkdir(parents=True,exist_ok=True)
            request_path.write_text(json.dumps({"item":item,"config":request["config"],"workspace":str(workspace),"output":str(output)}))
            process=subprocess.Popen([sys.executable,"-m",worker_module,"--item-worker",str(request_path)],start_new_session=True);status,error="completed",None
            try:
                code=process.wait(timeout=float(request.get("item_timeout_seconds",300)))
                if code:status,error="agent_error",f"item worker exited {code}"
            except subprocess.TimeoutExpired:
                status,error="timeout","per-item timeout";_terminate(process)
            except BaseException:
                _terminate(process);raise
            finally:_terminate(process)
            answer=(output/"final_answer.md").read_text() if status=="completed" else None
            row={"item_id":item_id,"status":status,"final_answer":answer,"artifacts_dir":f"items/{item_id}"}
            usage=output/"usage.json"
            if usage.is_file():row["usage"]=json.loads(usage.read_text())
            if error:row["error"]=error
            if single_mode and status=="completed":
                for artifact in output.iterdir():
                    if artifact.is_file():shutil.copy2(artifact,submission/artifact.name)
            stream.write(json.dumps(row)+"\n");stream.flush();os.fsync(stream.fileno())
    return 0
