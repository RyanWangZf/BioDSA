#!/usr/bin/env python3
import argparse, json, os, tempfile
from pathlib import Path
def main():
    p=argparse.ArgumentParser(); p.add_argument("--request",required=True); p.add_argument("--output-dir",required=True); a=p.parse_args(); req=json.loads(Path(a.request).read_text()); result=json.loads(Path(req["agent_result_path"]).read_text()); refs=json.loads(Path(req["reference"]["path"]).read_text()); expected=refs[req["task_id"]]
    answer=result["output"]["final_answer"]; artifact=Path(req["artifacts_dir"])/"analysis_summary.csv"; score=float(expected in answer and artifact.is_file())
    value={"protocol_version":req["protocol_version"],"run_id":req["run_id"],"attempt_id":req["attempt_id"],"task_id":req["task_id"],"status":"scored","metrics":{"task_completed":score},"details":{"expected":expected,"artifact_found":artifact.is_file()},"evaluator":{"id":"fixture_analysis.artifact_check","version":"0.1.0"}}
    out=Path(a.output_dir)/"result.json"; fd,tmp=tempfile.mkstemp(dir=out.parent,prefix=".tmp-");
    with os.fdopen(fd,"w") as h: json.dump(value,h,indent=2); h.flush(); os.fsync(h.fileno())
    os.replace(tmp,out)
if __name__ == "__main__": main()
