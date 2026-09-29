import json, os, re
from pathlib import Path

def norm(value):
    if isinstance(value, dict):
        value = value.get("selected_options", value.get("proposed_pmids", value))
    if isinstance(value, list): return sorted(str(x).strip().lower() for x in value)
    text = str(value or "").strip().lower()
    found = re.findall(r"(?<![a-z])[a-z](?![a-z])", text)
    return sorted(set(found)) if found else text

def answer_payload(text):
    matches = re.findall(r"<BIOMED_FINAL>\s*(\{.*?\})\s*</BIOMED_FINAL>", str(text or ""), re.S)
    if not matches: return text
    try: return json.loads(matches[-1])
    except json.JSONDecodeError: return text

refs = {x["item_id"]: x for x in map(json.loads, Path("/tests/references/references.jsonl").read_text().splitlines())}
selected = [x for x in os.environ.get("BIOAGENT_ITEM_IDS", "").split(",") if x] or list(refs)
preds, malformed = {}, []
path = Path("/app/submission/predictions.jsonl")
if path.is_file():
    for line in path.read_text().splitlines():
        try:
            row = json.loads(line); item_id = row["item_id"]
            if item_id in preds: malformed.append(item_id)
            else: preds[item_id] = row
        except Exception: malformed.append("<invalid>")
results = []
for item_id in selected:
    ref, pred = refs.get(item_id), preds.get(item_id)
    if ref is None: results.append({"item_id": item_id, "status": "grading_error", "error": "unknown trusted item id"}); continue
    if pred is None: results.append({"item_id": item_id, "status": "missing", "score": 0.0}); continue
    if pred.get("status") != "completed": results.append({"item_id": item_id, "status": pred.get("status", "agent_error"), "score": 0.0}); continue
    if ref.get("label") is None: results.append({"item_id": item_id, "status": "unscorable", "score": None}); continue
    results.append({"item_id": item_id, "status": "scored", "score": float(norm(answer_payload(pred.get("final_answer"))) == norm(ref["label"])), "task_type": ref["task_type"]})
unknown = sorted(set(preds) - set(selected))
counts = {k: sum(x["status"] == k for x in results) for k in ("scored", "missing", "timeout", "agent_error", "grading_error", "unscorable")}
scored = [x["score"] for x in results if x["status"] == "scored"]
invalid_scoring = counts["grading_error"] or counts["unscorable"] or malformed or unknown
summary = {"total": len(selected), "attempted": len(selected)-counts["missing"], "completed": sum(x["status"] in {"scored", "unscorable"} for x in results), **counts, "malformed_or_duplicate": malformed, "unknown_prediction_ids": unknown, "metric_scope": "complete" if not invalid_scoring else "partial", "accuracy": None if invalid_scoring or not selected else sum(scored)/len(selected), "scored_only_accuracy": sum(scored)/len(scored) if scored else None, "metric_denominator": len(selected), "scored_only_denominator": len(scored)}
logs=Path("/logs/verifier"); logs.mkdir(parents=True, exist_ok=True)
(logs/"per_item_results.jsonl").write_text("".join(json.dumps(x)+"\n" for x in results)); (logs/"summary.json").write_text(json.dumps(summary, indent=2)); (logs/"reward.txt").write_text(str(summary["accuracy"] or 0.0))
