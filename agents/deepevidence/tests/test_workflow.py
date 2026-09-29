import json,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
from bioagent_deepevidence.workflow import DeepEvidenceAgent
from bioagent_deepevidence.tools import KNOWLEDGE_BASES,build_tools
class WorkflowTests(unittest.TestCase):
 def config(self,**changes):
  value={"provider":"mock","tool_mode":"stub","knowledge_bases":["pubmed_papers","gene"],"routes":["bfs","dfs"],"main_search_rounds_budget":2,"main_action_rounds_budget":6,"subagent_action_rounds_budget":2,"memory":{"mode":"task"},"code_execution":{"enabled":True},"execution_environment":{"backend":"local_subprocess","timeout_seconds":2}}
  value.update(changes); return value
 def test_orchestrator_bfs_dfs_tools_memory_and_code(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary); result=DeepEvidenceAgent(self.config(),root).run("EGFR lung cancer")
   routes=[x["route"] for x in result["trace"] if x["event"]=="subagent_dispatched"]
   self.assertEqual(routes,["bfs","dfs"]); self.assertTrue(any(x["event"]=="tool_result" for x in result["trace"])); self.assertTrue(result["citations"]); self.assertTrue(result["memory_graph"]["entities"]); self.assertEqual(result["execution_logs"][0]["exit_code"],0); self.assertTrue((root/"evidence_counts.csv").is_file())
 def test_failure_timeout_and_budget_stop_are_traced(self):
  with tempfile.TemporaryDirectory() as temporary:
   result=DeepEvidenceAgent(self.config(subagent_action_rounds_budget=1),Path(temporary)).run("TOOL_TIMEOUT TOOL_FAILURE")
   self.assertTrue(any(x["event"]=="tool_error" and "timed out" in x["error"] for x in result["trace"])); self.assertTrue(any(x["event"]=="budget_stop" for x in result["trace"])); self.assertTrue(result["final_answer"])
  with tempfile.TemporaryDirectory() as temporary:
   failed=DeepEvidenceAgent(self.config(knowledge_bases=["pubmed_papers"]),Path(temporary)).run("TOOL_FAILURE")
   self.assertTrue(any(x["event"]=="tool_error" and "stub failure" in x["error"] for x in failed["trace"]))
  with tempfile.TemporaryDirectory() as temporary:
   failed=DeepEvidenceAgent(self.config(fail_routes=["bfs"]),Path(temporary)).run("subagent failure")
   self.assertTrue(any(x["event"]=="subagent_error" and x["route"]=="bfs" for x in failed["trace"])); self.assertTrue(any(x.get("route")=="dfs" for x in failed["trace"]))
 def test_task_memory_isolation(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary); first=root/"one"; second=root/"two"; DeepEvidenceAgent(self.config(),first).run("FIRST_MARKER"); agent=DeepEvidenceAgent(self.config(),second); self.assertEqual(agent.memory.data["entities"],[]); agent.run("SECOND_MARKER"); self.assertNotIn("FIRST_MARKER",(second/"evidence_graph.json").read_text())
 def test_unknown_or_unavailable_live_knowledge_base_fails_early(self):
  with tempfile.TemporaryDirectory() as temporary:
   with self.assertRaisesRegex(ValueError,"unknown knowledge bases"): DeepEvidenceAgent(self.config(knowledge_bases=["imaginary"]),Path(temporary))
   with self.assertRaisesRegex(RuntimeError,"target requires"): DeepEvidenceAgent(self.config(tool_mode="live",knowledge_bases=["target"]),Path(temporary))
 def test_all_legacy_knowledge_base_names_are_registered(self):
  self.assertEqual(set(KNOWLEDGE_BASES),{"pubmed_papers","gene","disease","drug","variant","clinical_trials","web_search","target","pathway","compound"})
  for name,tool in build_tools(KNOWLEDGE_BASES,"stub").items(): self.assertEqual(tool.search("smoke",1)[0]["source"],name)
 def test_evidence_gap_returns_ranked_unique_pubmed_ids(self):
  class PubMed:
   def search(self,query,limit):
    self.limit=limit
    return [{"source":"pubmed_papers","id":value,"title":value} for value in ("123","456","123")]
  tool=PubMed()
  with tempfile.TemporaryDirectory() as temporary, patch("bioagent_deepevidence.workflow.build_tools",return_value={"pubmed_papers":tool}):
   result=DeepEvidenceAgent(self.config(task_type="evidence_gap_retrieval",knowledge_bases=["pubmed_papers"],routes=["bfs"]),Path(temporary)).run("find studies")
   self.assertEqual(tool.limit,30)
   self.assertEqual(result["retrieved_pmids"],["123","456"])
if __name__=="__main__": unittest.main()
