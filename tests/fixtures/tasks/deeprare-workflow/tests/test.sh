#!/bin/sh
set -eu
python3 - <<'PY'
import json
from pathlib import Path
p=Path('/app/submission/items/deeprare-normal')
ok=(p/'final_answer.md').is_file()
try:
 d=json.loads((p/'diagnoses.json').read_text()); t=json.loads((p/'trajectory.json').read_text())
 roles=[x.get('role') for x in t if x.get('event')=='model_result']
 ok=ok and d[0]['diagnosis_id']=='ORPHA:123' and roles==['zero-shot diagnostician','central host candidate-fusion agent','candidate-specific disease checking agent','central host final reflection agent']
except Exception: ok=False
Path('/logs/verifier/reward.txt').write_text('1' if ok else '0')
PY
