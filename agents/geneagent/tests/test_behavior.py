import tempfile,unittest
from pathlib import Path
from bioagent_geneagent import GeneAgent

class GeneBehaviorTest(unittest.TestCase):
 def test_verification_changes_later_decisions(self):
  c={"responses":{"initial_gene_set_analysis":{"process":"old"},"topic_claims":[["claim-a","claim-b"]],"verify_claim":[{"verdict":"refuted"},{"verdict":"supported"},{"verdict":"supported"}],"topic_update":{"process":"updated"},"analysis_claims":[["analysis-c"]],"analysis_update":"final updated analysis"}}
  with tempfile.TemporaryDirectory() as d:r=GeneAgent(c,Path(d)).run({"instruction":"genes","genes":["TP53","EGFR"],"tool_fixture":{"pathway":{"TP53":"p53"}}})
  self.assertEqual(r["final_answer"],"final updated analysis");self.assertEqual(len(r["artifacts"]["topic_verification.json"]),2)
  update=next(x for x in r["trajectory"] if x["event"]=="topic_update");self.assertEqual(update["input"]["verification_reports"][0]["verification"]["verdict"],"refuted")
if __name__=="__main__":unittest.main()
