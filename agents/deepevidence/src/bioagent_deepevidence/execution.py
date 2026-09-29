from __future__ import annotations
import json,os,signal,subprocess,sys,time,uuid
from dataclasses import asdict,dataclass
from pathlib import Path
@dataclass
class ExecutionResult:
 code:str; exit_code:int|None; stdout:str; stderr:str; timed_out:bool; duration_seconds:float
 def json(self): return asdict(self)
class PythonExecutionSession:
 def __init__(self,workspace,timeout,env_names=None): self.workspace,self.timeout,self.env_names=Path(workspace).resolve(),timeout,env_names or []; self.workspace.mkdir(parents=True,exist_ok=True)
 def execute(self,code):
  started=time.monotonic(); base={n:os.environ[n] for n in ("PATH","HOME","TMPDIR","LANG","LC_ALL","SSL_CERT_FILE","SSL_CERT_DIR") if n in os.environ}; allowed={n:os.environ[n] for n in self.env_names if n in os.environ}; process=subprocess.Popen([sys.executable,"-c",code],cwd=self.workspace,env={**base,**allowed},stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
  try: stdout,stderr=process.communicate(timeout=self.timeout); return ExecutionResult(code,process.returncode,stdout,stderr,False,time.monotonic()-started)
  except subprocess.TimeoutExpired:
   try: os.killpg(process.pid,signal.SIGTERM); process.wait(timeout=1)
   except subprocess.TimeoutExpired: os.killpg(process.pid,signal.SIGKILL); process.wait()
   stdout,stderr=process.communicate(); return ExecutionResult(code,process.returncode,stdout or "",stderr or "",True,time.monotonic()-started)
class FileExecutionSession:
 def __init__(self,channel,timeout): self.channel,self.timeout=Path(channel),timeout
 def execute(self,code):
  identifier=uuid.uuid4().hex; requests=self.channel/"requests"; responses=self.channel/"responses"; requests.mkdir(parents=True,exist_ok=True); responses.mkdir(parents=True,exist_ok=True); temporary=requests/f".{identifier}.tmp"; temporary.write_text(json.dumps({"code":code,"timeout_seconds":self.timeout})); os.replace(temporary,requests/f"{identifier}.json"); deadline=time.monotonic()+self.timeout+5
  while time.monotonic()<deadline:
   failure=self.channel/"worker-failure.json"
   if failure.is_file(): raise RuntimeError("sandbox worker failed: "+json.loads(failure.read_text()).get("message","unknown"))
   response=responses/f"{identifier}.json"
   if response.is_file():
    value=json.loads(response.read_text()); response.unlink(missing_ok=True)
    if not value.get("ok"): raise RuntimeError("sandbox request failed: "+value.get("error",{}).get("message","unknown"))
    return ExecutionResult(**value["result"])
   time.sleep(.02)
  raise TimeoutError("sandbox response timed out")
def execution_session(config,workspace):
 settings=config["execution_environment"]; timeout=float(settings.get("timeout_seconds",30))
 return FileExecutionSession(settings["channel_dir"],timeout) if settings.get("backend")=="file_channel" else PythonExecutionSession(workspace,timeout,settings.get("sandbox_env_names",[]))
