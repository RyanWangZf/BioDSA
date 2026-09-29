from pathlib import Path
import runpy
p=Path('/app/submission/analysis.py'); reward=0.0
if p.is_file():
 try:
  s=runpy.run_path(str(p)); has_plot=any(x.suffix.lower() in {'.png','.pdf','.svg'} for x in Path('/app/submission').iterdir())
  reward=float(round(s['mean_age1'],2)==72.41 and round(s['mean_age2'],2)==71.27 and round(s['mean_age3'],2)==65.79 and has_plot)
 except (AssertionError,KeyError,TypeError,ValueError,ImportError,FileNotFoundError): pass
Path('/logs/verifier/reward.txt').write_text(str(reward))
