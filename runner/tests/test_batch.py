import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from bioagent_harbor_runtime.batch import _load_items, _terminate, run_batch

class BatchRuntimeTests(unittest.TestCase):
    def test_per_dataset_selection_is_strict(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory); (app / "data").mkdir()
            (app / "data/items.jsonl").write_text(json.dumps({"item_id":"known", "source_split":"fit"}) + "\n")
            (app / "data/manifest.json").write_text(json.dumps({"subset":"fixture"}))
            with self.assertRaisesRegex(ValueError, "unknown item_ids"):
                _load_items({"instruction":"x", "split":"fit", "item_ids_by_dataset":{"fixture":["missing"]}}, app, False, {"fit"})
            with self.assertRaisesRegex(ValueError, "no selection"):
                _load_items({"instruction":"x", "split":"fit", "item_ids_by_dataset":{"other":["known"]}}, app, False, {"fit"})

    def test_explicit_empty_selection_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory); (app / "data").mkdir()
            (app / "data/items.jsonl").write_text(json.dumps({"item_id":"known"}) + "\n")
            with self.assertRaisesRegex(ValueError, "non-empty"):
                _load_items({"instruction":"x", "item_ids":[]}, app, False, None)

    def test_bad_item_outputs_do_not_stop_later_items(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory) / "app"; modules = Path(directory) / "modules"
            (app / "data").mkdir(parents=True); modules.mkdir()
            items = [{"item_id": value} for value in ("missing", "bad-usage", "good")]
            (app / "data/items.jsonl").write_text("".join(json.dumps(row)+"\n" for row in items))
            (modules / "fixture_worker.py").write_text(
                "import argparse,json,pathlib\n"
                "p=argparse.ArgumentParser();p.add_argument('--item-worker');a=p.parse_args();r=json.loads(pathlib.Path(a.item_worker).read_text());o=pathlib.Path(r['output']);o.mkdir(parents=True,exist_ok=True);i=r['item']['item_id']\n"
                "if i!='missing':(o/'final_answer.md').write_text('answer '+i)\n"
                "if i=='bad-usage':(o/'usage.json').write_text('{bad')\n"
            )
            old = os.environ.get("PYTHONPATH"); os.environ["PYTHONPATH"] = str(modules) + (os.pathsep + old if old else "")
            try: run_batch({"instruction":"x", "config":{}, "item_timeout_seconds":5}, "fixture_worker", app=app)
            finally:
                if old is None: os.environ.pop("PYTHONPATH",None)
                else: os.environ["PYTHONPATH"] = old
            rows = [json.loads(line) for line in (app / "submission/predictions.jsonl").read_text().splitlines()]
            self.assertEqual([row["status"] for row in rows], ["agent_error", "agent_error", "completed"])
            self.assertIn("final_answer.md", rows[0]["error"])
            self.assertIn("usage.json", rows[1]["error"])

    @unittest.skipIf(sys.platform == "win32", "process groups require POSIX")
    def test_terminate_cleans_descendants_after_leader_exits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); ready = root / "ready"; terminated = root / "terminated"
            child = "import pathlib,signal,time,sys; ready=pathlib.Path(sys.argv[1]); done=pathlib.Path(sys.argv[2]); signal.signal(signal.SIGTERM,lambda *_:(done.write_text('yes'),sys.exit(0))); ready.write_text('yes'); time.sleep(60)"
            leader = "import subprocess,sys,time,pathlib; subprocess.Popen([sys.executable,'-c',sys.argv[1],sys.argv[2],sys.argv[3]]); p=pathlib.Path(sys.argv[2]);\nwhile not p.exists(): time.sleep(.01)"
            process = subprocess.Popen([sys.executable,"-c",leader,child,str(ready),str(terminated)], start_new_session=True)
            process.wait(timeout=5)
            _terminate(process)
            deadline=time.monotonic()+3
            while time.monotonic()<deadline and not terminated.exists(): time.sleep(.02)
            self.assertTrue(terminated.exists(), "orphaned child did not receive termination")

if __name__ == "__main__": unittest.main()
