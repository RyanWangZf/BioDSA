#!/bin/sh
set -eu
python3 - <<'PY2'
import json
from pathlib import Path
s=Path('/app/submission/items/geneagent-fixture')
ok=(s/'final_answer.md').is_file() and bool((s/'final_answer.md').read_text().strip())
try:
 events=[row['event'] for row in json.loads((s/'trajectory.json').read_text())]
 expected=['initial_gene_set_analysis', 'topic_claims', 'verify_claim', 'topic_update', 'analysis_claims', 'analysis_update']
 pos=-1
 for event in expected:
  pos=events.index(event,pos+1)
except Exception:
 ok=False
Path('/logs/verifier/reward.txt').write_text('1' if ok else '0')
PY2
