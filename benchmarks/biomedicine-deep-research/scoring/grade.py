"""Trusted Biomedical Deep Research batch grader."""
from __future__ import annotations
import json, os, re, sys
from collections import Counter, defaultdict
from pathlib import Path

FINAL_RE=re.compile(r"<BIOMED_FINAL>\s*(\{.*?\})\s*</BIOMED_FINAL>",re.S)
VALID_SPLITS={"fit","tune","verifier"}
RETRIEVAL_LIMIT=30

def parse_answer(text,ref):
    matches=FINAL_RE.findall(str(text or ""))
    if len(matches)!=1:raise ValueError("exactly one BIOMED_FINAL JSON object is required")
    try:payload=json.loads(matches[0])
    except json.JSONDecodeError as exc:raise ValueError("BIOMED_FINAL is not valid JSON") from exc
    kind=ref["task_type"];key="proposed_pmids" if kind=="evidence_gap_retrieval" else "selected_options"
    if set(payload)!={key} or not isinstance(payload[key],list) or not all(isinstance(x,str) and x.strip() for x in payload[key]):raise ValueError(f"{key} must be the only field and contain non-empty strings")
    values=[x.strip() for x in payload[key]]
    if kind in {"single_choice","multi_select"}:
        values=[x.upper() for x in values]
        if len(values)!=len(set(values)):raise ValueError("duplicate answer values are invalid")
        if any(x not in set(ref["valid_options"]) for x in values):raise ValueError("answer contains an unknown option")
        if kind=="single_choice" and len(values)!=1:raise ValueError("single_choice requires exactly one option")
    else:
        if len(values)>RETRIEVAL_LIMIT:raise ValueError(f"evidence retrieval accepts at most {RETRIEVAL_LIMIT} PMIDs")
        if any(not re.fullmatch(r"[1-9][0-9]*", value) for value in values):raise ValueError("proposed_pmids must contain bare numeric PubMed IDs")
        if len(values)!=len(set(values)):raise ValueError("duplicate answer values are invalid")
    return values

def load_predictions(path):
    predictions,malformed,duplicates={},[],[]
    if not path.is_file():return predictions,malformed,duplicates
    for number,line in enumerate(path.read_text().splitlines(),1):
        try:
            row=json.loads(line);item_id=row["item_id"]
            if item_id in predictions:duplicates.append(item_id)
            else:predictions[item_id]=row
        except Exception:malformed.append(number)
    return predictions,malformed,duplicates

def metrics(rows,global_error=False):
    counts=Counter(x["status"] for x in rows);valid=[x for x in rows if x["status"] in {"scored","missing","agent_timeout","agent_error"}]
    incomplete=counts["unscorable"] or counts["grading_error"] or global_error
    return {"expected_total":len(rows),"attempted":len(rows)-counts["missing"],"validly_evaluated":len(valid),"missing":counts["missing"],"agent_timeout":counts["agent_timeout"],"agent_error":counts["agent_error"],"unscorable":counts["unscorable"],"grading_error":counts["grading_error"]+int(global_error),"mean_score":None if incomplete or not rows else sum((x["score"] or 0) for x in valid)/len(rows)}

