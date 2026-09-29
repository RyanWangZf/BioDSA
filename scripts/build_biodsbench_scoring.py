"""Compile the pinned BioDSBench assertions into finite observation checks."""
from __future__ import annotations
import ast, json

BLOCKED = "assertion requires a boolean/comprehension operation outside the finite checker"

def literal(node):
    try: return True, ast.literal_eval(node)
    except Exception: return False, None

def literal_term(node):
    # Preserve tuples and non-string mapping keys across JSON serialization.
    return {"literal_source": ast.unparse(node)}

def observation(node, checks, observations):
    # Keep expected numeric values out of the untrusted observation spec.
    transform = None
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "abs" and len(node.args)==1:
        inner=node.args[0]
        if isinstance(inner,ast.BinOp) and isinstance(inner.op,ast.Sub):
            right_static,right=literal(inner.right)
            if right_static: node=inner.left; transform={"kind":"abs_diff","expected":right}
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=="round" and node.args:
        digits=literal(node.args[1]) if len(node.args)>1 else (True,0)
        if digits[0]: node=node.args[0]; transform={"kind":"round","digits":digits[1]}
    key=f"o{len(observations)}"; observations.append({"id":key,"expression":ast.unparse(node)})
    return {"observation":key,"transform":transform}

def compile_record(row):
    tree=ast.parse(row["test_cases"]); observations=[]; checks=[]; unsupported=[]
    setup=[node for node in tree.body if isinstance(node,(ast.Import,ast.ImportFrom,ast.Assign))]
    for number,node in enumerate(tree.body):
        if not isinstance(node,ast.Assert): continue
        test=node.test
        if isinstance(test,ast.Call) and isinstance(test.func,ast.Name) and test.func.id=="isinstance" and len(test.args)==2:
            checks.append({"kind":"type","actual":observation(test.args[0],checks,observations),"expected":ast.unparse(test.args[1])}); continue
        if not isinstance(test,ast.Compare) or len(test.ops)!=1 or len(test.comparators)!=1:
            checks.append({"kind":"truth","actual":observation(test,checks,observations)})
            continue
        left,right=test.left,test.comparators[0]; ls,lv=literal(left); rs,rv=literal(right)
        if ls and rs: unsupported.append({"assertion":number,"reason":"assertion has no submitted value"}); continue
        lhs=literal_term(left) if ls else observation(left,checks,observations)
        rhs=literal_term(right) if rs else observation(right,checks,observations)
        checks.append({"kind":"compare","op":type(test.ops[0]).__name__,"left":lhs,"right":rhs})
    names=sorted({n.id for obs in observations for n in ast.walk(ast.parse(obs["expression"])) if isinstance(n,ast.Name)})
    return {"item_id":row["unique_question_ids"],"original_assertions":row["test_cases"],"setup_code":"\n".join(ast.unparse(x) for x in setup),"observations":observations,"checks":checks,"required_variables":names,"export_types":["scalar","dataframe","series","ndarray","list","tuple","dict","set","type"],"supported":not unsupported,"blocking_reason":None if not unsupported else unsupported}

def build(rows): return [compile_record(row) for row in rows]

if __name__=="__main__":
    import pathlib,sys
    rows=[json.loads(x) for x in pathlib.Path(sys.argv[1]).read_text().splitlines()]
    print("".join(json.dumps(x)+"\n" for x in build(rows)),end="")
