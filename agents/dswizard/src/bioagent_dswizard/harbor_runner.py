from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from .agent import DSWizardAgent


def main() -> int:
    payload = json.loads(Path(sys.argv[1]).read_text())
    workspace = Path("/app")
    submission = workspace / "submission"
    submission.mkdir(exist_ok=True)
    inputs = sorted(str(path.relative_to(workspace)) for path in (workspace / "inputs").rglob("*") if path.is_file()) if (workspace / "inputs").is_dir() else []
    result = DSWizardAgent(payload["config"], workspace).run(payload["instruction"], inputs)
    (submission / "final_answer.md").write_text(result["final_answer"])
    (submission / "analysis_plan.md").write_text(result["analysis_plan"])
    (submission / "analysis.py").write_text("\n\n".join(result["generated_code"]))
    (submission / "execution.json").write_text(json.dumps(result["execution_logs"], indent=2))
    for path in workspace.iterdir():
        if path.is_file():
            shutil.copy2(path, submission / path.name)
    print(result["final_answer"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
