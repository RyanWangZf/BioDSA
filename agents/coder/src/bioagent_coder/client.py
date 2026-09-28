from __future__ import annotations
import json, os, time, urllib.request

class MockClient:
    def code(self, task: str, data_file: str) -> str:
        if "Count rows per group" in task:
            return f'''import csv\nfrom collections import Counter\nrows=list(csv.DictReader(open({data_file!r})))\ncounts=Counter(r["group"] for r in rows)\nwith open("analysis_summary.csv","w",newline="") as f:\n w=csv.writer(f); w.writerow(["group","count"]); w.writerows(sorted(counts.items()))\nprint("A=2, B=2")'''
        return f'''import csv\nrows=list(csv.DictReader(open({data_file!r})))\nmean=sum(float(r["value"]) for r in rows)/len(rows)\nwith open("analysis_summary.csv","w",newline="") as f:\n w=csv.writer(f); w.writerow(["metric","value"]); w.writerow(["mean",mean])\nprint(f"{{mean:.1f}}")'''
    def final(self, task: str, stdout: str) -> str: return f"Completed the requested analysis. Result: {stdout.strip()}"

class OpenAICompatibleClient:
    def __init__(self, config): self.config=config
    def complete(self, messages):
        provider=self.config.get("provider","openai"); model=self.config["model"]; key=os.environ[self.config.get("api_key_env",{"anthropic":"ANTHROPIC_API_KEY","google":"GOOGLE_API_KEY","azure":"AZURE_OPENAI_API_KEY"}.get(provider,"OPENAI_API_KEY"))]
        if provider=="anthropic": endpoint=self.config.get("endpoint","https://api.anthropic.com/v1/messages"); payload={"model":model,"max_tokens":self.config.get("max_tokens",5000),"messages":[m for m in messages if m["role"]!="system"],"system":"\n".join(m["content"] for m in messages if m["role"]=="system")}; headers={"x-api-key":key,"anthropic-version":"2023-06-01","Content-Type":"application/json"}
        elif provider=="google": endpoint=self.config.get("endpoint",f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent")+f"?key={key}"; payload={"contents":[{"role":"model" if m["role"]=="assistant" else "user","parts":[{"text":m["content"]}]} for m in messages]}; headers={"Content-Type":"application/json"}
        else:
            if provider=="azure": endpoint=self.config["endpoint"].rstrip("/")+f"/openai/deployments/{model}/chat/completions?api-version="+self.config.get("api_version","2024-12-01-preview"); headers={"api-key":key,"Content-Type":"application/json"}
            else: endpoint=self.config.get("endpoint","https://api.openai.com/v1").rstrip("/")+"/chat/completions"; headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"}
            payload={"model":model,"messages":messages,"temperature":self.config.get("temperature",1.0)}
        request=urllib.request.Request(endpoint,data=json.dumps(payload).encode(),headers=headers)
        attempts=int(self.config.get("max_attempts",3))
        for attempt in range(attempts):
            try:
                with urllib.request.urlopen(request,timeout=self.config.get("timeout_seconds",60)) as response: data=json.load(response)
                break
            except Exception:
                if attempt + 1 == attempts: raise
                time.sleep(min(2 ** attempt, 4))
        if provider=="anthropic": return data["content"][0]["text"]
        if provider=="google": return data["candidates"][0]["content"]["parts"][0]["text"]
        return data["choices"][0]["message"]["content"]
