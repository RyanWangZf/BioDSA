from __future__ import annotations
import json,os,time,urllib.request
class MockClient:
 def synthesize(self,question,evidence):
  citations=[item["id"] for item in evidence[:5]]; return f"Evidence synthesis for {question}: " + "; ".join(item["title"] for item in evidence[:4]) + ". Citations: " + ", ".join(citations)
class OpenAIClient:
 def __init__(self,config): self.config=config
 def synthesize(self,question,evidence):
  endpoint=self.config.get("endpoint","https://api.openai.com/v1").rstrip("/")+"/chat/completions"; key=os.environ[self.config.get("api_key_env","OPENAI_API_KEY")]; payload={"model":self.config["model"],"temperature":self.config.get("temperature",0.1),"messages":[{"role":"system","content":"Synthesize biomedical evidence with explicit source identifiers. Do not invent citations."},{"role":"user","content":question+"\nEvidence:\n"+json.dumps(evidence)}]}; request=urllib.request.Request(endpoint,data=json.dumps(payload).encode(),headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"}); attempts=int(self.config.get("max_attempts",2))
  for attempt in range(attempts):
   try:
    with urllib.request.urlopen(request,timeout=self.config.get("timeout_seconds",60)) as response: return json.load(response)["choices"][0]["message"]["content"]
   except Exception:
    if attempt+1==attempts: raise
    time.sleep(min(2**attempt,2))
