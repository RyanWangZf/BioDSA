"""Create local verifier-only oracle submissions from ignored references."""
from __future__ import annotations
import argparse,json,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def clean(path): shutil.rmtree(path,ignore_errors=True);path.mkdir(parents=True)
def bio(output):
    clean(output); refs=[json.loads(x) for x in (ROOT/"benchmarks/biodsbench/tasks/biodsbench-python/tests/references/references.jsonl").read_text().splitlines()]
    rows=[]
    for ref in refs:
        item=output/"submission/items"/ref["item_id"];item.mkdir(parents=True)
        (item/"analysis.py").write_text("\n\n".join(x for x in (ref.get("code_history"),ref["reference_answer"]) if x))
        rows.append({"item_id":ref["item_id"],"status":"completed","artifacts_dir":f"items/{ref['item_id']}"})
    (output/"submission/predictions.jsonl").write_text("".join(json.dumps(x)+"\n" for x in rows))
def deep(output):
    clean(output)
    for task in sorted((ROOT/"benchmarks/biomedicine-deep-research/tasks").iterdir()):
        if not task.is_dir():continue
        refs_file=task/"tests/references/references.jsonl"
        if not refs_file.is_file():continue
        target=output/task.name/"submission";target.mkdir(parents=True);rows=[]
        for ref in map(json.loads,refs_file.read_text().splitlines()):
            key="proposed_pmids" if ref["task_type"]=="evidence_gap_retrieval" else "selected_options"
            answer=f"<BIOMED_FINAL>{json.dumps({key:ref['label'][key]})}</BIOMED_FINAL>"
            rows.append({"item_id":ref["item_id"],"status":"completed","final_answer":answer})
        (target/"predictions.jsonl").write_text("".join(json.dumps(x)+"\n" for x in rows))
def main():
    p=argparse.ArgumentParser();p.add_argument("--bio-output",type=Path,default=Path("/tmp/biodsbench-oracle"));p.add_argument("--deep-output",type=Path,default=Path("/tmp/deepevidence-oracles"));a=p.parse_args();bio(a.bio_output);deep(a.deep_output);print("Prepared verifier-only oracle submissions")
if __name__=="__main__":main()
