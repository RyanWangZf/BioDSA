from __future__ import annotations
import json,os,time,urllib.parse,urllib.request

KNOWLEDGE_BASES=("pubmed_papers","gene","disease","drug","variant","clinical_trials","web_search","target","pathway","compound")
ENDPOINTS={
 "pubmed_papers":"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax={limit}&term={query}",
 "gene":"https://mygene.info/v3/query?q={query}&size={limit}",
 "disease":"https://www.ebi.ac.uk/ols4/api/search?q={query}&rows={limit}",
 "drug":"https://www.ebi.ac.uk/chembl/api/data/molecule/search.json?q={query}&limit={limit}",
 "variant":"https://myvariant.info/v1/query?q={query}&size={limit}",
 "clinical_trials":"https://clinicaltrials.gov/api/v2/studies?query.term={query}&pageSize={limit}",
 "target":"https://api.platform.opentargets.org/api/v4/graphql",
 "pathway":"https://reactome.org/ContentService/search/query?query={query}&cluster=true&rows={limit}",
 "compound":"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{query}/property/Title,CanonicalSMILES/JSON",
}
class Tool:
 def __init__(self,name,mode="stub",timeout=5): self.name,self.mode,self.timeout=name,mode,timeout
 def search(self,query,limit=3):
  if "TOOL_TIMEOUT" in query: raise TimeoutError(f"{self.name} timed out after {self.timeout}s")
  if "TOOL_FAILURE" in query: raise RuntimeError(f"{self.name} stub failure")
  if self.mode=="stub": return [{"source":self.name,"id":f"{self.name}:{i+1}","title":f"{query} evidence {i+1}","snippet":f"Stub {self.name} evidence for {query}","url":f"https://example.invalid/{self.name}/{i+1}"} for i in range(min(limit,2))]
  if self.name=="web_search":
   if not os.environ.get("WEB_SEARCH_API_KEY"): raise RuntimeError("knowledge base web_search requires WEB_SEARCH_API_KEY")
   raise RuntimeError("web_search live adapter requires an explicitly configured provider endpoint")
  if self.name=="target": raise RuntimeError("target live adapter requires an explicit GraphQL query adapter")
  template=ENDPOINTS.get(self.name)
  if not template: raise RuntimeError(f"knowledge base {self.name} has no live adapter")
  url=template.format(query=urllib.parse.quote(query),limit=limit); request=urllib.request.Request(url,headers={"User-Agent":"BioAgent-Gym/0.1"})
  with urllib.request.urlopen(request,timeout=self.timeout) as response: data=json.load(response)
  if self.name=="pubmed_papers":
   ids=data.get("esearchresult",{}).get("idlist",[])[:limit]
   if not ids: return []
   summary_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id="+",".join(ids)
   with urllib.request.urlopen(urllib.request.Request(summary_url,headers={"User-Agent":"BioAgent-Gym/0.1"}),timeout=self.timeout) as response: summaries=json.load(response).get("result",{})
   return [{"source":self.name,"id":pmid,"title":summaries.get(pmid,{}).get("title",f"PubMed {pmid}"),"snippet":"Publication date: "+summaries.get(pmid,{}).get("pubdate","unknown"),"url":f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"} for pmid in ids]
  rows=[]
  candidates=data.get("hits") or data.get("studies") or data.get("molecules") or data.get("response",{}).get("docs") or data.get("PropertyTable",{}).get("Properties") or []
  for index,item in enumerate(candidates[:limit]): rows.append({"source":self.name,"id":str(item.get("_id") or item.get("nctId") or item.get("molecule_chembl_id") or index+1),"title":str(item.get("name") or item.get("Title") or item.get("briefTitle") or item.get("pref_name") or query),"snippet":json.dumps(item)[:500],"url":url})
  return rows
def build_tools(names,mode,timeout=5):
 unknown=set(names)-set(KNOWLEDGE_BASES)
 if unknown: raise ValueError("unknown knowledge bases: "+", ".join(sorted(unknown)))
 if mode not in ("stub","live"): raise ValueError("tool_mode must be stub or live")
 if mode=="live" and "web_search" in names and not os.environ.get("WEB_SEARCH_API_KEY"): raise RuntimeError("knowledge base web_search requires WEB_SEARCH_API_KEY")
 if mode=="live" and "target" in names: raise RuntimeError("knowledge base target requires a configured GraphQL adapter")
 return {name:Tool(name,mode,timeout) for name in names}
