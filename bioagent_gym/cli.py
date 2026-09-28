from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .config import resolve_experiment, validate_prepared
from .errors import HarnessError
from .manifests import discover, load_agent, load_benchmark, resolve_command
from .runner import evaluate_run, run_experiment
from .settings import cache_dir


REPO_ROOT = Path(__file__).resolve().parents[1]


def _roots(values: list[str] | None, default: str) -> list[Path]:
    if values:
        return [Path(value).resolve() for value in values]
    candidates = [Path.cwd() / default, cache_dir() / default, REPO_ROOT / default]
    unique: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in unique:
            unique.append(resolved)
    return unique


def _manifest_by_id(identifier: str, roots: list[Path], kind: str):
    if kind == "agent":
        values = discover(roots, "agent.yaml", load_agent, "agent_id")
    else:
        values = discover(roots, "benchmark.yaml", load_benchmark, "benchmark_id")
    if identifier not in values:
        raise HarnessError(f"unknown {kind} ID: {identifier}")
    return values[identifier]


def cmd_list(args: argparse.Namespace) -> None:
    if args.kind == "agents":
        values = discover(_roots(args.root, "agents"), "agent.yaml", load_agent, "agent_id")
        for key, value in values.items():
            print(f"{key}\t{value.get('description', '')}\t{value['_path']}")
    else:
        values = discover(_roots(args.root, "benchmarks"), "benchmark.yaml", load_benchmark, "benchmark_id")
        for key, value in values.items():
            print(f"{key}\t{value.get('description', '')}\t{value['_path']}")


def cmd_validate(args: argparse.Namespace) -> None:
    resolved = resolve_experiment(Path(args.config))
    manifest, tasks = validate_prepared(resolved)
    # Validate presence only; validity of credentials remains an agent/provider concern.
    missing = [name for name in resolved["_agent"].get("required_env", []) if not __import__("os").environ.get(name)]
    if missing:
        raise HarnessError(f"missing required environment variables: {', '.join(missing)}")
    print(json.dumps({"valid": True, "tasks": len(tasks), "data_revision": manifest.get("data_revision")}, indent=2))


def cmd_prepare(args: argparse.Namespace) -> None:
    benchmark = _manifest_by_id(args.benchmark, _roots(args.benchmark_root, "benchmarks"), "benchmark")
    command, cwd = resolve_command(benchmark, "prepare")
    output = Path(args.output).resolve()
    if output.exists() and any(output.iterdir()):
        raise HarnessError(f"prepare output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(command + ["--config", str(Path(args.config).resolve()), "--output-dir", str(output)], cwd=cwd)
    if completed.returncode:
        raise HarnessError(f"prepare command exited with code {completed.returncode}")
    if not (output / "manifest.json").is_file() or not (output / "tasks.jsonl").is_file():
        raise HarnessError("prepare did not produce manifest.json and tasks.jsonl")
    print(output)


def cmd_run(args: argparse.Namespace) -> None:
    print(run_experiment(Path(args.config), evaluate_after=not args.no_evaluate))


def cmd_evaluate(args: argparse.Namespace) -> None:
    manifest = Path(args.benchmark_manifest) if args.benchmark_manifest else None
    print(json.dumps(evaluate_run(Path(args.run), manifest, args.allow_version_change), indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bioagent-gym",
        description="Run and evaluate biomedical AI agents in reproducible task environments.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list")
    listing.add_argument("kind", choices=("agents", "benchmarks"))
    listing.add_argument("--root", action="append")
    listing.set_defaults(func=cmd_list)
    validate = sub.add_parser("validate")
    validate.add_argument("--config", required=True)
    validate.set_defaults(func=cmd_validate)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--benchmark", required=True)
    prepare.add_argument("--config", required=True)
    prepare.add_argument("--output", required=True)
    prepare.add_argument("--benchmark-root", action="append")
    prepare.set_defaults(func=cmd_prepare)
    run = sub.add_parser("run")
    run.add_argument("--config", required=True)
    run.add_argument("--no-evaluate", action="store_true")
    run.set_defaults(func=cmd_run)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--run", required=True)
    evaluate.add_argument("--benchmark-manifest")
    evaluate.add_argument("--allow-version-change", action="store_true")
    evaluate.set_defaults(func=cmd_evaluate)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        args.func(args)
        return 0
    except HarnessError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except subprocess.TimeoutExpired as exc:
        print(f"error: process timed out: {exc.cmd}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("cancelled", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
