#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--request", required=True); parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(); request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    if request["scoring"].get("fail_task_id") == request["task_id"]:
        raise SystemExit(23)
    result = json.loads(Path(request["agent_result_path"]).read_text(encoding="utf-8")); references = json.loads(Path(request["reference"]["path"]).read_text(encoding="utf-8"))
    expected = references[request["task_id"]]; actual = result["output"]["selected_choice"]
    value = {"protocol_version":request["protocol_version"],"run_id":request["run_id"],"attempt_id":request["attempt_id"],"task_id":request["task_id"],"status":"scored","metrics":{"accuracy":1.0 if actual == expected else 0.0},"details":{"selected_choice":actual},"evaluator":{"id":"fixture_qa.exact_match","version":"0.1.0"}}
    output = Path(args.output_dir) / "result.json"; fd, temporary = tempfile.mkstemp(prefix=".result.", dir=output.parent)
    with os.fdopen(fd, "w", encoding="utf-8") as handle: json.dump(value, handle, indent=2); handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, output)


if __name__ == "__main__": main()
