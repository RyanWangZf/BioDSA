from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import yaml

from bioagent_gym.backends import LocalBackend
from bioagent_gym.errors import HarnessError
from bioagent_gym.io import atomic_json
from bioagent_gym.runner import _validate_result, evaluate_run, run_experiment
from bioagent_gym.settings import cache_dir


ROOT = Path(__file__).resolve().parents[2]
INPUT_SCHEMA = ROOT / "benchmarks/fixture_qa/schemas/qa-output.schema.json"


class ProtocolTests(unittest.TestCase):
    def request(self) -> dict:
        return {"protocol_version":"1.0","run_id":"run","attempt_id":"attempt-0001","task_id":"task","task_type":"qa.multiple_choice.v1"}

    def test_invalid_result_and_artifact_escape_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            atomic_json(output / "result.json", {"status": "completed"})
            with self.assertRaises(HarnessError):
                _validate_result(output / "result.json", self.request(), output, INPUT_SCHEMA)
            outside = output.parent / f"outside-{output.name}.txt"; outside.write_text("secret", encoding="utf-8")
            atomic_json(output / "result.json", {**self.request(), "status":"completed", "output":{"selected_choice":"A"}, "artifacts":[{"path":f"../{outside.name}","type":"text/plain","description":"bad"}]})
            try:
                with self.assertRaises(HarnessError):
                    _validate_result(output / "result.json", self.request(), output, INPUT_SCHEMA)
            finally: outside.unlink()

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_artifact_symlink_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary); outside = output.parent / f"outside-{output.name}.txt"; outside.write_text("secret", encoding="utf-8")
            (output / "link.txt").symlink_to(outside)
            atomic_json(output / "result.json", {**self.request(), "status":"completed", "output":{"selected_choice":"A"}, "artifacts":[{"path":"link.txt","type":"text/plain","description":"bad"}]})
            try:
                with self.assertRaises(HarnessError): _validate_result(output/"result.json", self.request(), output, INPUT_SCHEMA)
            finally: outside.unlink()

    @unittest.skipUnless(hasattr(os, "killpg"), "process groups require POSIX")
    def test_timeout_kills_child_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); child_pid = root / "child.pid"
            script = root / "parent.py"
            script.write_text("import subprocess,sys,time,pathlib\np=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])\npathlib.Path(sys.argv[1]).write_text(str(p.pid))\ntime.sleep(60)\n", encoding="utf-8")
            backend = LocalBackend(); backend.start([sys.executable, str(script), str(child_pid)], root, {}, root/"stdout", root/"stderr")
            deadline = time.time() + 2
            while not child_pid.exists() and time.time() < deadline: time.sleep(0.01)
            outcome = backend.wait(0.05)
            self.assertTrue(outcome.timed_out)
            pid = int(child_pid.read_text())
            time.sleep(0.05)
            with self.assertRaises(ProcessLookupError): os.kill(pid, 0)


class EndToEndTests(unittest.TestCase):
    def test_fixture_run_keeps_reference_private_and_rescores(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); prepared = root / "prepared"; run = root / ".biodsa" / "legacy-run"
            subprocess.run([str(ROOT/"benchmarks/fixture_qa/prepare.py"), "--config", str(ROOT/"experiments/fixture-prepare.json"), "--output-dir", str(prepared)], check=True)
            config = root / "experiment.yaml"
            config.write_text(yaml.safe_dump({
                "protocol_version":"1.0", "agent":{"manifest":str(ROOT/"agents/fixture_agent/agent.yaml")},
                "benchmark":{"manifest":str(ROOT/"benchmarks/fixture_qa/benchmark.yaml"),"prepared":str(prepared),"split":"test"},
                "execution":{"backend":"local"}, "budget":{"wall_time_seconds":5}, "seed":7, "output":str(run),
            }), encoding="utf-8")
            run_experiment(config)
            summary = json.loads((run/"summary.json").read_text())
            self.assertEqual(summary["metrics"]["accuracy"], 1.0)
            request_text = (run/"tasks/arithmetic/attempt-0001/input/request.json").read_text()
            self.assertNotIn("reference", request_text)
            self.assertNotIn("private", request_text)
            result = run/"tasks/arithmetic/attempt-0001/output/result.json"
            before = result.stat().st_mtime_ns
            evaluate_run(run)
            self.assertEqual(before, result.stat().st_mtime_ns)

    def test_new_cache_name_and_explicit_override(self) -> None:
        previous = os.environ.pop("BIOAGENT_GYM_CACHE_DIR", None)
        try:
            self.assertEqual(cache_dir(), Path.home() / ".cache" / "bioagent-gym")
            os.environ["BIOAGENT_GYM_CACHE_DIR"] = "/tmp/explicit-gym-cache"
            self.assertEqual(cache_dir(), Path("/tmp/explicit-gym-cache"))
        finally:
            os.environ.pop("BIOAGENT_GYM_CACHE_DIR", None)
            if previous is not None:
                os.environ["BIOAGENT_GYM_CACHE_DIR"] = previous

    def test_minimal_distribution_has_no_agent_stack_dependency(self) -> None:
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
        self.assertIn('name = "bioagent-gym"', text)
        self.assertIn('bioagent-gym = "bioagent_gym.cli:main"', text)
        for dependency in ("langchain", "langgraph", "openai", "anthropic", "numpy", "pandas"):
            self.assertNotIn(dependency, text)


if __name__ == "__main__": unittest.main()
