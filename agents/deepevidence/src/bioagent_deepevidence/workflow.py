from __future__ import annotations
import csv,json,re,time
from pathlib import Path
from .client import MockClient,OpenAIClient
from .execution import execution_session
from .memory import EvidenceMemory
from .prompts import ORCHESTRATOR_PROMPT,BFS_PROMPT,DFS_PROMPT
from .tools import build_tools
class DeepEvidenceAgent:
 def __init__(self,config,workspace):
  self.config,self.workspace=config,Path(workspace); self.trace=[]; self.client=MockClient() if config.get("provider","mock")=="mock" else OpenAIClient(config); memory=config.get("memory",{}); path=Path(memory["path"]).resolve() if memory.get("mode")=="shared" and memory.get("path") else self.workspace/"evidence_graph.json"; self.memory=EvidenceMemory(path); self.tools=build_tools(config.get("knowledge_bases",["pubmed_papers"]),config.get("tool_mode","stub"),config.get("tool_timeout_seconds",5)); self.tool_calls=0
 def _record(self,event,**values): self.trace.append({"event":event,"time":time.time(),**values})
 def _search(self,route,query):
  self._record("subagent_dispatched",route=route,prompt=BFS_PROMPT if route=="bfs" else DFS_PROMPT); found=[]; budget=int(self.config.get("subagent_action_rounds_budget",3))
  for index,(name,tool) in enumerate(self.tools.items()):
   if index>=budget: self._record("budget_stop",route=route,budget=budget); break
   if self.tool_calls>=int(self.config.get("tool_call_budget",10**9)): self._record("budget_stop",route=route,budget=self.config["tool_call_budget"],scope="tool_calls"); break
   try:
    self.tool_calls+=1; limit=30 if self.config.get("task_type")=="evidence_gap_retrieval" and name=="pubmed_papers" else (3 if route=="bfs" else 2); result=tool.search(query,limit); self._record("tool_result",route=route,tool=name,count=len(result)); found.extend(result)
   except Exception as exc: self._record("tool_error",route=route,tool=name,error=str(exc));
  for item in found: self.memory.add(item)
  return found
 def run(self,question,background=""):
  self._record("orchestrator_start",prompt=ORCHESTRATOR_PROMPT);evidence=[];routes=self.config.get("routes",["bfs","dfs"]);max_search=int(self.config.get("main_search_rounds_budget",2));task_type=self.config.get("task_type")
  queries=self.client.plan_queries(question,routes[:max_search]) if task_type=="evidence_gap_retrieval" else {route:question if route=="bfs" else question+" mechanisms" for route in routes[:max_search]};self._record("query_plan",queries=queries)
  action_budget=int(self.config.get("main_action_rounds_budget",6))
  for action,route in enumerate(routes[:max_search]):
   if action>=action_budget: self._record("budget_stop",scope="orchestrator",budget=action_budget); break
   try:
    if route in self.config.get("fail_routes",[]): raise RuntimeError(f"{route} subagent failed")
    result=self._search(route,queries[route]);evidence.extend(result)
   except Exception as exc: self._record("subagent_error",route=route,error=str(exc))
  retrieved=self.memory.retrieve(question); self._record("memory_retrieved",count=len(retrieved)); executions=[]; generated=[]
  if self.config.get("code_execution",{}).get("enabled"):
   code="import csv\nrows="+repr([(x.get('source'),x.get('id'),x.get('title')) for x in evidence])+"\nwith open('evidence_counts.csv','w',newline='') as f:\n w=csv.writer(f); w.writerow(['source','id','title']); w.writerows(rows)\nprint(len(rows))"
   generated.append(code); execution=execution_session(self.config,self.workspace).execute(code); executions.append(execution.json()); self._record("code_execution",exit_code=execution.exit_code,timed_out=execution.timed_out)
   if execution.timed_out or execution.exit_code!=0: raise RuntimeError("evidence code execution failed: "+execution.stderr)
  answer=self.client.synthesize(question,evidence,task_type);model_output=answer;self._record("synthesis_output",model_output=model_output);citations=[{"id":x["id"],"source":x["source"],"title":x["title"],"url":x.get("url")} for x in evidence]
  submitted_pmids=[]
  if task_type=="evidence_gap_retrieval":
   matches=re.findall(r"<BIOMED_FINAL>\s*(\{.*?\})\s*</BIOMED_FINAL>",answer,re.S)
   if len(matches)>1:raise RuntimeError("retrieval synthesis contains multiple BIOMED_FINAL objects")
   candidate=matches[0] if matches else answer.strip()
   if candidate.startswith("```"):candidate=re.sub(r"^```(?:json)?\s*|\s*```$","",candidate,flags=re.I)
   if not matches and not candidate.startswith("{"):
    found=re.search(r"\{\s*\"proposed_pmids\"\s*:.*?\}",candidate,re.S);candidate=found.group(0) if found else candidate
   try:payload=json.loads(candidate)
   except json.JSONDecodeError as exc:raise RuntimeError("retrieval synthesis BIOMED_FINAL is invalid JSON") from exc
   submitted_pmids=payload.get("proposed_pmids") if set(payload)=={"proposed_pmids"} else None
   evidence_pmids={str(item.get("id")) for item in evidence if item.get("source")=="pubmed_papers"}
   if not isinstance(submitted_pmids,list) or len(submitted_pmids)>30 or any(not isinstance(value,str) or not re.fullmatch(r"[1-9][0-9]*",value) for value in submitted_pmids) or len(submitted_pmids)!=len(set(submitted_pmids)):raise RuntimeError("retrieval synthesis returned an invalid PMID ranking")
   if not set(submitted_pmids)<=evidence_pmids:raise RuntimeError("retrieval synthesis selected PMID outside retrieved evidence")
   narrative=re.sub(r"<BIOMED_FINAL>.*?</BIOMED_FINAL>","",answer,flags=re.S).strip() if matches else "Model-selected PMID ranking."
   answer=narrative+"\n\n<BIOMED_FINAL>"+json.dumps({"proposed_pmids":submitted_pmids})+"</BIOMED_FINAL>"
  self._record("orchestrator_complete",evidence=len(evidence),submitted_pmids=submitted_pmids,model_output=model_output)
  return {"final_answer":answer,"submitted_pmids":submitted_pmids,"evidence":evidence,"citations":citations,"trace":self.trace,"memory_graph":self.memory.data,"generated_code":generated,"execution_logs":executions,"usage":{"model_calls":2 if task_type=="evidence_gap_retrieval" else 1,"tool_calls":self.tool_calls}}
