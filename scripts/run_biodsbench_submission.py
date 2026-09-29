"""Run submitted code and export only trusted finite observations as JSON."""
from __future__ import annotations
import ast, json, math, operator, runpy, sys
from pathlib import Path

MAX_ELEMENTS=5_000_000
MAX_JSON_BYTES=128*1024*1024

def evaluate(node,state,scope=None):
    scope=scope or {}
    if isinstance(node,ast.Expression): return evaluate(node.body,state,scope)
    if isinstance(node,ast.Constant): return node.value
    if isinstance(node,ast.Name):
        if node.id in scope:return scope[node.id]
        if node.id in state:return state[node.id]
        allowed={"len":len,"abs":abs,"round":round,"all":all,"any":any,"set":set,"list":list,"tuple":tuple,"dict":dict,"sorted":sorted,"sum":sum,"min":min,"max":max,"int":int,"float":float}
        if node.id in allowed:return allowed[node.id]
        raise NameError(node.id)
    if isinstance(node,(ast.List,ast.Tuple,ast.Set)):
        values=[evaluate(x,state,scope) for x in node.elts]; return tuple(values) if isinstance(node,ast.Tuple) else set(values) if isinstance(node,ast.Set) else values
    if isinstance(node,ast.Dict): return {evaluate(k,state,scope):evaluate(v,state,scope) for k,v in zip(node.keys,node.values)}
    if isinstance(node,ast.Attribute):
        if node.attr.startswith("_"): raise ValueError("private attributes are forbidden")
        return getattr(evaluate(node.value,state,scope),node.attr)
    if isinstance(node,ast.Subscript):
        target=evaluate(node.value,state,scope)
        if isinstance(node.slice,ast.Slice): key=slice(*(evaluate(x,state,scope) if x else None for x in (node.slice.lower,node.slice.upper,node.slice.step)))
        else:key=evaluate(node.slice,state,scope)
        return target[key]
    if isinstance(node,ast.Call):
        fn=evaluate(node.func,state,scope); args=[evaluate(x,state,scope) for x in node.args]; kwargs={x.arg:evaluate(x.value,state,scope) for x in node.keywords}
        return fn(*args,**kwargs)
    if isinstance(node,ast.UnaryOp):
        value=evaluate(node.operand,state,scope); return {ast.USub:operator.neg,ast.UAdd:operator.pos,ast.Not:operator.not_}[type(node.op)](value)
    if isinstance(node,ast.BoolOp):
        if isinstance(node.op,ast.And):
            for child in node.values:
                value=evaluate(child,state,scope)
                if not value:return value
            return value
        for child in node.values:
            value=evaluate(child,state,scope)
            if value:return value
        return value
    if isinstance(node,ast.BinOp):
        a,b=evaluate(node.left,state,scope),evaluate(node.right,state,scope); return {ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Pow:operator.pow,ast.Mod:operator.mod}[type(node.op)](a,b)
    if isinstance(node,ast.Compare):
        left=evaluate(node.left,state,scope); operations={ast.Eq:operator.eq,ast.NotEq:operator.ne,ast.Lt:operator.lt,ast.LtE:operator.le,ast.Gt:operator.gt,ast.GtE:operator.ge,ast.In:lambda x,y:x in y,ast.NotIn:lambda x,y:x not in y}
        for index,(op,right_node) in enumerate(zip(node.ops,node.comparators)):
            right=evaluate(right_node,state,scope)
            compared=operations[type(op)](left,right)
            if index==len(node.ops)-1:return compared
            if not compared:return False
            left=right
    if isinstance(node,ast.IfExp): return evaluate(node.body if evaluate(node.test,state,scope) else node.orelse,state,scope)
    if isinstance(node,ast.Lambda):
        names=[arg.arg for arg in node.args.args]
        if node.args.vararg or node.args.kwarg or node.args.kwonlyargs: raise ValueError("complex lambda is unsupported")
        def finite_lambda(*values):
            if len(values)!=len(names): raise TypeError("lambda argument count mismatch")
            return evaluate(node.body,state,{**scope,**dict(zip(names,values))})
        return finite_lambda
    if isinstance(node,(ast.ListComp,ast.GeneratorExp)):
        if len(node.generators)!=1: raise ValueError("only one finite comprehension generator is supported")
        gen=node.generators[0]
        if not isinstance(gen.target,ast.Name): raise ValueError("complex comprehension target is unsupported")
        values=[]
        for item in evaluate(gen.iter,state,scope):
            local={**scope,gen.target.id:item}
            if all(evaluate(cond,state,local) for cond in gen.ifs): values.append(evaluate(node.elt,state,local))
        return iter(values) if isinstance(node,ast.GeneratorExp) else values
    raise ValueError(f"unsupported observation node: {type(node).__name__}")

