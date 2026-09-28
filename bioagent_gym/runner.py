from __future__ import annotations

import shutil
import subprocess
import warnings
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

from .backends import DockerBackend, LocalBackend, SandboxContainer, utc_now
from .config import resolve_experiment, validate_prepared
from .errors import HarnessError
from .io import atomic_json, clean_env_names, common_schema, read_json, read_jsonl, safe_relative_dir, safe_relative_file, sha256, validate_schema
from .manifests import load_benchmark, public_manifest, resolve_command

SMALL_REFERENCE_LIMIT = 1024 * 1024
BUDGET_KEYS = ("model_calls", "tokens", "tool_calls")


def _git_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1], check=True, capture_output=True, text=True, timeout=3).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _safe_component(value: str) -> str:
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    if not value or value in (".", "..") or any(char not in allowed for char in value):
        raise HarnessError(f"unsafe ID for work directory: {value!r}")
    return value


def _copy_assets(task: dict[str, Any], assets_root: Path, input_dir: Path) -> list[dict[str, Any]]:
    copied = []
    for asset in task.get("assets", []):
        source = safe_relative_file(assets_root, asset["path"], "asset path")
        destination = input_dir / "assets" / asset["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        item = {**asset, "path": str(Path("assets") / asset["path"])}
        if asset.get("checksum"):
            actual = sha256(destination)
            if asset["checksum"] != actual:
                raise HarnessError(f"asset checksum mismatch: {asset['id']}")
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


def _budget_record(resolved: dict[str, Any]) -> dict[str, str]:
    raw = resolved["_agent"].get("budget_capabilities", {})
    capabilities = {name: "reported_only" for name in raw} if isinstance(raw, list) else raw
    record = {"wall_time_seconds": "harness_enforced"}
    unsupported = []
    for name in BUDGET_KEYS:
        if name not in resolved["budget"]: record[name] = "not_requested"
        elif name not in capabilities: record[name], unsupported = "unsupported", [*unsupported, name]
        else: record[name] = capabilities[name]
    if unsupported and resolved.get("budget_policy", "strict") != "best_effort":
        raise HarnessError(f"requested budgets are unsupported by agent {resolved['_agent']['agent_id']}: {', '.join(unsupported)}; set budget_policy: best_effort to pass them without enforcement")
    return record


def _agent_command(resolved: dict[str, Any], input_dir: Path, workspace: Path, output_dir: Path, config_snapshot: Path | None, channel: Path | None = None) -> tuple[LocalBackend, list[str]]:
    agent = resolved["_agent"]
    runtime_config = None
    if config_snapshot:
        runtime_config = read_json(config_snapshot)
        runtime_config["execution_environment"] = {**runtime_config.get("execution_environment", {}), "sandbox_env_names": agent.get("sandbox", {}).get("required_env", [])}
        if channel:
            runtime_config["execution_environment"].update({"backend": "file_channel", "channel_dir": "/sandbox-channel"})
        atomic_json(input_dir / "agent-config.json", runtime_config)
    if resolved["execution"]["backend"] == "local":
        command, _ = resolve_command(agent, "local")
        args = ["--request", str(input_dir / "request.json"), "--output-dir", str(output_dir)]
        if runtime_config is not None: args += ["--config", str(input_dir / "agent-config.json")]
        return LocalBackend(), command + args
    env_names = list(resolved["_agent_env_names"])
    if resolved["_network"]["boundary"] == "shared": env_names += list(agent.get("sandbox", {}).get("required_env", []))
    backend = DockerBackend(agent, input_dir, workspace, output_dir, resolved["_network"]["agent"]["mode"], channel, env_names)
    args = ["--request", "/input/request.json", "--output-dir", "/output"]
    if runtime_config is not None:
        args += ["--config", "/input/agent-config.json"]
    return backend, backend.agent_argv(args)


def _ensure_docker_image(resolved: dict[str, Any]) -> None:
    if resolved["execution"]["backend"] != "docker": return
    if not shutil.which("docker"): raise HarnessError("docker executable is unavailable")
    base = Path(resolved["_agent"]["_path"]).parent
    images = [(resolved["_agent"]["docker"], "agent")]
    if resolved["_network"]["boundary"] == "separate": images.append((resolved["_agent"]["sandbox"]["docker"], "sandbox"))
    seen = set()
    for docker, label in images:
        if docker["image"] in seen: continue
        seen.add(docker["image"])
        _ensure_image(docker, base, label)


def _ensure_image(docker: dict[str, Any], base: Path, label: str) -> None:
    if subprocess.run(["docker", "image", "inspect", docker["image"]], capture_output=True).returncode:
        context = safe_relative_dir(base, docker.get("build_context", "."), "docker build_context")
        dockerfile = safe_relative_file(base, docker.get("dockerfile", "Dockerfile"), "dockerfile")
        built = subprocess.run(["docker", "build", "-t", docker["image"], "-f", str(dockerfile), str(context)])
        if built.returncode: raise HarnessError(f"{label} Docker image build failed with code {built.returncode}")
    try:
        docker["digest"] = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", docker["image"]], capture_output=True, text=True, check=True).stdout.strip() or None
    except subprocess.SubprocessError as exc:
        raise HarnessError(f"cannot inspect Docker image {docker['image']}: {exc}") from exc


def _snapshot_context(output: Path, resolved: dict[str, Any], prepared: dict[str, Any], tasks: list[dict[str, Any]], budget_record: dict[str, str]) -> tuple[dict[str, Any], Path | None]:
    context = output / "context"
    experiment = {key: value for key, value in resolved.items() if not key.startswith("_")}
    experiment["network_resolution"] = resolved["_network"]
    experiment.update({"config_dir": str(Path(resolved["_config_path"]).parent), "prepared_path": resolved["_prepared"], "agent_manifest_path": resolved["_agent"]["_path"], "benchmark_manifest_path": resolved["_benchmark"]["_path"]})
    atomic_json(output / "resolved-experiment.json", experiment)
    atomic_json(context / "experiment.json", experiment)
    atomic_json(context / "agent-manifest.json", public_manifest(resolved["_agent"]))
    atomic_json(context / "benchmark-manifest.json", public_manifest(resolved["_benchmark"]))
    atomic_json(context / "prepared-manifest.json", prepared)
    atomic_json(context / "tasks.json", tasks)
    config_path = None
    if resolved["_agent_config"] is not None:
        config_path = context / "agent-config.json"
        atomic_json(config_path, resolved["_agent_config"])
    reference = {"kind": "none", "version": prepared.get("private", {}).get("reference_version", prepared["data_revision"]), "data_revision": prepared["data_revision"]}
    reference_file = prepared.get("private", {}).get("references")
    if reference_file:
        source = safe_relative_file(Path(resolved["_prepared"]), reference_file, "private reference path")
        if source.stat().st_size <= SMALL_REFERENCE_LIMIT:
            destination = context / "evaluator" / f"reference{source.suffix}"
            destination.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, destination)
            reference.update({"kind": "snapshot", "path": str(destination)})
        else: reference.update({"kind": "external", "path": str(source)})
    metadata = {"context_version": "1", "legacy": False, "protocol_version": resolved["protocol_version"], "benchmark_id": resolved["_benchmark"]["benchmark_id"], "benchmark_version": resolved["_benchmark"]["version"], "data_revision": prepared["data_revision"], "split": resolved["benchmark"]["split"], "evaluator": resolved["_benchmark"].get("evaluator"), "scoring": resolved["benchmark"].get("scoring", {}), "agent_config": str(config_path) if config_path else None, "budget_enforcement": budget_record, "network": resolved["_network"], "reference": reference, "immutability": "version-and-snapshot; external content modified in place under the same version is not detectable"}
    atomic_json(context / "metadata.json", metadata)
    atomic_json(output / "manifests" / "agent.json", public_manifest(resolved["_agent"]))
    atomic_json(output / "manifests" / "benchmark.json", public_manifest(resolved["_benchmark"]))
    return metadata, config_path


