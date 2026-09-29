import json, os, resource, subprocess, sys
from pathlib import Path
refs={x["item_id"]:x for x in map(json.loads,Path("/tests/references/references.jsonl").read_text().splitlines())}
selected=[x for x in os.environ.get("BIOAGENT_ITEM_IDS","").split(",") if x] or list(refs); preds={}
p=Path("/app/submission/predictions.jsonl")
if p.is_file():
    for line in p.read_text().splitlines():
        try:
            row=json.loads(line); preds.setdefault(row["item_id"],row)
        except Exception: pass
results=[]
def restrict_submission():
    resource.setrlimit(resource.RLIMIT_CPU,(60,60)); resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3)); resource.setrlimit(resource.RLIMIT_FSIZE,(256*1024**2,256*1024**2)); os.setgroups([]); os.setgid(65534); os.setuid(65534)
for item_id in selected:
    pred=preds.get(item_id)
    if pred is None: results.append({"item_id":item_id,"status":"missing","score":0.0}); continue
    if pred.get("status")!="completed": results.append({"item_id":item_id,"status":pred.get("status","agent_error"),"score":0.0}); continue
    code=Path("/app/submission")/pred["artifacts_dir"]/"analysis.py"
    if not code.is_file(): results.append({"item_id":item_id,"status":"missing","score":0.0}); continue
    try: proc=subprocess.run([sys.executable,"/tests/run_submission.py",str(code)],cwd="/tmp",capture_output=True,text=True,timeout=60,preexec_fn=restrict_submission)
    except subprocess.TimeoutExpired: results.append({"item_id":item_id,"status":"timeout","score":0.0}); continue
    if proc.returncode: results.append({"item_id":item_id,"status":"agent_error","score":0.0,"error":"submitted code failed"}); continue
    results.append({"item_id":item_id,"status":"unscorable","score":None,"reason":"safe source-assertion conversion pending"})
counts={k:sum(x["status"]==k for x in results) for k in ("scored","missing","timeout","agent_error","grading_error","unscorable")}
summary={"total":len(selected),"attempted":len(selected)-counts["missing"],"completed":sum(x["status"] in {"scored","unscorable"} for x in results),**counts,"metric_scope":"partial","accuracy":None}
logs=Path("/logs/verifier"); logs.mkdir(parents=True,exist_ok=True); (logs/"per_item_results.jsonl").write_text("".join(json.dumps(x)+"\n" for x in results)); (logs/"summary.json").write_text(json.dumps(summary,indent=2)); (logs/"reward.txt").write_text("0.0")
