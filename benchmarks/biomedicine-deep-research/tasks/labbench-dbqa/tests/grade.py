"""Trusted Biomedical Deep Research batch grader."""
from __future__ import annotations
import json, os, re, sys
from collections import Counter, defaultdict
from pathlib import Path

FINAL_RE = re.compile(r"<BIOMED_FINAL>\s*(\{.*?\})\s*</BIOMED_FINAL>", re.S)
VALID_SPLITS = {"fit", "tune", "verifier"}

def parse_answer(text, ref):
    matches = FINAL_RE.findall(str(text or ""))
    if len(matches) != 1:
        raise ValueError("exactly one BIOMED_FINAL JSON object is required")
    try: payload = json.loads(matches[0])
    except json.JSONDecodeError as exc: raise ValueError("BIOMED_FINAL is not valid JSON") from exc
    kind = ref["task_type"]
    key = "proposed_pmids" if kind == "evidence_gap_retrieval" else "selected_options"
    if set(payload) != {key} or not isinstance(payload[key], list) or not all(isinstance(x, str) and x.strip() for x in payload[key]):
        raise ValueError(f"{key} must be the only field and contain non-empty strings")
    values = [x.strip() for x in payload[key]]
    if len(values) != len(set(values)):
        raise ValueError("duplicate answer values are invalid")
    if kind in {"single_choice", "multi_select"}:
        valid = set(ref["valid_options"])
        values = [x.upper() for x in values]
        if any(x not in valid for x in values): raise ValueError("answer contains an unknown option")
        if kind == "single_choice" and len(values) != 1: raise ValueError("single_choice requires exactly one option")
    return values

def load_predictions(path):
    predictions, malformed, duplicates = {}, [], []
    if not path.is_file(): return predictions, malformed, duplicates
    for number, line in enumerate(path.read_text().splitlines(), 1):
        try:
            row=json.loads(line); item_id=row["item_id"]
            if item_id in predictions: duplicates.append(item_id)
            else: predictions[item_id]=row
        except Exception: malformed.append(number)
    return predictions, malformed, duplicates

refs={x["item_id"]:x for x in map(json.loads,Path("/tests/references/references.jsonl").read_text().splitlines())}
split=os.environ.get("BIOAGENT_SPLIT") or None
if split not in VALID_SPLITS|{None}: raise SystemExit(f"invalid BIOAGENT_SPLIT: {split}")
eligible={i:r for i,r in refs.items() if split is None or r["source_split"]==split}
explicit=[x for x in os.environ.get("BIOAGENT_ITEM_IDS","").split(",") if x]
if len(explicit)!=len(set(explicit)): raise SystemExit("trusted selection contains duplicate IDs")
selected=[x for x in explicit if x in eligible] if explicit else list(eligible)
if explicit and not selected: raise SystemExit(f"no trusted item ID belongs to this dataset task and split {split}")
preds,malformed,duplicates=load_predictions(Path("/app/submission/predictions.jsonl"))
unknown=sorted(set(preds)-set(selected))
results=[]
for item_id in selected:
    ref,pred=refs[item_id],preds.get(item_id)
    base={"item_id":item_id,"subset":ref["subset"],"split":ref["source_split"],"task_type":ref["task_type"]}
    if pred is None: results.append({**base,"status":"missing","score":0.0,"error":"prediction missing"}); continue
    state=pred.get("status")
    if state=="timeout": results.append({**base,"status":"agent_timeout","score":0.0,"error":pred.get("error")}); continue
    if state!="completed": results.append({**base,"status":"agent_error","score":0.0,"error":pred.get("error") or f"agent status {state}"}); continue
    if ref.get("label") is None: results.append({**base,"status":"unscorable","score":None,"error":"source label unavailable"}); continue
    if ref["task_type"]=="evidence_gap_retrieval":
        results.append({**base,"status":"unscorable","score":None,"error":"source revision supplies PMIDs but no retrieval metric or ordering rule"}); continue
    try: answer=parse_answer(pred.get("final_answer"),ref)
    except ValueError as exc: results.append({**base,"status":"scored","score":0.0,"error":str(exc)}); continue
    expected=[str(x).strip().upper() for x in ref["label"]["selected_options"]]
    score=float(answer==expected) if ref["task_type"]=="single_choice" else float(set(answer)==set(expected))
    results.append({**base,"status":"scored","score":score})

if malformed or duplicates or unknown:
    results.append({"item_id":"<predictions>","subset":None,"split":split,"task_type":None,"status":"grading_error","score":None,"error":{"malformed_lines":malformed,"duplicate_ids":duplicates,"unknown_ids":unknown}})
counts=Counter(x["status"] for x in results)
by_split=defaultdict(list)
for row in results:
    if row["item_id"]!="<predictions>": by_split[row["split"]].append(row)
def metrics(rows):
    c=Counter(x["status"] for x in rows); valid=[x for x in rows if x["status"] in {"scored","missing","agent_timeout","agent_error"}]
    return {"expected_total":len(rows),"attempted":len(rows)-c["missing"],"validly_evaluated":len(valid),"missing":c["missing"],"agent_timeout":c["agent_timeout"],"agent_error":c["agent_error"],"unscorable":c["unscorable"],"grading_error":c["grading_error"],"accuracy":sum((x["score"] or 0) for x in valid)/len(rows) if rows and not c["unscorable"] and not c["grading_error"] else None}
summary={**metrics([x for x in results if x["item_id"]!="<predictions>"]),"selection_split":split,"malformed_lines":malformed,"duplicate_prediction_ids":duplicates,"unknown_prediction_ids":unknown,"by_split":{s:metrics(rows) for s,rows in sorted(by_split.items())}}
logs=Path("/logs/verifier"); logs.mkdir(parents=True,exist_ok=True)
(logs/"per_item_results.jsonl").write_text("".join(json.dumps(x)+"\n" for x in results)); (logs/"summary.json").write_text(json.dumps(summary,indent=2))
if summary["accuracy"] is None:
    print("evaluation incomplete; see summary.json",file=sys.stderr); raise SystemExit(2)
(logs/"reward.txt").write_text(str(summary["accuracy"]))
