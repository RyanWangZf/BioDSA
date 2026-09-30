import tempfile,unittest
from pathlib import Path
from bioagent_trialgpt import TrialGPTAgent

class TrialGPTBehaviorTest(unittest.TestCase):
 def test_patient_retrieval_matching_and_ranking(self):
  c={"responses":{"retrieval_query":{"terms":["lung"]},"eligibility_match":[{"eligible":True,"inclusion":["NSCLC"],"exclusion":[]},{"eligible":False,"inclusion":[],"exclusion":["age"]}],"rank_trials":[[{"nct_id":"NCT1","score":0.9}]],"trial_summary":"NCT1 is the best eligible trial"}}
  item={"instruction":"match","patient":{"age":60,"condition":"NSCLC"},"trial_fixture":[{"nct_id":"NCT1","title":"lung trial","condition":"NSCLC","inclusion":["adult"]},{"nct_id":"NCT2","title":"lung trial 2","condition":"SCLC","exclusion":["older than 50"]}]}
  with tempfile.TemporaryDirectory() as d:r=TrialGPTAgent(c,Path(d)).run(item)
  self.assertEqual(r["artifacts"]["ranked_trials.json"][0]["nct_id"],"NCT1");self.assertEqual(r["artifacts"]["eligibility.json"][1]["eligible"],False);self.assertEqual(r["final_answer"],"NCT1 is the best eligible trial")
if __name__=="__main__":unittest.main()
