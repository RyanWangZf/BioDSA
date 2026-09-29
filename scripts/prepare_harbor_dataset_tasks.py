"""Prepare the two pinned sources as dataset-level Harbor tasks."""
from __future__ import annotations
import argparse, csv, json, shutil, tarfile
from collections import Counter
from pathlib import Path

BIO_REV="e59af82ee9461db78ed399544ec8520afeb02ce5"
BDR_REV="f3e34ee8ccde8ea15c98f55dae871e63ef8bc5b2"
ROOT=Path(__file__).resolve().parents[1]
TOML='''schema_version = "1.4"\nartifacts = ["/app/submission"]\n[metadata]\nsource = "{source}"\ndataset_task = "{name}"\ncategory = "Science"\ntags = {tags}\n[verifier]\ntimeout_sec = 7200.0\nenvironment_mode = "separate"\nnetwork_mode = "no-network"\n[agent]\ntimeout_sec = 86400.0\nnetwork_mode = "public"\n[environment]\nbuild_timeout_sec = 1200.0\ncpus = 2\nmemory_mb = 4096\nstorage_mb = 16384\nnetwork_mode = "public"\n'''
INSTRUCTION="# Dataset batch evaluation\n\nRead /app/data/items.jsonl. Answer each selected item independently. The adapter writes incremental predictions to /app/submission/predictions.jsonl and item artifacts below /app/submission/items/<item-id>/.\n"
ENV='''FROM python:3.12-slim\nRUN pip install --no-cache-dir pandas==2.3.3 numpy==2.3.4 scipy==1.16.3 matplotlib==3.10.7 seaborn==0.13.2 statsmodels==0.14.5 lifelines==0.30.0\nCOPY data/ /app/data/\nWORKDIR /app\n'''
BDR_ENV='''FROM python:3.12-slim\nCOPY data/ /app/data/\nWORKDIR /app\n'''
TEST_DOCKER='''FROM python:3.12-slim\nCOPY test.sh grade.py run_submission.py /tests/\nCOPY references/ /tests/references/\nCOPY data/ /app/data/\nRUN chmod 700 /tests/references && chmod +x /tests/test.sh\nWORKDIR /app\n'''

def read(path): return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
def write(path,rows): path.parent.mkdir(parents=True,exist_ok=True); path.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows))
def base(path,name,source,tags,env):
    for d in (path/"data",path/"environment/data",path/"tests/references",path/"tests/data"): d.mkdir(parents=True,exist_ok=True)
    (path/"instruction.md").write_text(INSTRUCTION); (path/"task.toml").write_text(TOML.format(source=source,name=name,tags=json.dumps(tags))); (path/"environment/Dockerfile").write_text(env); (path/"tests/Dockerfile").write_text(TEST_DOCKER); (path/"tests/test.sh").write_text("#!/bin/sh\nset -eu\npython3 /tests/grade.py\n")

def bio(source):
    for lang,filename in (("python","python_tasks_with_class.jsonl"),("r","R_tasks_with_class.jsonl")):
        task=ROOT/f"benchmarks/biodsbench/tasks/biodsbench-{lang}"; base(task,task.name,f"zifeng-ai/BioDSBench@{BIO_REV}",["biomedicine",lang,"data-analysis"],ENV)
        public=[]; refs=[]; blocked=[]
        for row in read(source/filename):
            tables=json.loads(row["tables"]) if isinstance(row["tables"],str) else row["tables"]; paths=[f"data/inputs/{row['study_ids']}/{Path(x).name}" for x in tables]
            prompt=row["queries"]+"\n\nInput files:\n"+"\n".join("- /app/"+x for x in paths)
            if row.get("code_histories"): prompt+="\n\nPermitted prior code:\n"+row["code_histories"]
            public.append({"item_id":row["unique_question_ids"],"source_split":"benchmark","instruction":prompt,"input_paths":paths,"language":lang,"study_id":row["study_ids"],"analysis_types":row["analysis_types"]})
            refs.append({"item_id":row["unique_question_ids"],"reference_answer":row.get("reference_answer"),"test_cases":row.get("test_cases")})
            reason="R runtime is not supported by the migrated agents" if lang=="r" else "safe source-assertion conversion pending"
            blocked.append({"item_id":row["unique_question_ids"],"reason":reason})
        write(task/"data/items.jsonl",public); write(task/"environment/data/items.jsonl",public); write(task/"tests/references/references.jsonl",refs)
        manifest={"source_repo":"zifeng-ai/BioDSBench","source_revision":BIO_REV,"subset":lang,"splits":{"benchmark":{"source_count":len(public),"included_count":len(public),"runnable_count":len(public) if lang=="python" else 0,"scorable_count":0,"blocked_count":len(blocked)}},"blocked":blocked}
        (task/"data/manifest.json").write_text(json.dumps(manifest,indent=2)); shutil.copy2(task/"data/manifest.json",task/"environment/data/manifest.json"); (task/"tests/grade.py").write_text((ROOT/"scripts/harbor_biodsbench_grade.py").read_text()); (task/"tests/run_submission.py").write_text((ROOT/"scripts/run_biodsbench_submission.py").read_text())

