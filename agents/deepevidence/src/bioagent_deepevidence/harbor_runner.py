from __future__ import annotations

import json
import sys
from pathlib import Path

from .workflow import DeepEvidenceAgent


def main() -> int:
    payload = json.loads(Path(sys.argv[1]).read_text())
    workspace = Path("/app")
    submission = workspace / "submission"
    submission.mkdir(exist_ok=True)
    result = DeepEvidenceAgent(payload["config"], workspace).run(payload["instruction"])
    usage = result.pop("usage")
    (submission / "final_answer.md").write_text(result["final_answer"])
    for name, key in (("citations.json", "citations"), ("evidence.json", "evidence"), ("trace.json", "trace"), ("memory_graph.json", "memory_graph"), ("execution.json", "execution_logs")):
        (submission / name).write_text(json.dumps(result[key], indent=2))
    (submission / "generated_code.py").write_text("\n\n".join(result["generated_code"]))
    (submission / "usage.json").write_text(json.dumps(usage, indent=2))
    print(result["final_answer"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
