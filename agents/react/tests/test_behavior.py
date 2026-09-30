import tempfile, unittest
from pathlib import Path
from bioagent_react import ReActAgent

class ReActBehaviorTest(unittest.TestCase):
 def test_tool_feedback_loop_and_first_call_limit(self):
  config={"responses":{"react_decision":[{"tool_calls":[{"name":"code_execution","args":{"code":"print(6*7)"}},{"name":"code_execution","args":{"code":"raise Exception('must not run')"}}]},{"final_answer":"42","tool_calls":[]}]}}
  with tempfile.TemporaryDirectory() as d:
   result=ReActAgent(config,Path(d)).run({"instruction":"compute","code_history":"seed=6"})
  self.assertEqual(result["final_answer"],"42");self.assertEqual(result["artifacts"]["code_execution.json"][0]["stdout"].strip(),"42");self.assertEqual(result["usage"]["tool_calls"],1)
  self.assertEqual([x["event"] for x in result["trajectory"]],["model_decision","tool_result","model_decision","stop"])
  self.assertEqual(result["artifacts"]["code_execution.json"][0]["executed_code"].count("seed=6"),1)
if __name__=="__main__":unittest.main()