def stage_bio_tables(source):
    for lang, archive_name in (("python","raw_patient_data_for_python_tasks.tar.gz"),("r","raw_patient_data_for_R_tasks.tar.gz")):
        archive=source/"data_files"/archive_name
        if not archive.is_file(): continue
        cache=source/f"extracted-{lang}"; cache.mkdir(exist_ok=True)
        marker=cache/".complete"
        if not marker.exists():
            with tarfile.open(archive) as tf: tf.extractall(cache,filter="data")
            marker.touch()
        task=ROOT/f"benchmarks/biodsbench/tasks/biodsbench-{lang}"; items=read(task/"data/items.jsonl")
        files=list(cache.rglob("*"))
        for item in items:
            dest=task/"environment/data/inputs"/item["study_id"]; dest.mkdir(parents=True,exist_ok=True)
            for rel in item["input_paths"]:
                name=Path(rel).name; stem=Path(name).stem
                matches=[p for p in files if p.is_file() and p.stem==stem and (lang=="r" or item["study_id"] in str(p))]
                if len(matches)!=1: continue
                input_file=matches[0]
                if input_file.suffix in {".txt",".xena",".tsv"} and Path(name).suffix==".csv":
                    with input_file.open(newline="",errors="replace") as src,(dest/name).open("w",newline="") as dst: csv.writer(dst).writerows(csv.reader(src,delimiter="\t"))
                else: shutil.copy2(input_file,dest/name)
                verifier_dest=task/"tests/data/inputs"/item["study_id"]; verifier_dest.mkdir(parents=True,exist_ok=True); shutil.copy2(dest/name,verifier_dest/name)

def bdr(source):
    labels={x["example_id"]:x for x in read(source/"private/eval_labels.jsonl")}; evals=read(source/"public/verifier/cases.jsonl")
    for subset in sorted(x.stem for x in (source/"public/development/fit").glob("*.jsonl")):
        task=ROOT/f"benchmarks/biomedicine-deep-research/tasks/{subset}"; base(task,subset,f"zifeng-ai/biomedicine-deep-research@{BDR_REV}",["biomedicine","evidence-synthesis",subset],BDR_ENV); public=[]; refs=[]; counts={}
        for split in ("fit","tune"):
            rows=read(source/f"public/development/{split}/{subset}.jsonl"); counts[split]=len(rows)
            for row in rows:
                item={k:v for k,v in row.items() if k!="label"}; item.update(item_id=row["example_id"],source_split=split,instruction=row["prompt"]); public.append(item); refs.append({"item_id":row["example_id"],"label":row.get("label"),"task_type":row["task_type"],"source_split":split})
        rows=[x for x in evals if x["benchmark"]==subset]; counts["verifier"]=len(rows)
        for row in rows:
            item=dict(row); item.update(item_id=row["example_id"],source_split="verifier",instruction=row["prompt"]); public.append(item); ref=labels.get(row["example_id"]); refs.append({"item_id":row["example_id"],"label":None if ref is None else ref.get("target"),"task_type":row["task_type"],"source_split":"verifier"})
        write(task/"data/items.jsonl",public); write(task/"environment/data/items.jsonl",public); write(task/"tests/references/references.jsonl",refs)
        blocked=[{"item_id":x["item_id"],"reason":"source label unavailable"} for x in refs if x["label"] is None]; manifest={"source_repo":"zifeng-ai/biomedicine-deep-research","source_revision":BDR_REV,"subset":subset,"splits":{s:{"source_count":n,"included_count":n,"runnable_count":n,"scorable_count":n,"blocked_count":0} for s,n in counts.items()},"source_count":len(public),"included_count":len(public),"runnable_count":len(public),"scorable_count":len(public)-len(blocked),"blocked_count":len(blocked),"task_types":dict(Counter(x["task_type"] for x in public)),"blocked":blocked}
        (task/"data/manifest.json").write_text(json.dumps(manifest,indent=2)); shutil.copy2(task/"data/manifest.json",task/"environment/data/manifest.json"); (task/"tests/grade.py").write_text((ROOT/"scripts/harbor_bdr_grade.py").read_text()); (task/"tests/run_submission.py").write_text("# unused for this task\n")

def main():
    p=argparse.ArgumentParser(); p.add_argument("--source-cache",type=Path); p.add_argument("--skip-large-data",action="store_true"); a=p.parse_args()
    if a.source_cache:
        bio_source=a.source_cache/f"datasets--zifeng-ai--BioDSBench/snapshots/{BIO_REV}"; bdr_source=a.source_cache/f"datasets--zifeng-ai--biomedicine-deep-research/snapshots/{BDR_REV}"
    else:
        from huggingface_hub import snapshot_download
        bio_source=Path(snapshot_download("zifeng-ai/BioDSBench",repo_type="dataset",revision=BIO_REV,allow_patterns=["*.jsonl","data_files/*.tar.gz"] if not a.skip_large_data else ["*.jsonl"]))
        bdr_source=Path(snapshot_download("zifeng-ai/biomedicine-deep-research",repo_type="dataset",revision=BDR_REV,allow_patterns=["public/**/*.jsonl","private/eval_labels.jsonl"]))
    bio(bio_source); bdr(bdr_source)
    if not a.skip_large_data: stage_bio_tables(bio_source)
    print("Prepared 15 dataset tasks")
if __name__=="__main__": main()