def special(value):
    if isinstance(value,float):
        if math.isnan(value): return {"$float":"nan"}
        if math.isinf(value): return {"$float":"inf" if value>0 else "-inf"}
    return value

def encode(value):
    import numpy as np, pandas as pd
    if value is None or isinstance(value,(str,bool,int,float)): return {"type":"scalar","python_type":type(value).__name__,"value":special(value)}
    if isinstance(value,np.generic): return {"type":"scalar","python_type":type(value).__name__,"dtype":str(value.dtype),"value":special(value.item())}
    if isinstance(value,pd.Index):
        if value.size>MAX_ELEMENTS: raise ValueError("index exceeds element limit")
        return {"type":"list","values":[encode(x) for x in value.tolist()]}
    if isinstance(value,pd.DataFrame):
        if value.size>MAX_ELEMENTS: raise ValueError("dataframe exceeds element limit")
        return {"type":"dataframe","columns":[encode(x) for x in value.columns.tolist()],"index":[encode(x) for x in value.index.tolist()],"dtypes":[str(x) for x in value.dtypes],"data":[[encode(x) for x in row] for row in value.itertuples(index=False,name=None)]}
    if isinstance(value,pd.Series):
        if value.size>MAX_ELEMENTS: raise ValueError("series exceeds element limit")
        return {"type":"series","name":encode(value.name),"index":[encode(x) for x in value.index.tolist()],"dtype":str(value.dtype),"values":[encode(x) for x in value.tolist()]}
    if isinstance(value,np.ndarray):
        if value.size>MAX_ELEMENTS: raise ValueError("array exceeds element limit")
        return {"type":"ndarray","shape":list(value.shape),"dtype":str(value.dtype),"values":encode(value.tolist())}
    if isinstance(value,(list,tuple,set)):
        if len(value)>MAX_ELEMENTS: raise ValueError("sequence exceeds element limit")
        return {"type":type(value).__name__,"values":[encode(x) for x in value]}
    if isinstance(value,dict):
        if len(value)>MAX_ELEMENTS: raise ValueError("mapping exceeds element limit")
        return {"type":"dict","items":[[encode(k),encode(v)] for k,v in value.items()]}
    return {"type":"type","value":f"{type(value).__module__}.{type(value).__name__}"}

def main():
    code,spec_path,out=map(Path,sys.argv[1:4]); spec=json.loads(spec_path.read_text())
    state=runpy.run_path(str(code))
    if spec.get("setup_code"): exec(compile(spec["setup_code"],"<public-setup>","exec"),state)
    exported={}
    for obs in spec["observations"]:
        value=evaluate(ast.parse(obs["expression"],mode="eval"),state)
        exported[obs["id"]]=encode(value)
    payload=json.dumps({"status":"completed","observations":exported},allow_nan=False)
    if len(payload.encode())>MAX_JSON_BYTES: raise ValueError("export exceeds byte limit")
    out.write_text(payload)
if __name__=="__main__":
    try: main()
    except Exception as exc:
        Path(sys.argv[3]).write_text(json.dumps({"status":"failed","error":{"type":type(exc).__name__,"message":str(exc)[:1000]}})); raise
