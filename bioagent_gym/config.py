from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import HarnessError
from .io import read_yaml, validate_schema, common_schema
from .manifests import load_agent, load_benchmark


def resolve_experiment(path: Path) -> dict[str, Any]:
    config = read_yaml(path.resolve())
    base = path.resolve().parent
    required = ("protocol_version", "agent", "benchmark", "execution", "budget", "output")
    missing = [key for key in required if key not in config]
    if missing:
        raise HarnessError(f"experiment missing keys: {', '.join(missing)}")
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
    backend = config["execution"].get("backend")
    if backend not in ("local", "docker"):
        raise HarnessError("execution.backend must be local or docker")
    wall = config["budget"].get("wall_time_seconds")
    if not isinstance(wall, (int, float)) or wall <= 0:
        raise HarnessError("budget.wall_time_seconds must be positive")
    return {
        **config,
        "_config_path": str(path.resolve()),
        "_agent": agent,
        "_benchmark": benchmark,
        "_prepared": str(prepared),
        "_output": str(output),
        "_compatible_task_types": sorted(common_tasks),
    }


def validate_prepared(resolved: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    from .io import read_json, read_jsonl

    prepared = Path(resolved["_prepared"])
    manifest = read_json(prepared / "manifest.json")
    if manifest.get("benchmark_id") != resolved["_benchmark"]["benchmark_id"]:
        raise HarnessError("prepared dataset benchmark_id does not match manifest")
    if manifest.get("protocol_version") != resolved["protocol_version"]:
        raise HarnessError("prepared dataset protocol version does not match")
    tasks_path = prepared / manifest.get("tasks_file", "tasks.jsonl")
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
        validate_schema(task["input"], (benchmark_dir / schemas[task_type]["input"]).resolve(), f"{task_type} input")
    if not tasks:
        raise HarnessError("selected dataset has no tasks")
    return manifest, tasks