def grade(refs,selected,predictions,malformed=None,duplicates=None):
    malformed=malformed or [];duplicates=duplicates or [];unknown=sorted(set(predictions)-set(selected));results=[]
    for item_id in selected:
        ref,pred=refs[item_id],predictions.get(item_id);base={"item_id":item_id,"subset":ref["subset"],"split":ref["source_split"],"task_type":ref["task_type"]}
        if pred is None:results.append({**base,"status":"missing","score":0.0,"error":"prediction missing"});continue
        state=pred.get("status")
        if state=="timeout":results.append({**base,"status":"agent_timeout","score":0.0,"error":pred.get("error")});continue
        if state!="completed":results.append({**base,"status":"agent_error","score":0.0,"error":pred.get("error") or f"agent status {state}"});continue
        if ref.get("label") is None:results.append({**base,"status":"unscorable","score":None,"error":"source label unavailable"});continue
        try:answer=parse_answer(pred.get("final_answer"),ref)
        except ValueError as exc:results.append({**base,"status":"scored","score":0.0,"error":str(exc)});continue
        if ref["task_type"]=="evidence_gap_retrieval":
            expected={str(x).strip() for x in ref["label"]["proposed_pmids"]};hits=expected & set(answer[:RETRIEVAL_LIMIT]);score=len(hits)/len(expected)
            results.append({**base,"status":"scored","score":score,"metric":f"recall@{RETRIEVAL_LIMIT}","hits":len(hits),"reference_pmids":len(expected),"retrieved_pmids":len(answer),"max_recall_at_30":min(RETRIEVAL_LIMIT,len(expected))/len(expected)})
        else:
            expected=[str(x).strip().upper() for x in ref["label"]["selected_options"]]
            score=float(answer==expected) if ref["task_type"]=="single_choice" else float(set(answer)==set(expected))
            results.append({**base,"status":"scored","score":score,"metric":"exact_match"})
    global_error=bool(malformed or duplicates or unknown)
    if global_error:results.append({"item_id":"<predictions>","subset":None,"split":None,"task_type":None,"status":"grading_error","score":None,"error":{"malformed_lines":malformed,"duplicate_ids":duplicates,"unknown_ids":unknown}})
    expected_rows=[x for x in results if x["item_id"]!="<predictions>"];by_split=defaultdict(list)
    for row in expected_rows:by_split[row["split"]].append(row)
    summary={**metrics(expected_rows,global_error),"malformed_lines":malformed,"duplicate_prediction_ids":duplicates,"unknown_prediction_ids":unknown,"by_split":{key:metrics(rows) for key,rows in sorted(by_split.items())}}
    retrieval=bool(selected) and all(refs[item_id]["task_type"]=="evidence_gap_retrieval" for item_id in selected);summary["primary_metric"]="mean_recall@30" if retrieval else "accuracy";summary["primary_score"]=summary["mean_score"]
    if retrieval:
        summary["mean_recall_at_30"]=summary["mean_score"]
        maxima=[min(RETRIEVAL_LIMIT,len(refs[item_id]["label"]["proposed_pmids"]))/len(refs[item_id]["label"]["proposed_pmids"]) for item_id in selected if refs[item_id].get("label")]
        summary["mean_max_recall_at_30"]=sum(maxima)/len(selected) if len(maxima)==len(selected) and selected else None
    else:summary["accuracy"]=summary["mean_score"]
    return results,summary

def main():
    refs={x["item_id"]:x for x in map(json.loads,Path("/tests/references/references.jsonl").read_text().splitlines())};split=os.environ.get("BIOAGENT_SPLIT") or None
    if split not in VALID_SPLITS|{None}:raise SystemExit(f"invalid BIOAGENT_SPLIT: {split}")
    eligible={key:ref for key,ref in refs.items() if split is None or ref["source_split"]==split};explicit=[x for x in os.environ.get("BIOAGENT_ITEM_IDS","").split(",") if x]
    if len(explicit)!=len(set(explicit)):raise SystemExit("trusted selection contains duplicate IDs")
    subset=next(iter(refs.values()))["subset"] if refs else "";local=[x for x in explicit if x.startswith(f"bdr-{subset}-")];unknown_selection=sorted(set(local)-set(eligible))
    if unknown_selection:raise SystemExit(f"unknown trusted item IDs for {subset}: {unknown_selection}")
    selected=local if explicit else list(eligible)
    if explicit and not selected:raise SystemExit(f"no trusted item ID belongs to this dataset task and split {split}")
    predictions,malformed,duplicates=load_predictions(Path("/app/submission/predictions.jsonl"));results,summary=grade(refs,selected,predictions,malformed,duplicates);summary["selection_split"]=split
    logs=Path("/logs/verifier");logs.mkdir(parents=True,exist_ok=True);(logs/"per_item_results.jsonl").write_text("".join(json.dumps(x)+"\n" for x in results));(logs/"summary.json").write_text(json.dumps(summary,indent=2))
    if summary["primary_score"] is None:print("evaluation incomplete; see summary.json",file=sys.stderr);return 2
    (logs/"reward.txt").write_text(str(summary["primary_score"]));return 0

if __name__=="__main__":raise SystemExit(main())
