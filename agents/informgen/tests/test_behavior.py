import tempfile,unittest
from pathlib import Path
from bioagent_informgen import InformGenAgent

class InformGenBehaviorTest(unittest.TestCase):
 def test_two_sections_with_one_revision(self):
  c={"max_revisions":2,"responses":{"draft:summary":"summary draft","review:summary":[{"complete":False,"feedback":"add outcome"},{"complete":True}],"revise:summary":"summary revised with outcome","draft:methods":"methods draft","review:methods":{"complete":True},"assemble_document":"# Summary\nsummary revised with outcome\n# Methods\nmethods draft"}}
  item={"instruction":"write report","source_document":"trial source","template_sections":[{"name":"summary","requirements":"outcome"},{"name":"methods","requirements":"design"}]}
  with tempfile.TemporaryDirectory() as d:r=InformGenAgent(c,Path(d)).run(item)
  self.assertEqual(len(r["artifacts"]["section_drafts.json"]["summary"]),2);self.assertEqual(len(r["artifacts"]["section_drafts.json"]["methods"]),1);self.assertIn("summary revised",r["final_answer"])
if __name__=="__main__":unittest.main()
