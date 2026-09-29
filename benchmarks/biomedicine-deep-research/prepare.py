"""Prepare pinned BDR data without rewriting Harbor task definitions."""
from __future__ import annotations
import argparse, json, shutil
from collections import Counter
from pathlib import Path

REVISION = "f3e34ee8ccde8ea15c98f55dae871e63ef8bc5b2"
HERE = Path(__file__).resolve().parent
def read(path): return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
def check_static(task):
    names = ["instruction.md", "task.toml", "environment/Dockerfile", "tests/Dockerfile", "tests/test.sh"]
    missing = [name for name in names if not (task / name).is_file()]
    if missing: raise FileNotFoundError(f"{task}: missing maintained files: {', '.join(missing)}")

def prepare(source):
    labels = {row["example_id"]: row for row in read(source / "private/eval_labels.jsonl")}
    verifier_rows = read(source / "public/verifier/cases.jsonl")
    subsets = sorted(path.stem for path in (source / "public/development/fit").glob("*.jsonl"))
    for subset in subsets:
        task = HERE / "tasks" / subset; check_static(task); public, references, counts = [], [], {}
        for split in ("fit", "tune"):
            rows = read(source / f"public/development/{split}/{subset}.jsonl"); counts[split] = len(rows)
            for row in rows:
                item = {key: value for key, value in row.items() if key != "label"}; item.update(item_id=row["example_id"], source_split=split, instruction=row["prompt"]); public.append(item)
                references.append({"item_id": row["example_id"], "subset": subset, "label": row.get("label"), "task_type": row["task_type"], "valid_options": row.get("valid_options", []), "source_split": split})
        rows = [row for row in verifier_rows if row["benchmark"] == subset]; counts["verifier"] = len(rows)
        for row in rows:
            item = dict(row); item.update(item_id=row["example_id"], source_split="verifier", instruction=row["prompt"]); public.append(item); label = labels.get(row["example_id"])
            references.append({"item_id": row["example_id"], "subset": subset, "label": None if label is None else label.get("target"), "task_type": row["task_type"], "valid_options": row.get("valid_options", []), "source_split": "verifier"})
        write(task / "data/items.jsonl", public); write(task / "environment/data/items.jsonl", public); write(task / "tests/references/references.jsonl", references)
        blocked = [{"item_id": row["item_id"], "reason": "source label unavailable"} for row in references if row["label"] is None]
        blocked += [{"item_id": row["item_id"], "reason": "source revision defines proposed PMIDs but no retrieval metric or ranking rule"} for row in references if row["task_type"] == "evidence_gap_retrieval"]
        split_metadata = {}
        for split, count in counts.items():
            selected = [row for row in references if row["source_split"] == split]; blocked_count = sum(row["label"] is None or row["task_type"] == "evidence_gap_retrieval" for row in selected)
            split_metadata[split] = {"source_count": count, "included_count": count, "runnable_count": count, "scorable_count": count - blocked_count, "oracle_verified": count - blocked_count, "live_verified": 0, "blocked_count": blocked_count}
        manifest = {"source_repo": "zifeng-ai/biomedicine-deep-research", "source_revision": REVISION, "subset": subset, "splits": split_metadata, "source_count": len(public), "included_count": len(public), "runnable_count": len(public), "scorable_count": len(public) - len(blocked), "oracle_verified": len(public) - len(blocked), "live_verified": 0, "blocked_count": len(blocked), "task_types": dict(Counter(row["task_type"] for row in public)), "blocked": blocked}
        (task / "data/manifest.json").write_text(json.dumps(manifest, indent=2)); shutil.copy2(task / "data/manifest.json", task / "environment/data/manifest.json")
        shutil.copy2(HERE / "scoring/grade.py", task / "tests/grade.py"); (task / "tests/run_submission.py").write_text("# unused for this task\n")
    print(f"Prepared {len(subsets)} BDR subset tasks")

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--source-cache", type=Path); args = parser.parse_args()
    if args.source_cache: source = args.source_cache / f"datasets--zifeng-ai--biomedicine-deep-research/snapshots/{REVISION}"
    else:
        from huggingface_hub import snapshot_download
        source = Path(snapshot_download("zifeng-ai/biomedicine-deep-research", repo_type="dataset", revision=REVISION, allow_patterns=["public/**/*.jsonl", "private/eval_labels.jsonl"]))
    prepare(source)
if __name__ == "__main__": main()