def _initial_record(resolved: dict[str, Any], run_id: str, prepared: dict[str, Any], budget: dict[str, str]) -> dict[str, Any]:
    docker = resolved["_agent"].get("docker", {})
    sandbox_docker = resolved["_agent"].get("sandbox", {}).get("docker", {})
    return {"run_id": run_id, "status": "running", "started_at": utc_now(), "ended_at": None, "protocol_version": resolved["protocol_version"], "git_commit": _git_commit(), "agent_id": resolved["_agent"]["agent_id"], "benchmark_id": resolved["_benchmark"]["benchmark_id"], "benchmark_version": resolved["_benchmark"]["version"], "data_revision": prepared["data_revision"], "split": resolved["benchmark"]["split"], "prepared_checksum": prepared.get("checksum"), "backend": resolved["execution"]["backend"], "network": resolved["_network"], "image": docker.get("image") if resolved["execution"]["backend"] == "docker" else None, "image_digest": docker.get("digest") if resolved["execution"]["backend"] == "docker" else None, "sandbox_image": sandbox_docker.get("image") if resolved["_network"]["boundary"] == "separate" else None, "sandbox_image_digest": sandbox_docker.get("digest") if resolved["_network"]["boundary"] == "separate" else None, "budget_enforcement": budget, "tasks": []}


