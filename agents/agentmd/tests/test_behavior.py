import json,tempfile,unittest
from pathlib import Path
from bioagent_agentmd import AgentMD

class AgentMDBehaviorTest(unittest.TestCase):
 def test_calculator_retrieval_selection_and_execution(self):
  c={"retrieval_mode":"bm25","responses":{"calculator_query":{"terms":["bmi"]},"select_calculator":{"calculator_id":"bmi"},"extract_inputs":{"height_m":2.0,"weight_kg":80},"calculator_answer":"BMI is 20.0"}}
  item={"instruction":"BMI for 80 kg and 2 m","calculator_fixture":[{"id":"bmi","name":"BMI","kind":"bmi","keywords":["bmi","weight"]},{"id":"other","kind":"unsupported","keywords":["risk"]}]}
  with tempfile.TemporaryDirectory() as d:r=AgentMD(c,Path(d)).run(item)
  self.assertEqual(r["artifacts"]["calculator_result.json"]["result"],20);self.assertEqual([x["event"] for x in r["trajectory"]],["calculator_search","calculator_selected","calculator_run"])
 def test_missing_resources_are_explicit(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(RuntimeError,"RiskCalcs resource unavailable"):AgentMD({"responses":{}},Path(d)).run({"instruction":"risk"})
 def test_riskcalcs_loads_but_medcpt_resources_are_explicit(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/"riskcalcs.json";path.write_text(json.dumps({"1":{"title":"BMI calculator","purpose":"body mass index"}}))
   with self.assertRaisesRegex(RuntimeError,"MedCPT retrieval requires"):
    AgentMD({"retrieval_mode":"medcpt","riskcalcs_path":str(path),"responses":{}},Path(d)).run({"instruction":"BMI"})
if __name__=="__main__":unittest.main()
