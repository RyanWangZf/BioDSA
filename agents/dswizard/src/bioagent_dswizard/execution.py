from __future__ import annotations
import os,signal,subprocess,sys,time
from dataclasses import asdict, dataclass
from pathlib import Path
@dataclass
class ExecutionResult:
 code:str; exit_code:int|None; stdout:str; stderr:str; timed_out:bool; duration_seconds:float
 def json(self): return asdict(self)
class PythonExecutionSession:
 def __init__(self,workspace:Path,timeout:float): self.workspace,self.timeout,self.closed=workspace.resolve(),timeout,False; self.workspace.mkdir(parents=True,exist_ok=True)
 def execute(self,code):
  if self.closed: raise RuntimeError("execution session is closed")
  started=time.monotonic()
  process=subprocess.Popen([sys.executable,"-c",code],cwd=self.workspace,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
  try:
   stdout,stderr=process.communicate(timeout=self.timeout); return ExecutionResult(code,process.returncode,stdout,stderr,False,time.monotonic()-started)
  except subprocess.TimeoutExpired:
   try: os.killpg(process.pid,signal.SIGTERM); process.wait(timeout=1)
   except subprocess.TimeoutExpired: os.killpg(process.pid,signal.SIGKILL); process.wait()
   stdout,stderr=process.communicate(); return ExecutionResult(code,process.returncode,stdout or "",stderr or "",True,time.monotonic()-started)
 def close(self): self.closed=True
 def __enter__(self): return self
 def __exit__(self,*_): self.close()
