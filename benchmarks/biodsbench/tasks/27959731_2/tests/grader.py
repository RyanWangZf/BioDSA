from pathlib import Path
import runpy
p=Path('/app/submission/analysis.py'); reward=0.0
if p.is_file():
 try: reward=float(runpy.run_path(str(p))['n']==20)
 except (AssertionError,KeyError,TypeError,ValueError,ImportError,FileNotFoundError): pass
Path('/logs/verifier/reward.txt').write_text(str(reward))
