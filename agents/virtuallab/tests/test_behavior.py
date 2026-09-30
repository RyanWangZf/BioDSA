import tempfile,unittest
from pathlib import Path
from bioagent_virtuallab import VirtualLabAgent

class VirtualLabBehaviorTest(unittest.TestCase):
 def test_team_and_individual_modes(self):
  team={"responses":{"team_lead_initial":"opening","team_member_response":["biology","statistics"],"team_lead_synthesize":"interim","team_lead_final":"team final"}}
  item={"instruction":"assess","mode":"team","rounds":1,"participants":[{"name":"lead","role":"leader"},{"name":"bio","role":"member"},{"name":"stats","role":"member"}]}
  with tempfile.TemporaryDirectory() as d:r=VirtualLabAgent(team,Path(d)).run(item)
  self.assertEqual(r["final_answer"],"team final");self.assertEqual([x["speaker"] for x in r["trajectory"]],["lead","bio","stats","lead","lead"])
  individual={"responses":{"individual_agent":"draft","individual_critic":{"issues":["missing control"]},"individual_revise":"revised with control","individual_complete":"individual final"}}
  with tempfile.TemporaryDirectory() as d:r=VirtualLabAgent(individual,Path(d)).run({"instruction":"design","mode":"individual","rounds":1,"agent":"scientist","critic":"reviewer"})
  self.assertEqual([x["event"] for x in r["trajectory"]],["individual_agent","individual_critic","individual_revise","individual_complete"]);self.assertEqual(r["final_answer"],"individual final")
if __name__=="__main__":unittest.main()
