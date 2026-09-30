"""Fail explicitly when the inventoried, unsupported R task is invoked."""
from pathlib import Path
import json

logs = Path("/logs/verifier")
logs.mkdir(parents=True, exist_ok=True)
summary = {
    "status": "unsupported",
    "reason": "BioDSBench R has no migrated agent runtime or trusted grader",
    "reward": None,
}
(logs / "summary.json").write_text(json.dumps(summary, indent=2))
raise SystemExit(2)
