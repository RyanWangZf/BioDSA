from __future__ import annotations
import argparse, json
from pathlib import Path
from bioagent_harbor_runtime import run_batch

def worker(path: Path) -> int:
    request=json.loads(path.read_text()); item=request["item"]; output=Path(request["output"]); output.mkdir(parents=True)
    options=item.get("valid_options") or []
    selected=[] if not options else [options[0]["id"] if isinstance(options[0],dict) else options[0]]
    answer=f"<BIOMED_FINAL>{json.dumps({'selected_options':selected})}</BIOMED_FINAL>"
    (output/"final_answer.md").write_text(answer); (output/"usage.json").write_text(json.dumps({"fixture_calls":1})); return 0

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("request",type=Path); parser.add_argument("--item-worker",action="store_true"); args=parser.parse_args()
    return worker(args.request) if args.item_worker else run_batch(json.loads(args.request.read_text()),"bioagent_fixture.bdr_runner",single_inputs=False,valid_splits={"fit","tune","verifier"})
if __name__ == "__main__": raise SystemExit(main())
