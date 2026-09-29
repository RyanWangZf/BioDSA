#!/bin/sh
set -eu
python3 - <<'PY'
from pathlib import Path
p=Path('/app/submission/network.txt')
Path('/logs/verifier/reward.txt').write_text('1' if p.is_file() and p.read_text()=='blocked' else '0')
PY
