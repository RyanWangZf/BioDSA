import tempfile,unittest
from pathlib import Path
from bioagent_dswizard.agent import DSWizardAgent
from bioagent_dswizard.execution import PythonExecutionSession
class Smoke(unittest.TestCase):
 def test_two_phase_execution(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); (root/"data.csv").write_text("group,value\nA,1\nB,3\n"); history="from pathlib import Path\nPath('history-ran').write_text('yes')"; result=DSWizardAgent({"provider":"mock","execution_environment":{"timeout_seconds":5}},root).run("Calculate the overall mean of the value column",["data.csv"],history); self.assertEqual(len(result["execution_logs"]),2); self.assertIn("Load and validate",result["analysis_plan"]); self.assertTrue((root/"analysis_summary.csv").is_file()); self.assertTrue((root/"history-ran").is_file()); self.assertEqual(result["execution_logs"][-1]["code"],result["final_program"]); self.assertNotIn(result["exploration_code"],result["final_program"])
 def test_timeout(self):
  with tempfile.TemporaryDirectory() as d: self.assertTrue(PythonExecutionSession(Path(d),.05).execute("import time; time.sleep(10)").timed_out)
if __name__=="__main__": unittest.main()
