from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import HarnessError
from .io import common_schema, read_json, read_jsonl, read_yaml, safe_relative_file, validate_schema
from .manifests import load_agent, load_benchmark


def resolve_experiment(path: Path) -> dict[str, Any]:
    config = read_yaml(path.resolve())
    validate_schema(config, common_schema("1.0", "experiment"), f"experiment {path.resolve()}")
    base = path.resolve().parent
    agent_path = (base / config["agent"]["manifest"]).resolve()
    benchmark_path = (base / config["benchmark"]["manifest"]).resolve()
    prepared = (base / config["benchmark"]["prepared"]).resolve()
    output = (base / config["output"]).resolve()
    agent = load_agent(agent_path)
    benchmark = load_benchmark(benchmark_path)
    version = str(config["protocol_version"])
    if version not in agent["protocol_versions"] or version not in benchmark["protocol_versions"]:
        raise HarnessError(f"protocol {version} is not supported by both manifests")
    common_tasks = set(agent["task_types"]) & set(benchmark["task_types"])
    if not common_tasks:
        raise HarnessError("agent and benchmark have no compatible task type")
    backend = config["execution"]["backend"]
    if backend == "docker" and "docker" not in agent:
        raise HarnessError(f"experiment {path.resolve()}: Docker backend requested but agent has no docker configuration")
    config_snapshot = None
    if config["agent"].get("config"):
        agent_config_path = (base / config["agent"]["config"]).resolve()
        config_snapshot = read_json(agent_config_path)
        if not isinstance(config_snapshot, dict):
            raise HarnessError(f"agent config must be a JSON object: {agent_config_path}")
    return {
        **config,
        "_config_path": str(path.resolve()),
        "_agent": agent,
        "_benchmark": benchmark,
        "_prepared": str(prepared),
        "_output": str(output),
        "_compatible_task_types": sorted(common_tasks),
        "_agent_config": config_snapshot,
    }


def validate_prepared(resolved: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    prepared = Path(resolved["_prepared"])
    manifest = read_json(prepared / "manifest.json")
    validate_schema(manifest, common_schema("1.0", "prepared-manifest"), f"prepared manifest {prepared / 'manifest.json'}")
    if manifest.get("benchmark_id") != resolved["_benchmark"]["benchmark_id"]:
        raise HarnessError("prepared dataset benchmark_id does not match manifest")
    if manifest.get("benchmark_version") != resolved["_benchmark"]["version"]:
        raise HarnessError("prepared dataset benchmark_version does not match benchmark manifest")
    if manifest.get("protocol_version") != resolved["protocol_version"]:
        raise HarnessError("prepared dataset protocol version does not match")
    requested_revision = resolved["benchmark"].get("data_revision")
    if requested_revision and requested_revision != manifest["data_revision"]:
        raise HarnessError(
            f"prepared dataset data_revision is {manifest['data_revision']!r}, requested {requested_revision!r}"
        )
    requested_split = resolved["benchmark"]["split"]
    if "splits" in manifest:
        if requested_split not in manifest["splits"]:
            raise HarnessError(
                f"prepared dataset does not contain split {requested_split!r}; available: {', '.join(sorted(manifest['splits']))}"
            )
        tasks_file = manifest["splits"][requested_split]["tasks_file"]
    else:
        if requested_split != manifest["split"]:
            raise HarnessError(
                f"prepared dataset split is {manifest['split']!r}, requested {requested_split!r}"
            )
        tasks_file = manifest["tasks_file"]
    tasks_path = safe_relative_file(prepared, tasks_file, "prepared tasks_file")
    tasks = read_jsonl(tasks_path)
    subset = resolved["benchmark"].get("tasks")
    if subset:
        wanted = set(subset)
        tasks = [task for task in tasks if task.get("task_id") in wanted]
        missing = wanted - {task.get("task_id") for task in tasks}
        if missing:
            raise HarnessError(f"unknown task IDs: {', '.join(sorted(missing))}")
    seen: set[str] = set()
    schemas = resolved["_benchmark"]["schemas"]
    benchmark_dir = Path(resolved["_benchmark"]["_path"]).parent
    for task in tasks:
        validate_schema(task, common_schema(resolved["protocol_version"], "task-spec"), "TaskSpec")
        task_id = task["task_id"]
        if task_id in seen:
            raise HarnessError(f"duplicate task_id: {task_id}")
        seen.add(task_id)
        task_type = task["task_type"]
        if task_type not in resolved["_compatible_task_types"] or task_type not in schemas:
            raise HarnessError(f"unsupported task type: {task_type}")
        input_schema = safe_relative_file(benchmark_dir, schemas[task_type]["input"], f"{task_type} input schema")
        validate_schema(task["input"], input_schema, f"{task_type} input")
    if not tasks:
        raise HarnessError("selected dataset has no tasks")
    return manifest, tasks