def run_experiment(config_path: Path, evaluate_after: bool = True) -> Path:
    resolved = resolve_experiment(config_path); prepared, tasks = validate_prepared(resolved)
    budget = _budget_record(resolved); env = clean_env_names(resolved["_agent_env_names"])
    sandbox_env = clean_env_names(resolved["_agent"].get("sandbox", {}).get("required_env", [])) if resolved["_network"]["sandbox"]["applicable"] else {}
    if resolved["_network"]["boundary"] == "shared": env.update(sandbox_env)
    _ensure_docker_image(resolved)
    output = Path(resolved["_output"])
    if output.exists() and any(output.iterdir()): raise HarnessError(f"run output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True); run_id = resolved.get("run_id") or f"run-{uuid.uuid4().hex[:12]}"
    _, config_snapshot = _snapshot_context(output, resolved, prepared, tasks, budget)
    record = _initial_record(resolved, run_id, prepared, budget); atomic_json(output / "run-record.json", record)
    assets_root = safe_relative_dir(Path(resolved["_prepared"]), prepared.get("assets_dir", "assets"), "assets_dir")
    schemas, benchmark_dir = resolved["_benchmark"]["schemas"], Path(resolved["_benchmark"]["_path"]).parent
    cancelled = False; pending: BaseException | None = None
    try:
        for task in tasks:
            task_id, attempt_id = _safe_component(task["task_id"]), "attempt-0001"
            attempt = output / "tasks" / task_id / attempt_id
            input_dir, workspace, output_dir, logs = attempt / "input", attempt / "workspace", attempt / "output", attempt / "logs"
            for directory in (input_dir, workspace, output_dir, logs): directory.mkdir(parents=True, exist_ok=True)
            request = {"protocol_version": resolved["protocol_version"], "run_id": run_id, "attempt_id": attempt_id, "task_id": task_id, "task_type": task["task_type"], "input": task["input"], "assets": _copy_assets(task, assets_root, input_dir), "budget": resolved["budget"]}
            if "seed" in resolved: request["seed"] = resolved["seed"]
            validate_schema(request, common_schema(resolved["protocol_version"], "task-request"), "TaskRequest"); atomic_json(input_dir / "request.json", request)
            task_record = {"task_id": task_id, "attempt_id": attempt_id, "status": "running", "workspace": str(workspace.relative_to(output))}; record["tasks"].append(task_record); atomic_json(output / "run-record.json", record)
            backend: LocalBackend | None = None
            sandbox: SandboxContainer | None = None
            try:
                channel = None
                if resolved["_network"]["boundary"] == "separate":
                    channel = attempt / "sandbox-channel"; channel.mkdir()
                    sandbox_names = resolved["_agent"]["sandbox"].get("required_env", [])
                    sandbox = SandboxContainer(resolved["_agent"], workspace, channel, resolved["_network"]["sandbox"]["mode"], sandbox_names)
                    sandbox.start()
                backend, argv = _agent_command(resolved, input_dir, workspace, output_dir, config_snapshot, channel)
                backend.start(argv, workspace, env, logs / "stdout.log", logs / "stderr.log"); outcome = backend.wait(float(resolved["budget"]["wall_time_seconds"])); task_record.update(vars(outcome))
                if outcome.timed_out: raise HarnessError("wall-time budget exceeded; process was terminated")
                if outcome.cancelled: raise HarnessError("agent process was cancelled")
                if outcome.exit_code != 0: raise HarnessError(f"agent exited with code {outcome.exit_code}")
                schema = safe_relative_file(benchmark_dir, schemas[task["task_type"]]["output"], f"{task['task_type']} output schema")
                result = _validate_result(output_dir / "result.json", request, output_dir, schema); atomic_json(attempt / "validated-result.json", result); task_record["status"] = result["status"]
                if result["status"] != "completed": task_record["failure_reason"] = result["error"]
            except KeyboardInterrupt as exc:
                if backend: backend.cancel(); backend.cleanup()
                if sandbox: sandbox.cleanup()
                task_record.update({"status": "cancelled", "cancelled": True, "failure_reason": "user cancelled"}); cancelled, pending = True, exc
            except (HarnessError, OSError, subprocess.SubprocessError) as exc:
                if backend: backend.cleanup()
                task_record["status"] = "timed_out" if task_record.get("timed_out") else "failed"; task_record["failure_reason"] = str(exc)
            finally:
                if sandbox: sandbox.cleanup()
                atomic_json(output / "run-record.json", record)
            if cancelled: break
        record["status"] = "cancelled" if cancelled else ("completed" if all(item["status"] == "completed" for item in record["tasks"]) else "completed_with_failures")
    except BaseException as exc:
        pending = pending or exc; record["status"] = "cancelled" if isinstance(exc, KeyboardInterrupt) else "failed"
    finally:
        record["ended_at"] = utc_now()
        if record["status"] == "running": record["status"] = "failed"
        atomic_json(output / "run-record.json", record)
    if pending: raise pending
    if evaluate_after: evaluate_run(output)
    return output


def _load_run_context(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], bool]:
    context = run_dir / "context"
    if (context / "metadata.json").is_file(): return read_json(context / "metadata.json"), read_json(context / "experiment.json"), read_json(context / "tasks.json"), False
    warnings.warn("legacy run has no task/context snapshot; rescoring reads external prepared data and cannot verify snapshot provenance", RuntimeWarning, stacklevel=2)
    experiment = read_json(run_dir / "resolved-experiment.json"); prepared = Path(experiment["prepared_path"]); manifest = read_json(prepared / "manifest.json"); benchmark = read_json(run_dir / "manifests" / "benchmark.json")
    tasks = read_jsonl(safe_relative_file(prepared, manifest.get("tasks_file", "tasks.jsonl"), "legacy tasks_file"))
    reference = safe_relative_file(prepared, manifest["private"]["references"], "legacy reference")
    metadata = {"context_version": "legacy", "legacy": True, "protocol_version": experiment["protocol_version"], "benchmark_id": benchmark["benchmark_id"], "benchmark_version": benchmark["version"], "data_revision": manifest.get("data_revision"), "split": manifest.get("split"), "evaluator": None, "scoring": experiment.get("benchmark", {}).get("scoring", {}), "reference": {"kind": "external", "path": str(reference), "version": manifest.get("data_revision")}}
    return metadata, experiment, tasks, True


