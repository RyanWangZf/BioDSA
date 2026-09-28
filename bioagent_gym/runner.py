from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

from .backends import DockerBackend, LocalBackend, utc_now
from .config import resolve_experiment, validate_prepared
from .errors import HarnessError
from .io import atomic_json, clean_env_names, common_schema, read_json, safe_relative_file, sha256, validate_schema
from .manifests import public_manifest, resolve_command


def _git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1],
            check=True, capture_output=True, text=True, timeout=3,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _safe_component(value: str) -> str:
    if not value or value in (".", "..") or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for char in value):
        raise HarnessError(f"unsafe ID for work directory: {value!r}")
    return value


def _copy_assets(task: dict[str, Any], prepared: Path, input_dir: Path) -> list[dict[str, Any]]:
    public_root = (prepared / "assets").resolve()
    copied: list[dict[str, Any]] = []
    for asset in task.get("assets", []):
        source = safe_relative_file(public_root, asset["path"], "asset path")
        destination = input_dir / "assets" / asset["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        item = {**asset, "path": str(Path("assets") / asset["path"])}
        actual = sha256(destination)
        if asset.get("checksum") and asset["checksum"] != actual:
            raise HarnessError(f"asset checksum mismatch: {asset['id']}")
        item["checksum"] = actual
        copied.append(item)
    return copied


def _validate_result(result_path: Path, request: dict[str, Any], output_dir: Path, output_schema: Path) -> dict[str, Any]:
    if not result_path.is_file():
        raise HarnessError("agent did not produce result.json")
    result = read_json(result_path)
    validate_schema(result, common_schema(request["protocol_version"], "agent-result"), "AgentResult")
    for key in ("protocol_version", "run_id", "attempt_id", "task_id"):
        if result[key] != request[key]:
            raise HarnessError(f"AgentResult {key} does not match request")
    if result["status"] == "completed":
        validate_schema(result["output"], output_schema, f"{request['task_type']} output")
    for artifact in result["artifacts"]:
        safe_relative_file(output_dir, artifact["path"], "artifact path")
    return result


def _agent_command(resolved: dict[str, Any], backend: str, input_dir: Path, output_dir: Path) -> tuple[LocalBackend, list[str], Path]:
    agent = resolved["_agent"]
    config_value = resolved["agent"].get("config")
    if backend == "local":
        command, cwd = resolve_command(agent, "local")
        args = ["--request", str(input_dir / "request.json"), "--output-dir", str(output_dir)]
        if config_value:
            args += ["--config", str((Path(resolved["_config_path"]).parent / config_value).resolve())]
        return LocalBackend(), command + args, cwd
    docker_backend = DockerBackend(agent, input_dir, output_dir)
    args = ["--request", "/input/request.json", "--output-dir", "/output"]
    if config_value:
        source = (Path(resolved["_config_path"]).parent / config_value).resolve()
        shutil.copy2(source, input_dir / "agent-config.json")
        args += ["--config", "/input/agent-config.json"]
    return docker_backend, docker_backend.agent_argv(args), Path(resolved["_agent"]["_path"]).parent


def _initial_record(resolved: dict[str, Any], run_id: str, prepared_manifest: dict[str, Any]) -> dict[str, Any]:
    docker = resolved["_agent"].get("docker", {})
    return {
        "run_id": run_id,
        "status": "running",
        "started_at": utc_now(),
        "ended_at": None,
        "protocol_version": resolved["protocol_version"],
        "git_commit": _git_commit(),
        "agent_id": resolved["_agent"]["agent_id"],
        "benchmark_id": resolved["_benchmark"]["benchmark_id"],
        "benchmark_version": resolved["_benchmark"]["version"],
        "data_revision": prepared_manifest.get("data_revision"),
        "prepared_checksum": prepared_manifest.get("checksum"),
        "backend": resolved["execution"]["backend"],
        "image": docker.get("image") if resolved["execution"]["backend"] == "docker" else None,
        "image_digest": docker.get("digest") if resolved["execution"]["backend"] == "docker" else None,
        "enforcement": {"wall_time_seconds": "harness", "model_calls": "agent", "tokens": "agent", "tool_calls": "agent"},
        "tasks": [],
    }


def _ensure_docker_image(resolved: dict[str, Any]) -> None:
    if resolved["execution"]["backend"] != "docker":
        return
    if not shutil.which("docker"):
        raise HarnessError("docker executable is unavailable")
    docker = resolved["_agent"].get("docker", {})
    image = docker.get("image")
    if not image:
        raise HarnessError("docker backend requires docker.image")
    inspect = subprocess.run(["docker", "image", "inspect", image], capture_output=True, text=True)
    if inspect.returncode != 0:
        base = Path(resolved["_agent"]["_path"]).parent
        context = (base / docker.get("build_context", ".")).resolve()
        dockerfile = (base / docker.get("dockerfile", "Dockerfile")).resolve()
        built = subprocess.run(["docker", "build", "-t", image, "-f", str(dockerfile), str(context)])
        if built.returncode != 0:
            raise HarnessError(f"docker image build failed with code {built.returncode}")
    digest = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    docker["digest"] = digest or None


def run_experiment(config_path: Path, evaluate_after: bool = True) -> Path:
    resolved = resolve_experiment(config_path)
    prepared_manifest, tasks = validate_prepared(resolved)
    required_env = resolved["_agent"].get("required_env", [])
    agent_env = clean_env_names(required_env)
    _ensure_docker_image(resolved)
    output = Path(resolved["_output"])
    if output.exists() and any(output.iterdir()):
        raise HarnessError(f"run output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    run_id = resolved.get("run_id") or f"run-{uuid.uuid4().hex[:12]}"
    persisted = {key: value for key, value in resolved.items() if not key.startswith("_")}
    persisted.update({
        "config_dir": str(Path(resolved["_config_path"]).parent),
        "prepared_path": resolved["_prepared"],
        "agent_manifest_path": resolved["_agent"]["_path"],
        "benchmark_manifest_path": resolved["_benchmark"]["_path"],
    })
    atomic_json(output / "resolved-experiment.json", persisted)
    atomic_json(output / "manifests" / "agent.json", public_manifest(resolved["_agent"]))
    atomic_json(output / "manifests" / "benchmark.json", public_manifest(resolved["_benchmark"]))
    record = _initial_record(resolved, run_id, prepared_manifest)
    atomic_json(output / "run-record.json", record)
    prepared = Path(resolved["_prepared"])
    schemas = resolved["_benchmark"]["schemas"]
    benchmark_dir = Path(resolved["_benchmark"]["_path"]).parent
    try:
        for task in tasks:
            task_id = _safe_component(task["task_id"])
            attempt_id = "attempt-0001"
            attempt = output / "tasks" / task_id / attempt_id
            input_dir, output_dir, logs_dir = attempt / "input", attempt / "output", attempt / "logs"
            for directory in (input_dir, output_dir, logs_dir):
                directory.mkdir(parents=True, exist_ok=True)
            request = {
                "protocol_version": resolved["protocol_version"], "run_id": run_id,
                "attempt_id": attempt_id, "task_id": task_id, "task_type": task["task_type"],
                "input": task["input"], "assets": _copy_assets(task, prepared, input_dir),
                "budget": resolved["budget"],
            }
            if "seed" in resolved:
                request["seed"] = resolved["seed"]
            validate_schema(request, common_schema(resolved["protocol_version"], "task-request"), "TaskRequest")
            atomic_json(input_dir / "request.json", request)
            task_record: dict[str, Any] = {"task_id": task_id, "attempt_id": attempt_id, "status": "running"}
            record["tasks"].append(task_record)
            atomic_json(output / "run-record.json", record)
            try:
                backend, argv, cwd = _agent_command(resolved, resolved["execution"]["backend"], input_dir, output_dir)
                backend.start(argv, cwd, agent_env, logs_dir / "stdout.log", logs_dir / "stderr.log")
                outcome = backend.wait(float(resolved["budget"]["wall_time_seconds"]))
                task_record.update(vars(outcome))
                if outcome.timed_out:
                    raise HarnessError("wall-time budget exceeded; process was terminated")
                if outcome.cancelled:
                    raise HarnessError("agent process was cancelled")
                if outcome.exit_code != 0:
                    raise HarnessError(f"agent exited with code {outcome.exit_code}")
                output_schema = (benchmark_dir / schemas[task["task_type"]]["output"]).resolve()
                result = _validate_result(output_dir / "result.json", request, output_dir, output_schema)
                atomic_json(attempt / "validated-result.json", result)
                task_record["status"] = result["status"]
                if result["status"] != "completed":
                    task_record["failure_reason"] = result["error"]
            except (HarnessError, OSError, subprocess.SubprocessError) as exc:
                task_record["status"] = "timed_out" if task_record.get("timed_out") else "failed"
                task_record["failure_reason"] = str(exc)
            atomic_json(output / "run-record.json", record)
        record["status"] = "completed" if all(t["status"] == "completed" for t in record["tasks"]) else "completed_with_failures"
    finally:
        record["ended_at"] = utc_now()
        if record["status"] == "running":
            record["status"] = "failed"
        atomic_json(output / "run-record.json", record)
    if evaluate_after:
        evaluate_run(output)
    return output


def _reference_for(task_id: str, prepared: Path, prepared_manifest: dict[str, Any]) -> dict[str, Any]:
    private = prepared_manifest.get("private", {})
    reference_file = private.get("references")
    if not reference_file:
        return {}
    path = safe_relative_file(prepared, reference_file, "private reference path")
    return {"path": str(path), "task_id": task_id}


def evaluate_run(run_dir: Path) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    experiment = read_json(run_dir / "resolved-experiment.json")
    # Stored manifests and explicit prepared path make rescoring independent of the source config.
    benchmark = read_json(run_dir / "manifests" / "benchmark.json")
    prepared = Path(experiment["prepared_path"])
    prepared_manifest = read_json(prepared / "manifest.json")
    from .io import read_jsonl

    tasks = {task["task_id"]: task for task in read_jsonl(prepared / prepared_manifest.get("tasks_file", "tasks.jsonl"))}
    benchmark_path = Path(experiment["benchmark_manifest_path"])
    benchmark["_path"] = str(benchmark_path)
    command, cwd = resolve_command(benchmark, "evaluate")
    run_record = read_json(run_dir / "run-record.json")
    evaluations: list[dict[str, Any]] = []
    for task_record in run_record["tasks"]:
        if task_record["status"] != "completed":
            continue
        task_id, attempt_id = task_record["task_id"], task_record["attempt_id"]
        attempt = run_dir / "tasks" / task_id / attempt_id
        request = {
            "protocol_version": experiment["protocol_version"], "run_id": run_record["run_id"],
            "attempt_id": attempt_id, "task_id": task_id, "task_type": tasks[task_id]["task_type"],
            "task": tasks[task_id], "agent_result_path": str(attempt / "validated-result.json"),
            "artifacts_dir": str(attempt / "output"),
            "reference": _reference_for(task_id, prepared, prepared_manifest),
            "scoring": experiment["benchmark"].get("scoring", {}),
        }
        validate_schema(request, common_schema(experiment["protocol_version"], "evaluation-request"), "EvaluationRequest")
        evaluation_dir = attempt / "evaluation"
        if evaluation_dir.exists():
            shutil.rmtree(evaluation_dir)
        evaluation_dir.mkdir(parents=True)
        atomic_json(evaluation_dir / "request.json", request)
        evaluator = LocalBackend()
        evaluator.start(
            command + ["--request", str(evaluation_dir / "request.json"), "--output-dir", str(evaluation_dir)],
            cwd, clean_env_names(benchmark.get("evaluate", {}).get("required_env", [])),
            evaluation_dir / "stdout.log", evaluation_dir / "stderr.log",
        )
        outcome = evaluator.wait(float(experiment["budget"]["wall_time_seconds"]))
        if outcome.timed_out:
            raise HarnessError(f"evaluator timed out for {task_id}")
        if outcome.exit_code != 0:
            raise HarnessError(f"evaluator failed for {task_id} with code {outcome.exit_code}")
        result = read_json(evaluation_dir / "result.json")
        validate_schema(result, common_schema(experiment["protocol_version"], "evaluation-result"), "EvaluationResult")
        if result["task_id"] != task_id or result["run_id"] != run_record["run_id"]:
            raise HarnessError(f"evaluator result identity mismatch for {task_id}")
        evaluations.append(result)
    summary = aggregate(evaluations, benchmark.get("aggregation", {}), run_record)
    atomic_json(run_dir / "summary.json", summary)
    return summary


def aggregate(results: list[dict[str, Any]], rules: dict[str, str], record: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, list[float]] = defaultdict(list)
    for result in results:
        if result["status"] == "scored":
            for name, value in result["metrics"].items():
                values[name].append(value)
    metrics: dict[str, float | int | None] = {}
    for name, operation in rules.items():
        items = values.get(name, [])
        if operation == "count": metrics[name] = len(items)
        elif not items: metrics[name] = None
        elif operation == "mean": metrics[name] = sum(items) / len(items)
        elif operation == "sum": metrics[name] = sum(items)
        elif operation == "min": metrics[name] = min(items)
        elif operation == "max": metrics[name] = max(items)
        else: raise HarnessError(f"unsupported aggregation operation: {operation}")
    statuses: dict[str, int] = defaultdict(int)
    for task in record["tasks"]: statuses[task["status"]] += 1
    return {"run_id": record["run_id"], "task_status_counts": dict(statuses), "evaluated_tasks": len(results), "metrics": metrics}
