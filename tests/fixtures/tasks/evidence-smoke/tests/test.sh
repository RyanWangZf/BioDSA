#!/bin/sh
set -eu
python3 - <<'PY'
import json
from pathlib import Path
s=Path('/app/submission'); required=['final_answer.md','citations.json','trace.json','memory_graph.json','usage.json','execution.json']
ok=all((s/x).is_file() for x in required)
if ok:
 try:
  trace=json.loads((s/'trace.json').read_text()); events=[x['event'] for x in trace]
  ok={'orchestrator_start','subagent_dispatched','tool_result','memory_retrieved','code_execution','orchestrator_complete'} <= set(events)
  ok=ok and len(json.loads((s/'citations.json').read_text()))>0 and len(json.loads((s/'memory_graph.json').read_text())['entities'])>0
 except Exception: ok=False
Path('/logs/verifier/reward.txt').write_text('1' if ok else '0')
PY
