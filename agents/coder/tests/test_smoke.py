import tempfile, unittest
from pathlib import Path
from bioagent_coder.agent import CoderAgent
from bioagent_coder.execution import PythonExecutionSession
class Smoke(unittest.TestCase):
 def test_executes_code(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); (root/"data.csv").write_text("group,value\nA,1\nB,3\n"); result=CoderAgent({"provider":"mock","execution_environment":{"timeout_seconds":5}},root).run("Calculate the overall mean of the value column",["data.csv"]); self.assertEqual(result["execution_logs"][0]["exit_code"],0); self.assertTrue((root/"analysis_summary.csv").is_file())
 def test_timeout(self):
  with tempfile.TemporaryDirectory() as d: self.assertTrue(PythonExecutionSession(Path(d),.05).execute("import time; time.sleep(10)").timed_out)
if __name__=="__main__": unittest.main()
