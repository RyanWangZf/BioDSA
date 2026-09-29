import json, runpy, sys
from pathlib import Path
try:
    state=runpy.run_path(sys.argv[1])
    public={k:type(v).__name__ for k,v in state.items() if not k.startswith("_")}
    Path("/tmp/submission-result.json").write_text(json.dumps({"status":"completed","variables":public}))
except Exception as exc:
    Path("/tmp/submission-result.json").write_text(json.dumps({"status":"failed","error":type(exc).__name__}))
    raise
