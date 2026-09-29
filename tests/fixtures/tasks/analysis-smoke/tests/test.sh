#!/bin/sh
set -eu
python3 - <<'PY'
import csv
from pathlib import Path
p=Path('/app/submission/analysis_summary.csv'); ok=p.is_file()
if ok:
 try: ok=list(csv.reader(p.open()))==[['group','count'],['A','2'],['B','2']]
 except Exception: ok=False
ok=ok and Path('/app/submission/analysis.py').is_file() and Path('/app/submission/final_answer.md').is_file()
Path('/logs/verifier/reward.txt').write_text('1' if ok else '0')
PY
