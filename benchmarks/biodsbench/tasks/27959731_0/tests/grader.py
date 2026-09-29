from pathlib import Path
import runpy
p=Path('/app/submission/analysis.py')
reward=0.0
if p.is_file():
 try:
  state=runpy.run_path(str(p)); output_df=state['output_df']
  reward=float(len(output_df)==6 and list(output_df.columns)==['SOURCE','DISEASE','count'] and output_df[output_df['SOURCE']=='WashU_on_study']['count'].sum()==84)
 except (AssertionError,KeyError,TypeError,ValueError,ImportError,FileNotFoundError): pass
Path('/logs/verifier/reward.txt').write_text(str(reward))
