import os,tempfile, unittest
from unittest import mock
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from bioagent_coder.agent import CoderAgent
from bioagent_coder.execution import PythonExecutionSession
class Smoke(unittest.TestCase):
 def test_executes_code(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); (root/"data.csv").write_text("group,value\nA,1\nB,3\n"); result=CoderAgent({"provider":"mock","execution_environment":{"timeout_seconds":5}},root).run("Calculate the overall mean of the value column",["data.csv"]); self.assertEqual(result["execution_logs"][0]["exit_code"],0); self.assertTrue((root/"analysis_summary.csv").is_file())
 def test_timeout(self):
  with tempfile.TemporaryDirectory() as d: self.assertTrue(PythonExecutionSession(Path(d),.05).execute("import time; time.sleep(10)").timed_out)
 def test_code_history_is_part_of_executed_and_submitted_program(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/"data.csv").write_text("group,value\nA,1\nB,3\n");history="open('history.marker','w').write('used')";result=CoderAgent({"provider":"mock","execution_environment":{"timeout_seconds":5}},root).run("Calculate the overall mean of the value column",["data.csv"],history)
   self.assertEqual((root/"history.marker").read_text(),"used");self.assertTrue(result["final_program"].startswith(history));self.assertEqual((root/"candidate_analysis.py").read_text(),result["final_program"]);self.assertTrue((root/"candidate_execution.json").is_file());self.assertEqual(result["execution_logs"][0]["exit_code"],0)
 def test_sandbox_environment_allowlist(self):
  with tempfile.TemporaryDirectory() as d:
   with mock.patch.dict(os.environ,{"DECLARED_FAKE":"yes","UNDECLARED_FAKE":"no"}): result=PythonExecutionSession(Path(d),2,["DECLARED_FAKE"]).execute("import os; print(os.getenv('DECLARED_FAKE'),os.getenv('UNDECLARED_FAKE'))")
   self.assertEqual(result.stdout.strip(),"yes None")
 def test_generated_code_reaches_controlled_endpoint(self):
  class Handler(BaseHTTPRequestHandler):
   def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"sandbox-online")
   def log_message(self,*_): pass
  try: server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
  except PermissionError: self.skipTest("test sandbox cannot bind a loopback endpoint")
  thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
  try:
   with tempfile.TemporaryDirectory() as d:
    result=PythonExecutionSession(Path(d),2).execute(f"import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:{server.server_port}',timeout=1).read().decode())")
    self.assertEqual(result.stdout.strip(),"sandbox-online")
  finally: server.shutdown(); server.server_close()
if __name__=="__main__": unittest.main()
