#!/bin/sh
set -eu
python3 - <<'PY'
import json
from pathlib import Path
answer = Path('/app/submission/final_answer.md')
artifact = Path('/app/submission/artifact.json')
ok = answer.is_file() and answer.read_text().strip() == 'fixture completed'
ok = ok and artifact.is_file() and json.loads(artifact.read_text()) == {'status': 'ok'}
Path('/logs/verifier/reward.txt').write_text('1' if ok else '0')
PY
