from __future__ import annotations
import json,os,re,time,urllib.request
class MockClient:
 def plan_queries(self,question,routes):return {route:question if route=="bfs" else question+" mechanisms" for route in routes}
 def synthesize(self,question,evidence,task_type=None):
  if task_type=="evidence_gap_retrieval":
   pmids=[]
   for item in evidence:
    value=str(item.get("id","")).strip()
    if item.get("source")=="pubmed_papers" and value.isdigit() and value not in pmids:pmids.append(value)
   return "Deterministic retrieval baseline.\n\n<BIOMED_FINAL>"+json.dumps({"proposed_pmids":pmids[:30]})+"</BIOMED_FINAL>"
  citations=[item["id"] for item in evidence[:5]];return f"Evidence synthesis for {question}: " + "; ".join(item["title"] for item in evidence[:4]) + ". Citations: " + ", ".join(citations)
class OpenAIClient:
 def __init__(self,config):self.config=config
 def _complete(self,system,user):
  endpoint=self.config.get("endpoint","https://api.openai.com/v1").rstrip("/")+"/chat/completions";key=os.environ[self.config.get("api_key_env","OPENAI_API_KEY")];payload={"model":self.config["model"],"temperature":self.config.get("temperature",0.1),"max_tokens":self.config.get("max_tokens",2000),"messages":[{"role":"system","content":system},{"role":"user","content":user}]}
  if self.config.get("reasoning_effort"):payload["reasoning"]={"effort":self.config["reasoning_effort"]}
  request=urllib.request.Request(endpoint,data=json.dumps(payload).encode(),headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"});attempts=int(self.config.get("max_attempts",2))
  for attempt in range(attempts):
   try:
    with urllib.request.urlopen(request,timeout=self.config.get("timeout_seconds",60)) as response:data=json.load(response)
    message=data["choices"][0]["message"];text=message.get("content") or message.get("reasoning")
    if not text:raise RuntimeError(f"model returned no text (finish_reason={data['choices'][0].get('finish_reason')})")
    return text
   except Exception:
    if attempt+1==attempts:raise
    time.sleep(min(2**attempt,2))
 def plan_queries(self,question,routes):
  text=self._complete("Generate concise PubMed search queries. Return only a JSON object mapping each requested route to one query.",json.dumps({"question":question,"routes":routes}))
  cleaned=text.strip()
  if cleaned.startswith("```"):cleaned=re.sub(r"^```(?:json)?\s*|\s*```$","",cleaned,flags=re.I)
  try:value=json.loads(cleaned)
  except json.JSONDecodeError as exc:raise RuntimeError("model query plan is not valid JSON") from exc
  if not isinstance(value,dict) or set(value)!=set(routes) or any(not isinstance(value[route],str) or not value[route].strip() for route in routes):raise RuntimeError("model query plan does not match requested routes")
  return {route:value[route].strip() for route in routes}
 def synthesize(self,question,evidence,task_type=None):
  system="Synthesize biomedical evidence with explicit source identifiers. Do not invent citations."
  if task_type=="evidence_gap_retrieval":system+=" Select and rank up to 30 PubMed IDs from the supplied evidence. End with exactly one <BIOMED_FINAL> JSON object whose only field is proposed_pmids."
  return self._complete(system,question+"\nEvidence:\n"+json.dumps(evidence))
