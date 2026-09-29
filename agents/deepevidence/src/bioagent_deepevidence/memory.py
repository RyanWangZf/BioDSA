from __future__ import annotations
import json
from pathlib import Path
class EvidenceMemory:
 def __init__(self,path:Path): self.path=path; self.data={"entities":[],"relations":[]}; self.path.parent.mkdir(parents=True,exist_ok=True); self._load()
 def _load(self):
  if self.path.is_file(): self.data=json.loads(self.path.read_text())
 def add(self,item):
  key=(item.get("source"),item.get("id"),item.get("title")); existing={(x.get("source"),x.get("id"),x.get("title")) for x in self.data["entities"]}
  if key not in existing: self.data["entities"].append(item); self.save()
 def retrieve(self,query):
  words=set(query.lower().split()); return [x for x in self.data["entities"] if words & set(json.dumps(x).lower().split())]
 def save(self): self.path.write_text(json.dumps(self.data,indent=2))
