"""Trusted BioDSBench grader over JSON observations from an unprivileged runner."""
from __future__ import annotations
import ast, json, math, operator, os, resource, shutil, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path

def restrict_submission():
    resource.setrlimit(resource.RLIMIT_CPU,(60,60)); resource.setrlimit(resource.RLIMIT_AS,(3*1024**3,3*1024**3)); resource.setrlimit(resource.RLIMIT_FSIZE,(128*1024**2,128*1024**2)); resource.setrlimit(resource.RLIMIT_NPROC,(64,64)); os.setgroups([]); os.setgid(65534); os.setuid(65534)

def decode(encoded):
    if not isinstance(encoded,dict) or "type" not in encoded:return encoded
    kind=encoded["type"]
    if kind=="scalar":
        value=encoded.get("value")
        if isinstance(value,dict) and "$float" in value:return {"nan":math.nan,"inf":math.inf,"-inf":-math.inf}[value["$float"]]
        return value
    if kind in {"list","tuple","set"}:
        values=[decode(x) for x in encoded["values"]];return tuple(values) if kind=="tuple" else set(values) if kind=="set" else values
    if kind=="dict":return {decode(k):decode(v) for k,v in encoded["items"]}
    if kind=="ndarray":return decode(encoded["values"])
    if kind=="series":return [decode(x) for x in encoded["values"]]
    return encoded
def scalar(encoded):
    value=decode(encoded)
    return value

def apply_transform(value, transform):
    if not transform:return value
    value=scalar(value)
    if transform["kind"]=="abs_diff": return abs(value-transform["expected"])
    if transform["kind"]=="round": return round(value,transform["digits"])
    raise ValueError("unknown transform")

OPS={"Eq":operator.eq,"NotEq":operator.ne,"Lt":operator.lt,"LtE":operator.le,"Gt":operator.gt,"GtE":operator.ge,"In":lambda a,b:a in b,"NotIn":lambda a,b:a not in b}
def resolve(term,observations):
    if "literal_source" in term:return ast.literal_eval(term["literal_source"])
    if "literal" in term:return term["literal"]
    return apply_transform(observations[term["observation"]],term.get("transform"))
def check_one(check,observations):
    if check["kind"]=="truth":
        return bool(scalar(observations[check["actual"]["observation"]]))
    if check["kind"]=="type":
        actual=observations[check["actual"]["observation"]]
        if actual.get("type")=="type": typename=actual["value"]
        else: typename={"series":"pandas.core.series.Series","dataframe":"pandas.core.frame.DataFrame","ndarray":"numpy.ndarray"}.get(actual.get("type"),actual.get("type"))
        expected=check["expected"].split(".")[-1]
        if actual.get("type")=="scalar":
            value=decode(actual)
            if expected in {"float","int","str","bool"}: return isinstance(value,{"float":float,"int":int,"str":str,"bool":bool}[expected])
            typename=actual.get("python_type",typename)
        return typename.split(".")[-1]==expected
    left,right=resolve(check["left"],observations),resolve(check["right"],observations)
    left=scalar(left); right=scalar(right)
    if check["op"] in {"Eq","NotEq"} and isinstance(left,float) and isinstance(right,float) and math.isnan(left) and math.isnan(right): return check["op"]=="Eq"
    compared=OPS[check["op"]](left,right)
    if isinstance(compared,list): return len(compared)==1 and bool(compared[0])
    # NumPy's original assertion semantics accept a one-element array.
    if check["op"] in {"Eq","NotEq"}:
        if isinstance(left,list) and len(left)==1 and not isinstance(right,(list,tuple,dict,set)): return bool(OPS[check["op"]](left[0],right))
        if isinstance(right,list) and len(right)==1 and not isinstance(left,(list,tuple,dict,set)): return bool(OPS[check["op"]](left,right[0]))
    return bool(compared)

refs={x["item_id"]:x for x in map(json.loads,Path("/tests/references/references.jsonl").read_text().splitlines())}
selected=[x for x in os.environ.get("BIOAGENT_ITEM_IDS","").split(",") if x] or list(refs)
if len(selected)!=len(set(selected)) or set(selected)-set(refs): raise SystemExit("invalid trusted BioDSBench selection")
preds={}; malformed=[]; duplicates=[]
p=Path("/app/submission/predictions.jsonl")
if p.is_file():
    for number,line in enumerate(p.read_text().splitlines(),1):
        try:
            row=json.loads(line); item_id=row["item_id"]
            if item_id in preds: duplicates.append(item_id)
            else:preds[item_id]=row
        except Exception:malformed.append(number)
