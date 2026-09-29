"""Produce a complete formal leaderboard result from one Harbor job directory."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE_REVISION = "f3e34ee8ccde8ea15c98f55dae871e63ef8bc5b2"
FORMAL_EXPECTED_COUNTS = {
    "drug-regimen-design": 5, "hle-biomedicine": 8, "hle-medicine": 6,
    "in-vivo-metabolic-flux-response": 5, "labbench-dbqa": 10,
    "labbench-litqa2": 5, "moa-pathway-reasoning": 5,
    "sample-size-estimation": 5, "supergpqa-hard-medicine": 35,
    "surrogate-endpoint-discovery": 3, "target-identification": 5,
    "trqa-lit": 35,
}
FORMAL_SUBSETS = set(FORMAL_EXPECTED_COUNTS)


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _expected(subset: str) -> set[str]:
    rows = [json.loads(line) for line in (HERE / f"tasks/{subset}/data/items.jsonl").read_text().splitlines() if line]
    return {row["item_id"] for row in rows if row.get("source_split") == "verifier"}


def summarize(job_dir: Path) -> dict:
    job = _read_json(job_dir / "config.json")
    configured = {Path(task["path"]).name for task in job.get("tasks", [])}
    problems = []
    if configured != FORMAL_SUBSETS:
        problems.append(f"formal subset mismatch: missing={sorted(FORMAL_SUBSETS-configured)}, extra={sorted(configured-FORMAL_SUBSETS)}")
    if job.get("verifier", {}).get("env", {}).get("BIOAGENT_SPLIT") != "verifier":
        problems.append("job verifier selection is not split=verifier")
    for subset, count in FORMAL_EXPECTED_COUNTS.items():
        actual = len(_expected(subset))
        if actual != count: problems.append(f"{subset}: pinned verifier inventory has {actual} items, expected {count}")
        manifest = _read_json(HERE / f"tasks/{subset}/data/manifest.json")
        if manifest.get("source_revision") != SOURCE_REVISION: problems.append(f"{subset}: source revision mismatch")

    groups = defaultdict(dict)
    for trial in sorted(path for path in job_dir.iterdir() if path.is_dir() and (path / "config.json").is_file()):
        config = _read_json(trial / "config.json")
        subset = Path(config["task"]["path"]).name
        agent = config["agent"]
        key = (agent.get("import_path") or agent.get("name"), agent.get("model_name"), agent.get("kwargs", {}).get("provider"))
        if subset in groups[key]:
            problems.append(f"duplicate trial for {key} and {subset}")
        groups[key][subset] = trial
    if not groups:
        problems.append("no Harbor trial directories found")

    evaluations = []
    for (agent, model, provider), trials in sorted(groups.items(), key=lambda pair: str(pair[0])):
        missing_trials = FORMAL_SUBSETS - set(trials)
        extra_trials = set(trials) - FORMAL_SUBSETS
        errors = []
        if missing_trials: errors.append(f"missing trials: {sorted(missing_trials)}")
        if extra_trials: errors.append(f"unexpected trials: {sorted(extra_trials)}")
        totals = Counter(); subset_results = {}; correct = 0.0; expected_total = 0; versions = set()
        for subset in sorted(FORMAL_SUBSETS & set(trials)):
            trial = trials[subset]; expected = _expected(subset); expected_total += len(expected)
            result_path = trial / "result.json"; per_item_path = trial / "verifier/per_item_results.jsonl"; summary_path = trial / "verifier/summary.json"
            if not result_path.is_file() or not per_item_path.is_file() or not summary_path.is_file():
                errors.append(f"{subset}: missing result or verifier artifacts"); continue
            trial_result = _read_json(result_path)
            if trial_result.get("agent_info", {}).get("version"): versions.add(trial_result["agent_info"]["version"])
            if trial_result.get("exception_info"):
                errors.append(f"{subset}: Harbor trial exception {trial_result['exception_info'].get('exception_type')}")
            rows = [json.loads(line) for line in per_item_path.read_text().splitlines() if line]
            ids = [row.get("item_id") for row in rows if row.get("item_id") != "<predictions>"]
            if len(ids) != len(set(ids)) or set(ids) != expected:
                errors.append(f"{subset}: per-item denominator differs from trusted verifier inventory")
            summary = _read_json(summary_path)
            if summary.get("selection_split") != "verifier": errors.append(f"{subset}: verifier summary split is not verifier")
            if summary.get("expected_total") != len(expected): errors.append(f"{subset}: expected_total mismatch")
            if summary.get("grading_error") or summary.get("unscorable") or summary.get("accuracy") is None:
                errors.append(f"{subset}: incomplete grading")
            counts = Counter(row.get("status", "unknown") for row in rows if row.get("item_id") != "<predictions>")
            score = sum(float(row.get("score") or 0) for row in rows if row.get("item_id") != "<predictions>")
            correct += score; totals.update(counts)
            subset_results[subset] = {"expected_total": len(expected), "correct": score, "accuracy": score / len(expected) if expected else None, "statuses": dict(sorted(counts.items()))}
        valid = not problems and not errors and set(trials) == FORMAL_SUBSETS
        evaluations.append({"valid": valid, "agent": agent, "agent_versions": sorted(versions), "provider": provider, "model": model, "expected_total": expected_total, "correct": correct, "micro_accuracy": correct / expected_total if valid and expected_total else None, "statuses": dict(sorted(totals.items())), "subsets": subset_results, "errors": errors})
    return {"valid": not problems and bool(evaluations) and all(row["valid"] for row in evaluations), "job_name": job.get("job_name"), "source_revision": SOURCE_REVISION, "formal_split": "verifier", "formal_subsets": sorted(FORMAL_SUBSETS), "errors": problems, "evaluations": evaluations}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("job_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = summarize(args.job_dir)
    payload = json.dumps(result, indent=2)
    if args.output: args.output.write_text(payload + "\n")
    else: print(payload)
    return 0 if result["valid"] else 2


if __name__ == "__main__": raise SystemExit(main())
