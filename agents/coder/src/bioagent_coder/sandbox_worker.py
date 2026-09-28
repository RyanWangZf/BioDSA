from __future__ import annotations
import argparse,json,os,time
from pathlib import Path
from .execution import PythonExecutionSession

def main(argv=None):
    parser=argparse.ArgumentParser(); parser.add_argument("--channel",required=True); args=parser.parse_args(argv)
    channel=Path(args.channel); requests=channel/"requests"; responses=channel/"responses"; requests.mkdir(parents=True,exist_ok=True); responses.mkdir(parents=True,exist_ok=True)
    temporary=channel/".ready.tmp"; temporary.write_text(json.dumps({"status":"ready","pid":os.getpid()})); os.replace(temporary,channel/"ready.json")
    while True:
        for request in requests.glob("*.json"):
            try:
                value=json.loads(request.read_text()); result=PythonExecutionSession(Path.cwd(),float(value["timeout_seconds"]),list(os.environ)).execute(value["code"]).json(); response={"ok":True,"result":result}
            except Exception as exc:
                response={"ok":False,"error":{"code":"request_failed","message":str(exc),"recoverable":True}}
            temporary=responses/f".{request.stem}.tmp"; temporary.write_text(json.dumps(response)); os.replace(temporary,responses/f"{request.stem}.json"); request.unlink(missing_ok=True)
        time.sleep(.02)
if __name__=="__main__": raise SystemExit(main())
