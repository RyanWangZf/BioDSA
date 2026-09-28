from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import HarnessError
from .io import read_yaml


def _require(manifest: dict[str, Any], keys: tuple[str, ...], path: Path) -> None:
    missing = [key for key in keys if key not in manifest]
    if missing:
        raise HarnessError(f"{path} missing keys: {', '.join(missing)}")


def load_agent(path: Path) -> dict[str, Any]:
    value = read_yaml(path.resolve())
    _require(value, ("manifest_version", "agent_id", "protocol_versions", "task_types", "local"), path)
    if value["manifest_version"] != "1.0" or not isinstance(value["local"].get("command"), list):
        raise HarnessError(f"invalid agent manifest version or local command: {path}")
    value["_path"] = str(path.resolve())
    return value


def load_benchmark(path: Path) -> dict[str, Any]:
    value = read_yaml(path.resolve())
    _require(value, ("manifest_version", "benchmark_id", "version", "protocol_versions", "task_types", "prepare", "evaluate", "schemas"), path)
    if value["manifest_version"] != "1.0":
        raise HarnessError(f"unsupported benchmark manifest version: {path}")
    for name in ("prepare", "evaluate"):
        if not isinstance(value[name].get("command"), list):
            raise HarnessError(f"{name}.command must be an argv array: {path}")
    value["_path"] = str(path.resolve())
    return value


def discover(roots: list[Path], filename: str, loader, id_key: str) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob(filename)):
            manifest = loader(path)
            identifier = manifest[id_key]
            if identifier in found:
                raise HarnessError(f"duplicate {id_key} {identifier}: {path}")
            found[identifier] = manifest
    return found


def public_manifest(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if not key.startswith("_")}


def resolve_command(manifest: dict[str, Any], section: str) -> tuple[list[str], Path]:
    base = Path(manifest["_path"]).parent
    command = list(manifest[section]["command"])
    if not command:
        raise HarnessError(f"empty {section} command")
    executable = Path(command[0])
    if ("/" in command[0] or command[0].startswith(".")) and not executable.is_absolute():
        command[0] = str((base / executable).resolve())
    return command, base
