#!/bin/sh
set -eu
python3 - <<'PY2'
import json
from pathlib import Path
s=Path('/app/submission/items/informgen-fixture')
ok=(s/'final_answer.md').is_file() and bool((s/'final_answer.md').read_text().strip())
try:
 events=[row['event'] for row in json.loads((s/'trajectory.json').read_text())]
 expected=['draft:summary', 'review:summary', 'revise:summary', 'section_complete', 'draft:methods', 'review:methods', 'assemble_document']
 pos=-1
 for event in expected:
  pos=events.index(event,pos+1)
except Exception:
 ok=False
Path('/logs/verifier/reward.txt').write_text('1' if ok else '0')
PY2
