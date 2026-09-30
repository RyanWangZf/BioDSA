from __future__ import annotations
import argparse, json, traceback
from pathlib import Path
from bioagent_harbor_runtime import run_batch
from .workflow import DeepRareAgent

def _worker(request: Path) -> int:
    data=json.loads(request.read_text()); item=data["item"]; output=Path(data["output"]); output.mkdir(parents=True,exist_ok=True)
    config={**data["config"], **item.get("agent_config", {})}; agent=DeepRareAgent(config)
    case=item.get("case", item)
    try: result=agent.run(case)
    except Exception as exc:
        (output/"trajectory.json").write_text(json.dumps(agent.trace,indent=2))
        (output/"failure.json").write_text(json.dumps({"type":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc()},indent=2)); raise
    (output/"final_answer.md").write_text(result["final_answer"])
    for filename,key in (("diagnoses.json","diagnoses"),("retrieval.json","retrieval"),("similar_cases.json","similar_checks"),("evidence.json","evidence"),("judgements.json","judgements"),("trajectory.json","trace"),("usage.json","usage")):
        (output/filename).write_text(json.dumps(result[key],indent=2,ensure_ascii=False))
    return 0

def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument("request",type=Path); parser.add_argument("--item-worker",action="store_true"); args=parser.parse_args()
    return _worker(args.request) if args.item_worker else run_batch(json.loads(args.request.read_text()),"bioagent_deeprare.harbor_runner",single_inputs=False)
if __name__=="__main__": raise SystemExit(main())