def _version_differences(metadata: dict[str, Any], benchmark: dict[str, Any], experiment: dict[str, Any], legacy: bool) -> list[str]:
    differences = []
    if benchmark["benchmark_id"] != metadata["benchmark_id"]: differences.append(f"benchmark_id {metadata['benchmark_id']} -> {benchmark['benchmark_id']}")
    if benchmark["version"] != metadata["benchmark_version"]: differences.append(f"benchmark_version {metadata['benchmark_version']} -> {benchmark['version']}")
    if metadata.get("evaluator") and benchmark.get("evaluator") != metadata["evaluator"]: differences.append(f"evaluator {metadata['evaluator']} -> {benchmark.get('evaluator')}")
    prepared = Path(experiment.get("prepared_path", ""))
    if (prepared / "manifest.json").is_file():
        current = read_json(prepared / "manifest.json")
        if current.get("data_revision") != metadata.get("data_revision"): differences.append(f"data_revision {metadata.get('data_revision')} -> {current.get('data_revision')}")
    if legacy: differences.append("legacy run has no immutable context snapshot")
    return differences


def _failure(path: Path, code: str, message: str) -> dict[str, Any]:
    result = {"evaluation_status": "failed", "error": {"code": code, "message": message}}; atomic_json(path / "status.json", result); return result


