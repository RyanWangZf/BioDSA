from __future__ import annotations
import json, os, shutil, signal, subprocess, sys, time
from pathlib import Path

def _terminate(process: subprocess.Popen) -> None:
    """Terminate the worker's whole process group, including orphaned children."""
    try: os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError: pass
    try: process.wait(timeout=5)
    except subprocess.TimeoutExpired: pass
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        try: os.killpg(process.pid,0)
        except ProcessLookupError: return
        time.sleep(.05)
    try: os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError: pass
    if process.poll() is None: process.wait()

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
    has_direct_selection="item_ids" in request
    has_dataset_selection="item_ids_by_dataset" in request
    selected=request.get("item_ids") if has_direct_selection else None
    by_dataset=request.get("item_ids_by_dataset") if has_dataset_selection else None
    if has_direct_selection and (not isinstance(selected,list) or not selected):
        raise ValueError("item_ids must be a non-empty list when provided")
    if has_dataset_selection and (not isinstance(by_dataset,dict) or not by_dataset):
        raise ValueError("item_ids_by_dataset must be a non-empty mapping when provided")
    if has_dataset_selection:
        manifest=json.loads((app/"data/manifest.json").read_text());subset=manifest["subset"]
        if subset not in by_dataset:raise ValueError(f"item_ids_by_dataset has no selection for {subset}")
        selected=by_dataset[subset]
        if not isinstance(selected,list) or not selected:raise ValueError(f"item_ids_by_dataset selection for {subset} must be non-empty")
    selected=selected or []
    known={item["item_id"] for item in items}; unknown=set(selected)-known
    if unknown:raise ValueError(f"unknown item_ids: {sorted(unknown)}")
    if selected:items=[item for item in items if item["item_id"] in set(selected)]
    if (has_direct_selection or has_dataset_selection) and not items:raise ValueError("trusted selection is empty for this dataset task")
    return items,False

def _failure(status: str, message: str) -> tuple[str, str]:
    return status, message[:2000]

def run_batch(request: dict, worker_module: str, *, single_inputs: bool=True, valid_splits: set[str] | None=None, app: Path=Path("/app"), python_executable: str | None=None) -> int:
    items,single_mode=_load_items(request,app,single_inputs,valid_splits);submission=app/"submission";submission.mkdir(exist_ok=True)
    python_executable=python_executable or sys.executable
    with (submission/"predictions.jsonl").open("w") as stream:
        for item in items:
            item_id=item["item_id"];workspace=app/"work/items"/item_id;output=submission/"items"/item_id;request_path=app/"work/requests"/f"{item_id}.json";request_path.parent.mkdir(parents=True,exist_ok=True)
            request_path.write_text(json.dumps({"item":item,"config":request["config"],"workspace":str(workspace),"output":str(output)}))
            process=subprocess.Popen([python_executable,"-m",worker_module,"--item-worker",str(request_path)],start_new_session=True);status,error="completed",None
            try:
                code=process.wait(timeout=float(request.get("item_timeout_seconds",300)))
                if code:status,error=_failure("agent_error",f"item worker exited {code}")
            except subprocess.TimeoutExpired:
                status,error=_failure("timeout","per-item timeout")
            except BaseException:
                _terminate(process);raise
            finally:_terminate(process)
            answer=None
            if status=="completed":
                try: answer=(output/"final_answer.md").read_text()
                except (OSError,UnicodeError) as exc: status,error=_failure("agent_error",f"invalid final_answer.md: {type(exc).__name__}: {exc}")
            row={"item_id":item_id,"status":status,"final_answer":answer,"artifacts_dir":f"items/{item_id}"}
            usage=output/"usage.json"
            if usage.is_file():
                try:
                    parsed=json.loads(usage.read_text())
                    if not isinstance(parsed,dict):raise ValueError("usage must be a JSON object")
                    row["usage"]=parsed
                except (OSError,UnicodeError,json.JSONDecodeError,ValueError) as exc:
                    status,error=_failure("agent_error",f"invalid usage.json: {type(exc).__name__}: {exc}");row["status"]=status;row["final_answer"]=None
            if error:row["error"]=error
            if single_mode and status=="completed":
                for artifact in output.iterdir() if output.is_dir() else ():
                    if artifact.is_file():shutil.copy2(artifact,submission/artifact.name)
            stream.write(json.dumps(row)+"\n");stream.flush();os.fsync(stream.fileno())
    return 0