unknown=sorted(set(preds)-set(selected)); results=[]
for item_id in selected:
    ref,pred=refs[item_id],preds.get(item_id); base={"item_id":item_id,"subset":"python","split":"benchmark"}
    if pred is None:results.append({**base,"status":"missing","score":0.0,"error":"prediction missing"});continue
    if pred.get("status")=="timeout":results.append({**base,"status":"agent_timeout","score":0.0,"error":pred.get("error")});continue
    if pred.get("status")!="completed":results.append({**base,"status":"agent_error","score":0.0,"error":pred.get("error")});continue
    if not ref["scoring"]["supported"]:results.append({**base,"status":"unscorable","score":None,"error":ref["scoring"]["blocking_reason"]});continue
    code=Path("/app/submission")/pred["artifacts_dir"]/"analysis.py"
    if not code.is_file():results.append({**base,"status":"missing","score":0.0,"error":"analysis.py missing"});continue
    study=ref["study_id"]; workdir=Path("/workdir")
    try:
        if workdir.exists() or workdir.is_symlink(): workdir.unlink()
        workdir.symlink_to(Path("/app/data/inputs")/study,target_is_directory=True)
        with tempfile.TemporaryDirectory(dir="/tmp") as temp:
            temp=Path(temp); os.chmod(temp,0o777); (temp/"workdir").symlink_to(Path("/app/data/inputs")/study,target_is_directory=True); spec=temp/"spec.json"; output=temp/"result.json"; spec.write_text(json.dumps({"setup_code":ref["scoring"]["setup_code"],"observations":ref["scoring"]["observations"]})); os.chmod(spec,0o644)
            proc=subprocess.run([sys.executable,"/tests/run_submission.py",str(code),str(spec),str(output)],cwd=str(temp),capture_output=True,text=True,timeout=75,preexec_fn=restrict_submission)
            exported=json.loads(output.read_text()) if output.is_file() else {"status":"failed","error":{"message":"no result export"}}
        if proc.returncode or exported.get("status")!="completed": results.append({**base,"status":"agent_error","score":0.0,"error":exported.get("error")});continue
        checks=[check_one(c,exported["observations"]) for c in ref["scoring"]["checks"]]
        results.append({**base,"status":"scored","score":float(all(checks)),"assertions_passed":sum(checks),"assertions_total":len(checks),"failed_assertions":[i for i,value in enumerate(checks) if not value]})
    except subprocess.TimeoutExpired:results.append({**base,"status":"agent_timeout","score":0.0,"error":"verifier replay timeout"})
    except Exception as exc:results.append({**base,"status":"grading_error","score":None,"error":f"{type(exc).__name__}: {exc}"})
    finally:
        if workdir.is_symlink():workdir.unlink()
if malformed or duplicates or unknown:results.append({"item_id":"<predictions>","subset":"python","split":"benchmark","status":"grading_error","score":None,"error":{"malformed_lines":malformed,"duplicate_ids":duplicates,"unknown_ids":unknown}})
c=Counter(x["status"] for x in results); expected=[x for x in results if x["item_id"]!="<predictions>"]; valid=[x for x in expected if x["status"] in {"scored","missing","agent_timeout","agent_error"}]
summary={"expected_total":len(expected),"attempted":len(expected)-c["missing"],"validly_evaluated":len(valid),"missing":c["missing"],"agent_timeout":c["agent_timeout"],"agent_error":c["agent_error"],"unscorable":c["unscorable"],"grading_error":c["grading_error"],"accuracy":sum((x["score"] or 0) for x in valid)/len(expected) if expected and not c["unscorable"] and not c["grading_error"] else None}
logs=Path("/logs/verifier");logs.mkdir(parents=True,exist_ok=True);(logs/"per_item_results.jsonl").write_text("".join(json.dumps(x)+"\n" for x in results));(logs/"summary.json").write_text(json.dumps(summary,indent=2))
if summary["accuracy"] is None:print("evaluation incomplete; see summary.json",file=sys.stderr);raise SystemExit(2)
(logs/"reward.txt").write_text(str(summary["accuracy"]))
