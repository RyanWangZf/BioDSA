from pathlib import Path
import runpy
p=Path('/app/submission/analysis.py'); reward=0.0
if p.is_file():
 try:
  s=runpy.run_path(str(p)); reward=float(s['n_cr']==15 and s['n_cri']==24 and s['n_or']==39)
 except (AssertionError,KeyError,TypeError,ValueError,ImportError,FileNotFoundError): pass
Path('/logs/verifier/reward.txt').write_text(str(reward))
