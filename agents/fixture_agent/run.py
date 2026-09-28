#!/usr/bin/env python3
"""Standalone deterministic fixture. It imports no BioAgent Gym code."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".result.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try: os.unlink(temporary)
        except FileNotFoundError: pass
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--config")
    args = parser.parse_args()
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    question = request["input"]["question"].lower()
    choices = request["input"]["choices"]
    preferred = "4" if "2 + 2" in question else "liver" if "detox" in question else choices[0]["text"]
    selected = next((item["id"] for item in choices if item["text"].lower() == preferred), choices[0]["id"])
    (output / "decision.txt").write_text(f"selected={selected}\n", encoding="utf-8")
    result = {
        "protocol_version": request["protocol_version"], "run_id": request["run_id"],
        "attempt_id": request["attempt_id"], "task_id": request["task_id"],
        "status": "completed", "output": {"selected_choice": selected},
        "artifacts": [{"path": "decision.txt", "type": "text/plain", "description": "Deterministic decision trace"}],
        "extensions": {"fixture": True},
    }
    atomic_json(output / "result.json", result)


if __name__ == "__main__": main()
