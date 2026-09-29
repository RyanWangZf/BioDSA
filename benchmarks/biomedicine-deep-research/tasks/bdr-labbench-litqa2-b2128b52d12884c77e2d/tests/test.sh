#!/bin/sh
set -eu
python3 - <<'PY'
import json,re
from pathlib import Path
p=Path('/app/submission/final_answer.md'); reward=0.0
if p.is_file():
 m=re.findall(r'<BIOMED_FINAL>\s*(\{.*?\})\s*</BIOMED_FINAL>',p.read_text(),re.S)
 if m:
  try: reward=float(json.loads(m[-1])=={'selected_options':['D']})
  except (ValueError,TypeError,json.JSONDecodeError): pass
Path('/logs/verifier/reward.txt').write_text(str(reward))
PY
