from __future__ import annotations
import json,os,time,urllib.request
class MockClient:
 def synthesize(self,question,evidence):
  citations=[item["id"] for item in evidence[:5]]; return f"Evidence synthesis for {question}: " + "; ".join(item["title"] for item in evidence[:4]) + ". Citations: " + ", ".join(citations)
class OpenAIClient:
 def __init__(self,config): self.config=config
 def synthesize(self,question,evidence):
  endpoint=self.config.get("endpoint","https://api.openai.com/v1").rstrip("/")+"/chat/completions"; key=os.environ[self.config.get("api_key_env","OPENAI_API_KEY")]; payload={"model":self.config["model"],"temperature":self.config.get("temperature",0.1),"max_tokens":self.config.get("max_tokens",2000),"messages":[{"role":"system","content":"Synthesize biomedical evidence with explicit source identifiers. Do not invent citations."},{"role":"user","content":question+"\nEvidence:\n"+json.dumps(evidence)}]}
  if self.config.get("reasoning_effort"): payload["reasoning"]={"effort":self.config["reasoning_effort"]}
  request=urllib.request.Request(endpoint,data=json.dumps(payload).encode(),headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"}); attempts=int(self.config.get("max_attempts",2))
  for attempt in range(attempts):
   try:
    with urllib.request.urlopen(request,timeout=self.config.get("timeout_seconds",60)) as response: data=json.load(response)
    message=data["choices"][0]["message"]; text=message.get("content") or message.get("reasoning")
    if not text: raise RuntimeError(f"model returned no text (finish_reason={data['choices'][0].get('finish_reason')})")
    return text
   except Exception:
    if attempt+1==attempts: raise
    time.sleep(min(2**attempt,2))
