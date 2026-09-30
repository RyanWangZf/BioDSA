#!/bin/sh
set -eu
python3 - <<'PY2'
import json
from pathlib import Path
root=Path('/app/submission/items')
checks={
 'virtuallab-fixture':['team_lead_initial','team_member_response','team_lead_synthesize','team_lead_final'],
 'virtuallab-individual-fixture':['individual_agent','individual_critic','individual_revise','individual_complete'],
}
ok=True
for item_id,expected in checks.items():
 try:
  output=root/item_id;events=[row['event'] for row in json.loads((output/'trajectory.json').read_text())]
  pos=-1
  for event in expected:pos=events.index(event,pos+1)
  ok=ok and bool((output/'final_answer.md').read_text().strip())
 except Exception:ok=False
Path('/logs/verifier/reward.txt').write_text('1' if ok else '0')
PY2
