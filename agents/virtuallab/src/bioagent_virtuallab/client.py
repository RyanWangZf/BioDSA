from __future__ import annotations
import json, os, urllib.request

class ModelClient:
    def __init__(self, config): self.config=config; self.calls=[]
    def complete(self, stage, payload):
        self.calls.append({"stage":stage,"payload":payload})
        scripted=self.config.get("responses",{})
        value=scripted.get(stage)
        if isinstance(value,list):
            if not value: raise RuntimeError(f"fixture responses exhausted for {stage}")
            return value.pop(0)
        if value is not None:return value
        if self.config.get("provider","fixture")=="fixture":raise RuntimeError(f"missing fixture response for {stage}")
        key=os.environ.get(self.config.get("api_key_env","OPENAI_API_KEY"))
        if not key:raise RuntimeError("model credential unavailable")
        body=json.dumps({"model":self.config["model"],"messages":[{"role":"system","content":stage},{"role":"user","content":json.dumps(payload)}],"max_tokens":self.config.get("max_tokens",2000)}).encode()
        req=urllib.request.Request(self.config.get("endpoint","https://api.openai.com/v1")+"/chat/completions",body,{"Authorization":f"Bearer {key}","Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=self.config.get("timeout_seconds",60)) as response: content=json.loads(response.read())["choices"][0]["message"]["content"]
        try:return json.loads(content)
        except (json.JSONDecodeError,TypeError):return content
