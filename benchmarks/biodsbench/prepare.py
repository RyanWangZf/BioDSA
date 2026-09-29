"""Prepare pinned BioDSBench data without rewriting Harbor task definitions."""
from __future__ import annotations
import argparse, csv, json, shutil, sys, tarfile
from pathlib import Path

REVISION = "e59af82ee9461db78ed399544ec8520afeb02ce5"
ORACLE_FAILURES = {"28481359_4", "28481359_5", "28481359_7", "28481359_8", "28472509_4", "37699004_1"}
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "scoring"))
from compile_assertions import build  # noqa: E402

def read(path): return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
def check_static(task):
    names = ["instruction.md", "task.toml", "environment/Dockerfile", "tests/Dockerfile", "tests/test.sh"]
    missing = [name for name in names if not (task / name).is_file()]
    if missing: raise FileNotFoundError(f"{task}: missing maintained files: {', '.join(missing)}")

def prepare_metadata(source):
    for language, filename in (("python", "python_tasks_with_class.jsonl"), ("r", "R_tasks_with_class.jsonl")):
        task = HERE / "tasks" / f"biodsbench-{language}"
        check_static(task)
        rows = read(source / filename)
        scoring = {x["item_id"]: x for x in build(rows)} if language == "python" else {}
        public, references, blocked = [], [], []
        for row in rows:
            tables = json.loads(row["tables"]) if isinstance(row["tables"], str) else row["tables"]
            paths = [f"data/inputs/{row['study_ids']}/{Path(name).name}" for name in tables]
            prompt = row["queries"] + "\n\nInput files:\n" + "\n".join(f"- /app/{path}" for path in paths)
            if row.get("code_histories"): prompt += "\n\nPermitted prior code:\n" + row["code_histories"]
            item_id = row["unique_question_ids"]
            item = {"item_id": item_id, "source_split": "benchmark", "instruction": prompt, "input_paths": paths}
            if language == "python": item["code_history"] = row.get("code_histories") or ""
            item.update(language=language, study_id=row["study_ids"], analysis_types=row["analysis_types"])
            public.append(item)
            item_scoring = scoring.get(item_id)
            references.append({"item_id": item_id, "study_id": row["study_ids"], "reference_answer": row.get("reference_answer"), "code_history": row.get("code_histories") or "", "scoring": item_scoring})
            if language == "r": blocked.append({"item_id": item_id, "reason": "R runtime is not supported by the migrated agents"})
            elif not item_scoring["supported"]: blocked.append({"item_id": item_id, "reason": item_scoring["blocking_reason"]})
        write(task / "data/items.jsonl", public); write(task / "environment/data/items.jsonl", public)
        write(task / "tests/references/references.jsonl", references)
        failures = [] if language != "python" else [{"item_id": item_id, "reason": "pinned source reference implementation fails before or during its original assertions; grader remains available"} for item_id in sorted(ORACLE_FAILURES)]
        scorable = len(public) - len(blocked) if language == "python" else 0
        manifest = {"source_repo": "zifeng-ai/BioDSBench", "source_revision": REVISION, "subset": language, "splits": {"benchmark": {"source_count": len(public), "included_count": len(public), "runnable_count": len(public) if language == "python" else 0, "scorable_count": scorable, "oracle_verified": scorable - len(failures), "live_verified": 0, "blocked_count": len(blocked)}}, "blocked": blocked, "oracle_failures": failures}
        (task / "data/manifest.json").write_text(json.dumps(manifest, indent=2))
        shutil.copy2(task / "data/manifest.json", task / "environment/data/manifest.json")
        if language == "python":
            shutil.copy2(HERE / "scoring/grade.py", task / "tests/grade.py")
            shutil.copy2(HERE / "scoring/run_submission.py", task / "tests/run_submission.py")
        else:
            shutil.copy2(HERE / "scoring/grade_r_unsupported.py", task / "tests/grade.py")
            (task / "tests/run_submission.py").write_text("# R execution is not supported\n")

def stage_tables(source):
    for language, archive_name in (("python", "raw_patient_data_for_python_tasks.tar.gz"), ("r", "raw_patient_data_for_R_tasks.tar.gz")):
        archive = source / "data_files" / archive_name
        if not archive.is_file(): continue
        cache = source / f"extracted-{language}"; cache.mkdir(exist_ok=True)
        if not (cache / ".complete").exists():
            with tarfile.open(archive) as handle: handle.extractall(cache, filter="data")
            (cache / ".complete").touch()
        task = HERE / "tasks" / f"biodsbench-{language}"; files = list(cache.rglob("*"))
        for item in read(task / "data/items.jsonl"):
            destination = task / "environment/data/inputs" / item["study_id"]; destination.mkdir(parents=True, exist_ok=True)
            for relative in item["input_paths"]:
                name = Path(relative).name
                matches = [p for p in files if p.is_file() and p.stem == Path(name).stem and (language == "r" or item["study_id"] in str(p))]
                if len(matches) != 1: continue
                source_file = matches[0]
                if source_file.suffix in {".txt", ".xena", ".tsv"} and Path(name).suffix == ".csv":
                    with source_file.open(newline="", errors="replace") as src, (destination / name).open("w", newline="") as dst: csv.writer(dst).writerows(csv.reader(src, delimiter="\t"))
                else: shutil.copy2(source_file, destination / name)
                verifier = task / "tests/data/inputs" / item["study_id"]; verifier.mkdir(parents=True, exist_ok=True)
                shutil.copy2(destination / name, verifier / name)

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--source-cache", type=Path); parser.add_argument("--skip-large-data", action="store_true"); args = parser.parse_args()
    if args.source_cache: source = args.source_cache / f"datasets--zifeng-ai--BioDSBench/snapshots/{REVISION}"
    else:
        from huggingface_hub import snapshot_download
        source = Path(snapshot_download("zifeng-ai/BioDSBench", repo_type="dataset", revision=REVISION, allow_patterns=["*.jsonl"] if args.skip_large_data else ["*.jsonl", "data_files/*.tar.gz"]))
    prepare_metadata(source)
    if not args.skip_large_data: stage_tables(source)
    print("Prepared BioDSBench Python and R data")
if __name__ == "__main__": main()
