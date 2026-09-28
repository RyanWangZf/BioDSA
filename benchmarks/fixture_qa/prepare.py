#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path


def atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True); handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--config", required=True); parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(); config = json.loads(Path(args.config).read_text(encoding="utf-8")); output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True); (output / "assets").mkdir(); (output / "private").mkdir()
    tasks = [
        {"task_id":"arithmetic","task_type":"qa.multiple_choice.v1","input":{"question":"What is 2 + 2?","choices":[{"id":"A","text":"3"},{"id":"B","text":"4"}]},"assets":[]},
        {"task_id":"biology","task_type":"qa.multiple_choice.v1","input":{"question":"Which organ is central to detoxification?","choices":[{"id":"A","text":"Liver"},{"id":"B","text":"Patella"}]},"assets":[]},
    ]
    tasks = tasks[:int(config.get("limit", len(tasks)))]
    lines = "".join(json.dumps(task, sort_keys=True) + "\n" for task in tasks); (output / "tasks.jsonl").write_text(lines, encoding="utf-8")
    references = {"arithmetic":"B", "biology":"A"}; atomic(output / "private" / "references.json", references)
    digest = hashlib.sha256(lines.encode()).hexdigest()
    revision = config.get("data_revision", "fixture-r1")
    atomic(output / "manifest.json", {"protocol_version":"1.0","benchmark_id":"fixture_qa","benchmark_version":"0.1.0","data_revision":revision,"split":config.get("split","test"),"checksum":f"sha256:{digest}","task_types":["qa.multiple_choice.v1"],"tasks_file":"tasks.jsonl","assets_dir":"assets","private":{"references":"private/references.json","reference_version":revision}})


if __name__ == "__main__": main()
