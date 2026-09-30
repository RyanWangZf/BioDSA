import tempfile,unittest
from pathlib import Path
from bioagent_trialmind_slr import TrialMindSLRAgent

class TrialMindBehaviorTest(unittest.TestCase):
 def test_four_stages_and_exclusion(self):
  c={"responses":{"search_queries":[["diabetes"]],"eligibility_criteria":{"population":"adult"},"screen_study":[{"decision":"include","reason":"adult"},{"decision":"exclude","reason":"child"}],"extraction_fields":[["effect"]],"extract_study":[{"effect":0.7}],"synthesize_evidence":{"effect":0.7},"generate_report":"one included study"}}
  item={"instruction":"review diabetes","pubmed_fixture":[{"pmid":"1","search_text":"adult diabetes"},{"pmid":"2","search_text":"child diabetes"}]}
  with tempfile.TemporaryDirectory() as d:r=TrialMindSLRAgent(c,Path(d)).run(item)
  self.assertEqual(r["artifacts"]["prisma.json"],{"identified":2,"screened":2,"included":1});self.assertEqual(r["final_answer"],"one included study")
  events=[x["event"] for x in r["trajectory"]];self.assertLess(events.index("search_finalized"),events.index("screening_start"));self.assertLess(events.index("screening_finalized"),events.index("extraction_start"));self.assertEqual(events[-1],"synthesis_finalized")
if __name__=="__main__":unittest.main()