def evaluate_run(run_dir: Path, benchmark_manifest: Path | None = None, allow_version_change: bool = False) -> dict[str, Any]:
    run_dir = run_dir.resolve(); metadata, experiment, task_list, legacy = _load_run_context(run_dir)
    benchmark_path = benchmark_manifest.resolve() if benchmark_manifest else Path(experiment["benchmark_manifest_path"]); benchmark = load_benchmark(benchmark_path)
    differences = _version_differences(metadata, benchmark, experiment, legacy)
    if differences and not allow_version_change and not legacy: raise HarnessError("rescoring version mismatch; pass --allow-version-change: " + "; ".join(differences))
    if legacy: warnings.warn("legacy rescore version verification is incomplete", RuntimeWarning, stacklevel=2)
    command, _ = resolve_command(benchmark, "evaluate"); run_record = read_json(run_dir / "run-record.json"); tasks = {task["task_id"]: task for task in task_list}
    timestamp = utc_now().replace(":", "").replace("+0000", "Z")
    evaluation_id = f"eval-{timestamp}-{uuid.uuid4().hex[:8]}"; root = run_dir / "evaluations" / evaluation_id; root.mkdir(parents=True)
    record = {"evaluation_id": evaluation_id, "run_id": run_record["run_id"], "status": "running", "started_at": utc_now(), "ended_at": None, "legacy_context": legacy, "benchmark_id": benchmark["benchmark_id"], "benchmark_version": benchmark["version"], "data_revision": metadata.get("data_revision"), "evaluator": benchmark.get("evaluator"), "scoring": metadata.get("scoring", {}), "version_differences": differences, "version_override": bool(differences and allow_version_change), "tasks": []}; atomic_json(root / "evaluation-record.json", record)
    results = {}; cancelled = False
    for execution in run_record["tasks"]:
        task_id, attempt_id = execution["task_id"], execution["attempt_id"]; directory = root / "tasks" / task_id / attempt_id; directory.mkdir(parents=True); item = {"task_id": task_id, "attempt_id": attempt_id}; record["tasks"].append(item)
        if execution["status"] != "completed": item.update({"evaluation_status": "not_run_agent_failed", "agent_status": execution["status"]}); atomic_json(directory / "status.json", item); continue
        try:
            task, attempt = tasks[task_id], run_dir / "tasks" / task_id / attempt_id; reference = {**metadata.get("reference", {}), "task_id": task_id}
            request = {"protocol_version": metadata["protocol_version"], "run_id": run_record["run_id"], "attempt_id": attempt_id, "task_id": task_id, "task_type": task["task_type"], "task": task, "agent_result_path": str(attempt / "validated-result.json"), "artifacts_dir": str(attempt / "output"), "reference": reference, "scoring": metadata.get("scoring", {})}
            validate_schema(request, common_schema(metadata["protocol_version"], "evaluation-request"), "EvaluationRequest"); atomic_json(directory / "request.json", request); evaluator = LocalBackend()
            try:
                evaluator.start(command + ["--request", str(directory / "request.json"), "--output-dir", str(directory)], directory, clean_env_names(benchmark["evaluate"].get("required_env", [])), directory / "stdout.log", directory / "stderr.log"); outcome = evaluator.wait(float(experiment["budget"]["wall_time_seconds"]))
            except KeyboardInterrupt:
                evaluator.cancel(); evaluator.cleanup(); item.update({"evaluation_status": "cancelled"}); atomic_json(directory / "status.json", item); cancelled = True; break
            if outcome.timed_out: item.update(_failure(directory, "timeout", "evaluator wall-time budget exceeded")); continue
            if outcome.exit_code != 0: item.update(_failure(directory, "nonzero_exit", f"evaluator exited with code {outcome.exit_code}")); continue
            result = read_json(directory / "result.json"); validate_schema(result, common_schema(metadata["protocol_version"], "evaluation-result"), "EvaluationResult")
            for key, expected in (("protocol_version", metadata["protocol_version"]), ("run_id", run_record["run_id"]), ("task_id", task_id), ("attempt_id", attempt_id)):
                if result[key] != expected: raise HarnessError(f"EvaluationResult {key} does not match request")
            if benchmark.get("evaluator") and result["evaluator"] != benchmark["evaluator"]: raise HarnessError("EvaluationResult evaluator does not match benchmark manifest")
            results[task_id] = result; item["evaluation_status"] = result["status"]
            if result["status"] == "failed": item["error"] = result.get("error")
            atomic_json(directory / "status.json", item)
        except KeyboardInterrupt:
            item["evaluation_status"] = "cancelled"; atomic_json(directory / "status.json", item); cancelled = True; break
        except (HarnessError, OSError, subprocess.SubprocessError, KeyError, ValueError) as exc: item.update(_failure(directory, "invalid_evaluation", str(exc)))
        finally: atomic_json(root / "evaluation-record.json", record)
    record["status"] = "cancelled" if cancelled else ("completed_with_failures" if any(item["evaluation_status"] == "failed" for item in record["tasks"]) else "completed"); record["ended_at"] = utc_now()
    summary = aggregate(results, benchmark["aggregation"], run_record, record); atomic_json(root / "summary.json", summary); atomic_json(root / "evaluation-record.json", record); atomic_json(run_dir / "latest-evaluation.json", {"evaluation_id": evaluation_id, "summary": str(Path("evaluations") / evaluation_id / "summary.json")})
    if cancelled: raise KeyboardInterrupt
    return summary


