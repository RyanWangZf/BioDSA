"""Produce a complete formal leaderboard result from one Harbor job directory."""
from __future__ import annotations

import argparse
import json
import math
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
    "trqa-lit": 35, "evidence-gap-discovery": 4,
}
FORMAL_SUBSETS = set(FORMAL_EXPECTED_COUNTS)


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _expected_rows(subset: str) -> dict[str, dict]:
    rows = [json.loads(line) for line in (HERE / f"tasks/{subset}/data/items.jsonl").read_text().splitlines() if line]
    return {row["item_id"]: row for row in rows if row.get("source_split") == "verifier"}


def _expected(subset: str) -> set[str]:
    return set(_expected_rows(subset))


def _agent_config(agent: dict) -> dict:
    return {key: agent.get(key) for key in ("import_path", "name", "model_name", "kwargs") if agent.get(key) is not None}


def _config_key(agent: dict) -> str:
    return json.dumps(_agent_config(agent), sort_keys=True, separators=(",", ":"))


def _load_lines(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip(): continue
        value = json.loads(line)
        if not isinstance(value, dict): raise ValueError(f"{path}:{number}: expected JSON object")
        rows.append(value)
    return rows


def summarize(job_dir: Path) -> dict:
    try: job = _read_json(job_dir / "config.json")
    except Exception as exc:return {"valid":False,"job_name":None,"source_revision":SOURCE_REVISION,"formal_split":"verifier","formal_subsets":sorted(FORMAL_SUBSETS),"errors":[f"invalid job config: {type(exc).__name__}: {exc}"],"evaluations":[]}
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

    expected_agents={}
    for index,agent in enumerate(job.get("agents",[])):
        try:key=_config_key(agent)
        except Exception as exc:problems.append(f"agent {index}: invalid config: {exc}");continue
        if key in expected_agents:problems.append(f"duplicate configured agent: {key}")
        else:expected_agents[key]=_agent_config(agent)
    if not expected_agents:problems.append("job config has no agents")
    groups = defaultdict(dict)
    for trial in sorted(path for path in job_dir.iterdir() if path.is_dir() and (path / "config.json").is_file()):
        try:
            config = _read_json(trial / "config.json");subset=Path(config["task"]["path"]).name;key=_config_key(config["agent"])
        except Exception as exc:problems.append(f"{trial.name}: invalid trial config: {type(exc).__name__}: {exc}");continue
        if key not in expected_agents:problems.append(f"{trial.name}: agent config is not present in job config");continue
        if subset in groups[key]:
            problems.append(f"duplicate trial for {key} and {subset}")
        groups[key][subset] = trial

    evaluations = []
    for key,agent_config in expected_agents.items():
        trials=groups.get(key,{})
        agent=agent_config.get("import_path") or agent_config.get("name");model=agent_config.get("model_name");provider=agent_config.get("kwargs",{}).get("provider")
        missing_trials = FORMAL_SUBSETS - set(trials)
        extra_trials = set(trials) - FORMAL_SUBSETS
        errors = []
        if missing_trials: errors.append(f"missing trials: {sorted(missing_trials)}")
        if extra_trials: errors.append(f"unexpected trials: {sorted(extra_trials)}")
        totals = Counter(); subset_results = {}; correct = 0.0; expected_total = 0; versions = set();choice_score=0.0;choice_total=0;retrieval_score=0.0;retrieval_total=0
        for subset in sorted(FORMAL_SUBSETS & set(trials)):
            trial=trials[subset];expected_rows=_expected_rows(subset);expected=set(expected_rows);expected_total+=len(expected)
            result_path = trial / "result.json"; per_item_path = trial / "verifier/per_item_results.jsonl"; summary_path = trial / "verifier/summary.json"
            if not result_path.is_file() or not per_item_path.is_file() or not summary_path.is_file():
                errors.append(f"{subset}: missing result or verifier artifacts"); continue
            try:trial_result=_read_json(result_path);rows=_load_lines(per_item_path);summary=_read_json(summary_path)
            except Exception as exc:errors.append(f"{subset}: invalid result artifact: {type(exc).__name__}: {exc}");continue
            if trial_result.get("agent_info", {}).get("version"): versions.add(trial_result["agent_info"]["version"])
            if trial_result.get("exception_info"):
                errors.append(f"{subset}: Harbor trial exception {trial_result['exception_info'].get('exception_type')}")
            ids = [row.get("item_id") for row in rows if row.get("item_id") != "<predictions>"]
            if len(ids) != len(set(ids)) or set(ids) != expected:
                errors.append(f"{subset}: per-item denominator differs from trusted verifier inventory")
            data_rows=[row for row in rows if row.get("item_id") in expected]
            allowed={"scored","missing","agent_timeout","agent_error"};validated_scores=[]
            for row in data_rows:
                item_id=row["item_id"];status=row.get("status");score=row.get("score");expected_row=expected_rows[item_id];expected_metric="recall@30" if subset=="evidence-gap-discovery" else "exact_match"
                if row.get("subset")!=subset or row.get("split")!="verifier" or row.get("task_type")!=expected_row.get("task_type"):errors.append(f"{subset}/{item_id}: row metadata mismatch")
                if status not in allowed:errors.append(f"{subset}/{item_id}: invalid status {status!r}")
                if isinstance(score,bool) or not isinstance(score,(int,float)) or not math.isfinite(score) or not 0<=score<=1:errors.append(f"{subset}/{item_id}: score must be finite and within [0,1]");continue
                if status!="scored" and score!=0:errors.append(f"{subset}/{item_id}: failed item must have score 0")
                if status=="scored" and subset!="evidence-gap-discovery" and score not in (0,1):errors.append(f"{subset}/{item_id}: choice score must be 0 or 1")
                if status=="scored" and row.get("metric")!=expected_metric:errors.append(f"{subset}/{item_id}: metric mismatch")
                validated_scores.append(float(score))
            if summary.get("selection_split") != "verifier": errors.append(f"{subset}: verifier summary split is not verifier")
            if summary.get("expected_total") != len(expected): errors.append(f"{subset}: expected_total mismatch")
            expected_primary="mean_recall@30" if subset=="evidence-gap-discovery" else "accuracy"
            if summary.get("grading_error") or summary.get("unscorable") or summary.get("primary_score") is None:
                errors.append(f"{subset}: incomplete grading")
            if summary.get("primary_metric")!=expected_primary:errors.append(f"{subset}: primary metric mismatch")
            counts = Counter(row.get("status", "unknown") for row in rows if row.get("item_id") != "<predictions>")
            if summary.get("attempted")!=len(expected)-counts["missing"]:errors.append(f"{subset}: summary attempted differs from per-item results")
            if summary.get("validly_evaluated")!=sum(counts[name] for name in allowed):errors.append(f"{subset}: summary validly_evaluated differs from per-item results")
            score=sum(validated_scores)
            calculated=score/len(expected) if expected else None
            if isinstance(summary.get("primary_score"),bool) or not isinstance(summary.get("primary_score"),(int,float)) or not math.isclose(float(summary["primary_score"]),calculated,rel_tol=1e-12,abs_tol=1e-12):errors.append(f"{subset}: primary_score differs from per-item results")
            for field in ("missing","agent_timeout","agent_error","unscorable","grading_error"):
                if summary.get(field)!=counts[field]:errors.append(f"{subset}: summary {field} differs from per-item results")
            if subset=="evidence-gap-discovery":retrieval_score+=score;retrieval_total+=len(expected)
            else:choice_score+=score;choice_total+=len(expected)
            correct += score; totals.update(counts)
            metric="mean_recall@30" if subset=="evidence-gap-discovery" else "accuracy"
            subset_results[subset] = {"expected_total": len(expected), "score_sum": score, "metric":metric,"score": score / len(expected) if expected else None, "statuses": dict(sorted(counts.items()))}
        valid = not problems and not errors and set(trials) == FORMAL_SUBSETS
        overall_score=correct/expected_total if valid and expected_total else None
        evaluations.append({"valid": valid, "agent": agent, "agent_config":agent_config,"agent_versions": sorted(versions), "provider": provider, "model": model, "expected_total": expected_total, "score_sum": correct, "overall_mean_item_score": overall_score, "choice_items":choice_total,"choice_micro_accuracy":choice_score/choice_total if valid and choice_total else None,"retrieval_items":retrieval_total,"evidence_gap_mean_recall_at_30":retrieval_score/retrieval_total if valid and retrieval_total else None,"statuses": dict(sorted(totals.items())), "subsets": subset_results, "errors": errors})
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
