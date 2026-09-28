from __future__ import annotations
import json,os,signal,subprocess,sys,time,uuid
from dataclasses import asdict, dataclass
from pathlib import Path
@dataclass
class ExecutionResult:
 code:str; exit_code:int|None; stdout:str; stderr:str; timed_out:bool; duration_seconds:float
 def json(self): return asdict(self)
class PythonExecutionSession:
 def __init__(self,workspace:Path,timeout:float,env_names=None): self.workspace,self.timeout,self.closed,self.env_names=workspace.resolve(),timeout,False,env_names or []; self.workspace.mkdir(parents=True,exist_ok=True)
 def execute(self,code):
  if self.closed: raise RuntimeError("execution session is closed")
  started=time.monotonic()
  base={name:os.environ[name] for name in ("PATH","HOME","TMPDIR","LANG","LC_ALL","SSL_CERT_FILE","SSL_CERT_DIR") if name in os.environ}; sandbox_env={name:os.environ[name] for name in self.env_names if name in os.environ}; process=subprocess.Popen([sys.executable,"-c",code],cwd=self.workspace,env={**base,**sandbox_env},stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
  try:
   stdout,stderr=process.communicate(timeout=self.timeout); return ExecutionResult(code,process.returncode,stdout,stderr,False,time.monotonic()-started)
  except subprocess.TimeoutExpired:
   try: os.killpg(process.pid,signal.SIGTERM); process.wait(timeout=1)
   except subprocess.TimeoutExpired: os.killpg(process.pid,signal.SIGKILL); process.wait()
   stdout,stderr=process.communicate(); return ExecutionResult(code,process.returncode,stdout or "",stderr or "",True,time.monotonic()-started)
 def close(self): self.closed=True
 def __enter__(self): return self
 def __exit__(self,*_): self.close()
class FileExecutionSession:
 def __init__(self,channel:Path,timeout:float): self.channel,self.timeout,self.closed=channel,timeout,False
 def execute(self,code):
  if self.closed: raise RuntimeError("execution session is closed")
  request_id=uuid.uuid4().hex; requests=self.channel/"requests"; responses=self.channel/"responses"; requests.mkdir(parents=True,exist_ok=True); responses.mkdir(parents=True,exist_ok=True); temporary=requests/f".{request_id}.tmp"; target=requests/f"{request_id}.json"; temporary.write_text(json.dumps({"code":code,"timeout_seconds":self.timeout})); os.replace(temporary,target); response=responses/f"{request_id}.json"; deadline=time.monotonic()+self.timeout+5
  while time.monotonic()<deadline:
   if response.is_file(): value=json.loads(response.read_text()); response.unlink(missing_ok=True); return ExecutionResult(**value)
   time.sleep(.02)
  raise TimeoutError("sandbox response timed out")
 def close(self): self.closed=True
 def __enter__(self): return self
 def __exit__(self,*_): self.close()
def execution_session(config,workspace):
 settings=config["execution_environment"]; timeout=float(settings["timeout_seconds"])
 return FileExecutionSession(Path(settings["channel_dir"]),timeout) if settings.get("backend")=="file_channel" else PythonExecutionSession(workspace,timeout,settings.get("sandbox_env_names",[]))
