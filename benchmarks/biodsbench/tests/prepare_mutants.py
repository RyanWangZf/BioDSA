"""Create one deterministic wrong-result submission for every pinned Python item."""
from __future__ import annotations
import argparse, ast, json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]

def assigned(code):
    names=set()
    try:tree=ast.parse(code)
    except SyntaxError:return names
    for node in ast.walk(tree):
        if isinstance(node,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
            targets=node.targets if isinstance(node,ast.Assign) else [node.target]
            for target in targets:
                names.update(value.id for value in ast.walk(target) if isinstance(value,ast.Name))
    return names

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,default=Path("/tmp/biodsbench-mutants"));args=parser.parse_args()
    refs=[json.loads(line) for line in (ROOT/"benchmarks/biodsbench/tasks/biodsbench-python/tests/references/references.jsonl").read_text().splitlines()]
    shutil.rmtree(args.output,ignore_errors=True);rows=[];mutations=[]
    for ref in refs:
        code="\n\n".join(value for value in (ref.get("code_history"),ref["reference_answer"]) if value)
        candidates=(assigned(code)-assigned(ref["scoring"]["setup_code"]))&set(ref["scoring"]["required_variables"])
        candidates-={"pd","np","os","plt","lifelines"}
        if not candidates:raise RuntimeError(f"no result variable can be mutated for {ref['item_id']}")
        variable=sorted(candidates)[0];item=args.output/"submission/items"/ref["item_id"];item.mkdir(parents=True);(item/"analysis.py").write_text(f"{code}\n\n{variable} = None\n")
        rows.append({"item_id":ref["item_id"],"status":"completed","artifacts_dir":f"items/{ref['item_id']}"});mutations.append({"item_id":ref["item_id"],"mutated_variable":variable})
    (args.output/"submission/predictions.jsonl").write_text("".join(json.dumps(row)+"\n" for row in rows));(args.output/"mutations.jsonl").write_text("".join(json.dumps(row)+"\n" for row in mutations));print(f"Prepared {len(mutations)} wrong-result submissions")

if __name__=="__main__":main()
