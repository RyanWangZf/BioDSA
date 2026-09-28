from __future__ import annotations

import hashlib
import json
import os
import tempfile
from importlib.resources import files
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator

from .errors import HarnessError


try:
    _protocol_files = files("bioagent_gym.protocol")
except ModuleNotFoundError:  # Direct source checkout before installation.
    _protocol_files = files("protocol")
SCHEMA_ROOT = Path(str(_protocol_files.joinpath("schemas")))


def read_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessError(f"cannot read JSON {path}: {exc}") from exc


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            value = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        raise HarnessError(f"cannot read YAML {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise HarnessError(f"manifest/config must be an object: {path}")
    return value


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def validate_schema(value: Any, schema_path: Path, label: str) -> None:
    schema = read_json(schema_path)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: list(e.path))
    if errors:
        rendered = "; ".join(
            f"{'.'.join(map(str, error.path)) or '<root>'}: {error.message}"
            for error in errors[:5]
        )
        raise HarnessError(f"invalid {label}: {rendered}")


def common_schema(version: str, name: str) -> Path:
    path = SCHEMA_ROOT / version / f"{name}.schema.json"
    if not path.is_file():
        raise HarnessError(f"unsupported protocol/schema: {version}/{name}")
    return path


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError("row is not an object")
                values.append(value)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise HarnessError(f"cannot read JSONL {path}: {exc}") from exc
    return values


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def safe_relative_file(root: Path, relative: str, label: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise HarnessError(f"{label} must be a contained relative path: {relative}")
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve(strict=True)
    if resolved == resolved_root or resolved_root not in resolved.parents or not resolved.is_file():
        raise HarnessError(f"{label} escapes its root or is not a file: {relative}")
    return resolved


def safe_relative_dir(root: Path, relative: str, label: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise HarnessError(f"{label} must be a contained relative path: {relative}")
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve(strict=True)
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise HarnessError(f"{label} escapes its root: {relative}")
    if not resolved.is_dir():
        raise HarnessError(f"{label} is not a directory: {relative}")
    return resolved


def clean_env_names(names: Iterable[str]) -> dict[str, str]:
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise HarnessError(f"missing required environment variables: {', '.join(missing)}")
    return {name: os.environ[name] for name in names}
