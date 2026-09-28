#!/usr/bin/env python3
import argparse, hashlib, json, os, tempfile
from pathlib import Path

def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True); fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    with os.fdopen(fd, "w", encoding="utf-8") as handle: json.dump(value, handle, indent=2); handle.flush(); os.fsync(handle.fileno())
    os.replace(tmp, path)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--config", required=True); parser.add_argument("--output-dir", required=True); args=parser.parse_args()
    config=json.loads(Path(args.config).read_text()); root=Path(args.output_dir); (root/"assets").mkdir(parents=True); (root/"private").mkdir()
    data="group,value\nA,1\nA,3\nB,5\nB,7\n"; (root/"assets/data.csv").write_text(data)
    digest="sha256:"+hashlib.sha256(data.encode()).hexdigest()
    common={"task_type":"data.analysis.python.v1","assets":[{"id":"table","path":"data.csv","media_type":"text/csv","checksum":digest}]}
    tasks=[{**common,"task_id":"mean_value","input":{"user_task":"Calculate the overall mean of the value column and save a one-row analysis_summary.csv.","tables":[{"asset_id":"table","description":"Measurements by group","columns":["group","value"]}],"output_requirements":["Report the mean","Create analysis_summary.csv"]}}, {**common,"task_id":"group_count","input":{"user_task":"Count rows per group and save the counts as analysis_summary.csv.","tables":[{"asset_id":"table","description":"Measurements by group","columns":["group","value"]}],"output_requirements":["Report group counts","Create analysis_summary.csv"]}}]
    (root/"tasks.jsonl").write_text("".join(json.dumps(task)+"\n" for task in tasks)); atomic(root/"private/references.json", {"mean_value":"4.0","group_count":"A=2, B=2"})
    revision=config.get("data_revision","analysis-r1"); atomic(root/"manifest.json", {"protocol_version":"1.0","benchmark_id":"fixture_analysis","benchmark_version":"0.1.0","data_revision":revision,"split":config.get("split","test"),"task_types":["data.analysis.python.v1"],"tasks_file":"tasks.jsonl","assets_dir":"assets","private":{"references":"private/references.json","reference_version":revision}})
if __name__ == "__main__": main()
