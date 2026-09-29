"""Compile the pinned BioDSBench assertions into trusted finite predicates."""
from __future__ import annotations
import ast
import json

def is_literal(node):
    try: ast.literal_eval(node); return True
    except Exception: return False

def literal_term(node): return {"literal_source": ast.unparse(node)}

def observation(node, observations):
    transform=None
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=="abs" and len(node.args)==1:
        inner=node.args[0]
        if isinstance(inner,ast.BinOp) and isinstance(inner.op,ast.Sub) and is_literal(inner.right):
            node=inner.left; transform={"kind":"abs_diff","expected_source":ast.unparse(inner.right)}
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=="round" and node.args and (len(node.args)==1 or is_literal(node.args[1])):
        transform={"kind":"round","digits_source":ast.unparse(node.args[1]) if len(node.args)>1 else "0"}; node=node.args[0]
    key=f"o{len(observations)}"; observations.append({"id":key,"expression":ast.unparse(node)})
    return {"observation":key,"transform":transform}

def term(node, observations): return literal_term(node) if is_literal(node) else observation(node,observations)

def comparison(node, observations):
    operands=[node.left,*node.comparators]; parts=[]
    for index,op in enumerate(node.ops):
        parts.append({"kind":"compare","op":type(op).__name__,"left":term(operands[index],observations),"right":term(operands[index+1],observations)})
    return parts[0] if len(parts)==1 else {"kind":"all","predicates":parts}

def membership_all(node, observations):
    if not isinstance(node.func,ast.Name) or node.func.id!="all" or len(node.args)!=1:return None
    value=node.args[0]
    if isinstance(value,(ast.GeneratorExp,ast.ListComp)) and len(value.generators)==1:
        gen=value.generators[0]; elt=value.elt
        if not gen.ifs and isinstance(gen.target,ast.Name) and isinstance(elt,ast.Compare) and len(elt.ops)==1 and isinstance(elt.ops[0],ast.In) and isinstance(elt.left,ast.Name) and elt.left.id==gen.target.id:
            return {"kind":"all_membership","items":term(gen.iter,observations),"container":term(elt.comparators[0],observations)}
    if isinstance(value,ast.Call) and isinstance(value.func,ast.Attribute) and value.func.attr=="all" and not value.args:
        mapped=value.func.value
        if isinstance(mapped,ast.Call) and isinstance(mapped.func,ast.Attribute) and mapped.func.attr=="map" and len(mapped.args)==1 and isinstance(mapped.args[0],ast.Lambda):
            lam=mapped.args[0]; body=lam.body
            if len(lam.args.args)==1 and isinstance(body,ast.Compare) and len(body.ops)==1 and isinstance(body.ops[0],ast.In) and isinstance(body.left,ast.Name) and body.left.id==lam.args.args[0].arg:
                return {"kind":"all_values_in","values":term(mapped.func.value,observations),"container":term(body.comparators[0],observations)}
    return None

def condition(node, observations):
    if isinstance(node,ast.Compare):return comparison(node,observations)
    if isinstance(node,ast.BoolOp):
        children=[condition(child,observations) for child in node.values]
        return None if any(child is None for child in children) else {"kind":"all" if isinstance(node.op,ast.And) else "any","predicates":children}
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.Not):
        child=condition(node.operand,observations)
        return {"kind":"not","predicate":child or {"kind":"truth","actual":term(node.operand,observations)}}
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=="isinstance" and len(node.args)==2:
        return {"kind":"type","actual":observation(node.args[0],observations),"expected":ast.unparse(node.args[1])}
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=="equals" and len(node.args)==1:
        return {"kind":"compare","op":"Eq","left":term(node.func.value,observations),"right":term(node.args[0],observations)}
    return membership_all(node,observations) if isinstance(node,ast.Call) else None

def compile_record(row):
    tree=ast.parse(row["test_cases"]); observations=[]; checks=[]; unsupported=[]; setup=[]
    for number,node in enumerate(tree.body):
        if isinstance(node,(ast.Import,ast.ImportFrom,ast.Assign,ast.Expr)):setup.append(node);continue
        if not isinstance(node,ast.Assert):unsupported.append({"statement":number,"reason":f"unsupported top-level {type(node).__name__}"});continue
        compiled=condition(node.test,observations)
        if compiled is None:unsupported.append({"assertion":number,"reason":f"unsupported assertion: {ast.unparse(node.test)}"})
        else:checks.append(compiled)
    if not checks:unsupported.append({"reason":"test contains no supported assertions"})
    names=sorted({n.id for obs in observations for n in ast.walk(ast.parse(obs["expression"])) if isinstance(n,ast.Name)})
    return {"item_id":row["unique_question_ids"],"original_assertions":row["test_cases"],"setup_code":"\n".join(ast.unparse(x) for x in setup),"observations":observations,"checks":checks,"required_variables":names,"export_types":["scalar","dataframe","series","ndarray","list","tuple","dict","set","type"],"supported":not unsupported,"blocking_reason":None if not unsupported else unsupported}

def build(rows):return [compile_record(row) for row in rows]

if __name__=="__main__":
    import pathlib,sys
    rows=[json.loads(x) for x in pathlib.Path(sys.argv[1]).read_text().splitlines()]
    print("".join(json.dumps(x)+"\n" for x in build(rows)),end="")
