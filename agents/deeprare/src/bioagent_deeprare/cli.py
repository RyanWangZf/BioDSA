from __future__ import annotations
import argparse, json
from pathlib import Path
from .workflow import DeepRareAgent

def main()->int:
    parser=argparse.ArgumentParser(description="Run one phenotype-only case through DeepRare")
    parser.add_argument("case",type=Path); parser.add_argument("result",type=Path)
    parser.add_argument("--config",type=Path)
    args=parser.parse_args(); config=json.loads(args.config.read_text()) if args.config else {"provider":"gateway"}
    result=DeepRareAgent(config).run(json.loads(args.case.read_text()))
    args.result.write_text(result["final_answer"])
    return 0
if __name__=="__main__": raise SystemExit(main())