def aggregate(results: dict[str, dict[str, Any]], rules: dict[str, Any], run_record: dict[str, Any], evaluation_record: dict[str, Any]) -> dict[str, Any]:
    execution_counts: dict[str, int] = defaultdict(int); evaluation_counts: dict[str, int] = defaultdict(int)
    for task in run_record["tasks"]: execution_counts[task["status"]] += 1
    for task in evaluation_record["tasks"]: evaluation_counts[task["evaluation_status"]] += 1
    total = len(run_record["tasks"]); agent_failures = sum(value for key, value in execution_counts.items() if key != "completed"); metrics = {}
    for name, raw in rules.items():
        rule = {"operation": raw, "agent_failure": "exclude"} if isinstance(raw, str) else raw; values = [result["metrics"][name] for result in results.values() if result["status"] == "scored" and name in result["metrics"]]; valid = len(values)
        if rule["agent_failure"] == "zero": values += [0.0] * agent_failures; denominator = "scored_and_agent_failures"
        else: denominator = "scored_only"
        operation = rule["operation"]
        if not values: value = None
        elif operation == "mean": value = sum(values) / len(values)
        elif operation == "sum": value = sum(values)
        elif operation == "min": value = min(values)
        elif operation == "max": value = max(values)
        elif operation == "count": value = len(values)
        else: raise HarnessError(f"unsupported aggregation operation: {operation}")
        metrics[name] = {"value": value, "operation": operation, "denominator": denominator, "denominator_count": len(values), "valid_scores": valid, "coverage": valid / total if total else None}
    return {"run_id": run_record["run_id"], "evaluation_id": evaluation_record["evaluation_id"], "total_tasks": total, "execution_status_counts": dict(execution_counts), "evaluation_status_counts": dict(evaluation_counts), "metrics": metrics, "legacy_context": evaluation_record["legacy_context"]}
