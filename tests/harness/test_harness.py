from __future__ import annotations

import json
import os
import subprocess
import shutil
import sys
import tempfile
import time
import unittest
from unittest import mock
from pathlib import Path

import yaml

from bioagent_gym.backends import LocalBackend
from bioagent_gym.errors import HarnessError
from bioagent_gym.io import atomic_json
from bioagent_gym.config import resolve_experiment, validate_prepared
from bioagent_gym.runner import _validate_result, evaluate_run, run_experiment
from bioagent_gym.settings import cache_dir


ROOT = Path(__file__).resolve().parents[2]
INPUT_SCHEMA = ROOT / "benchmarks/fixture_qa/schemas/qa-output.schema.json"


class ProtocolTests(unittest.TestCase):
    def wait_pid_gone(self, pid: int, timeout: float = 3) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            time.sleep(0.01)
        self.fail(f"process {pid} still exists after cleanup deadline")

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
            self.wait_pid_gone(pid)

    @unittest.skipUnless(hasattr(os, "killpg"), "process groups require POSIX")
    def test_cancel_kills_agent_and_child_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); child_pid = root / "child.pid"; script = root / "parent.py"
            script.write_text("import subprocess,sys,time,pathlib\np=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])\npathlib.Path(sys.argv[1]).write_text(str(p.pid))\ntime.sleep(60)\n", encoding="utf-8")
            backend = LocalBackend(); backend.start([sys.executable, str(script), str(child_pid)], root, {}, root/"stdout", root/"stderr")
            deadline = time.monotonic() + 2
            while not child_pid.exists() and time.monotonic() < deadline: time.sleep(0.01)
            self.assertTrue(child_pid.exists()); parent = backend.process.pid; child = int(child_pid.read_text()); backend.cancel()
            self.wait_pid_gone(parent); self.wait_pid_gone(child)


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
            summary = evaluate_run(run)
            self.assertEqual(summary["metrics"]["accuracy"]["value"], 1.0)
            request_text = (run/"tasks/arithmetic/attempt-0001/input/request.json").read_text()
            self.assertNotIn("reference", request_text)
            self.assertNotIn("private", request_text)
            result = run/"tasks/arithmetic/attempt-0001/output/result.json"
            before = result.stat().st_mtime_ns
            evaluate_run(run)
            self.assertEqual(before, result.stat().st_mtime_ns)
            self.assertEqual(len(list((run/"evaluations").iterdir())), 3)
            self.assertTrue((run/"context/tasks.json").is_file())
            workspaces = [run/"tasks"/task/"attempt-0001/workspace" for task in ("arithmetic", "biology")]
            self.assertNotEqual(*(path.read_text() for path in [workspaces[0]/"workspace-marker.txt", workspaces[1]/"workspace-marker.txt"]))
            self.assertFalse((workspaces[1]/"arithmetic.tmp").exists())

    def test_task_snapshot_wins_and_legacy_run_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); prepared, config, _ = self._prepared_and_config(root); run_experiment(config)
            (prepared/"tasks.jsonl").write_text("{\"changed\": true}\n", encoding="utf-8")
            summary = evaluate_run(root/"run"); self.assertEqual(summary["metrics"]["accuracy"]["value"], 1.0)
            shutil.rmtree(root/"run/context")
            # Restore a readable external task list for the deliberately legacy path.
            subprocess.run([str(ROOT/"benchmarks/fixture_qa/prepare.py"), "--config", str(ROOT/"experiments/fixture-prepare.json"), "--output-dir", str(root/"replacement")], check=True)
            shutil.copy2(root/"replacement/tasks.jsonl", prepared/"tasks.jsonl")
            with self.assertWarns(RuntimeWarning): legacy = evaluate_run(root/"run")
            self.assertTrue(legacy["legacy_context"])

    def _prepared_and_config(self, root: Path, **changes):
        prepared = root / "prepared"
        subprocess.run([str(ROOT/"benchmarks/fixture_qa/prepare.py"), "--config", str(ROOT/"experiments/fixture-prepare.json"), "--output-dir", str(prepared)], check=True)
        value = {"protocol_version":"1.0", "agent":{"manifest":str(ROOT/"agents/fixture_agent/agent.yaml")}, "benchmark":{"manifest":str(ROOT/"benchmarks/fixture_qa/benchmark.yaml"),"prepared":str(prepared),"split":"test","data_revision":"fixture-r1"}, "execution":{"backend":"local"}, "budget":{"wall_time_seconds":5}, "output":str(root/"run")}
        for key, item in changes.items(): value[key] = item
        config = root / "experiment.yaml"; config.write_text(yaml.safe_dump(value), encoding="utf-8")
        return prepared, config, value

    def test_split_revision_and_unknown_fields_fail_before_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); _, config, value = self._prepared_and_config(root)
            value["benchmark"]["split"] = "missing"; config.write_text(yaml.safe_dump(value), encoding="utf-8")
            with self.assertRaisesRegex(HarnessError, "does not contain split|prepared dataset split"):
                validate_prepared(resolve_experiment(config))
            value["benchmark"]["split"] = "test"; value["benchmark"]["data_revision"] = "wrong"; config.write_text(yaml.safe_dump(value), encoding="utf-8")
            with self.assertRaisesRegex(HarnessError, "data_revision"):
                validate_prepared(resolve_experiment(config))
            value["benchmark"]["data_revision"] = "fixture-r1"; value["budegt"] = {}; config.write_text(yaml.safe_dump(value), encoding="utf-8")
            with self.assertRaisesRegex(HarnessError, "budegt"):
                resolve_experiment(config)

    def test_agent_failure_and_evaluator_failure_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); _, config, value = self._prepared_and_config(root)
            agent_config = root/"agent.json"; agent_config.write_text(json.dumps({"fail_task_id":"arithmetic"}), encoding="utf-8"); value["agent"]["config"] = str(agent_config); config.write_text(yaml.safe_dump(value), encoding="utf-8")
            run_experiment(config); latest = json.loads((root/"run/latest-evaluation.json").read_text()); summary = json.loads((root/"run"/latest["summary"]).read_text())
            self.assertEqual(json.loads((root/"run/context/agent-config.json").read_text()), {"fail_task_id":"arithmetic"})
            self.assertEqual(summary["total_tasks"], 2); self.assertEqual(summary["execution_status_counts"]["failed"], 1)
            self.assertEqual(summary["metrics"]["accuracy"]["denominator_count"], 1); self.assertEqual(summary["metrics"]["accuracy"]["coverage"], .5)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); _, config, value = self._prepared_and_config(root); value["benchmark"]["scoring"] = {"fail_task_id":"biology"}; config.write_text(yaml.safe_dump(value), encoding="utf-8")
            run_experiment(config); latest = json.loads((root/"run/latest-evaluation.json").read_text()); summary = json.loads((root/"run"/latest["summary"]).read_text())
            self.assertEqual(summary["evaluation_status_counts"], {"failed":1, "scored":1}); self.assertEqual(summary["metrics"]["accuracy"]["valid_scores"], 1)

    def test_unsupported_budget_requires_explicit_best_effort(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); _, config, value = self._prepared_and_config(root); value["budget"]["tokens"] = 10; config.write_text(yaml.safe_dump(value), encoding="utf-8")
            with self.assertRaisesRegex(HarnessError, "unsupported"): run_experiment(config, evaluate_after=False)
            value["budget_policy"] = "best_effort"; config.write_text(yaml.safe_dump(value), encoding="utf-8"); run_experiment(config, evaluate_after=False)
            record = json.loads((root/"run/run-record.json").read_text()); self.assertEqual(record["budget_enforcement"]["tokens"], "unsupported")

    def test_runner_cancellation_records_state_and_stops_scheduling(self) -> None:
        class InterruptedBackend:
            def start(self, *args): pass
            def wait(self, timeout): raise KeyboardInterrupt
            def cancel(self): pass
            def cleanup(self): pass
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); _, config, _ = self._prepared_and_config(root)
            with mock.patch("bioagent_gym.runner._agent_command", return_value=(InterruptedBackend(), ["unused"])):
                with self.assertRaises(KeyboardInterrupt): run_experiment(config, evaluate_after=False)
            record = json.loads((root/"run/run-record.json").read_text())
            self.assertEqual(record["status"], "cancelled"); self.assertEqual(len(record["tasks"]), 1)
            self.assertEqual(record["tasks"][0]["status"], "cancelled")

    def test_rescore_version_change_requires_explicit_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); prepared, config, _ = self._prepared_and_config(root); run_experiment(config)
            manifest = json.loads((prepared/"manifest.json").read_text()); manifest["data_revision"] = "fixture-r2"; (prepared/"manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(HarnessError, "version mismatch"): evaluate_run(root/"run")
            summary = evaluate_run(root/"run", allow_version_change=True)
            record = json.loads((root/"run/evaluations"/summary["evaluation_id"]/"evaluation-record.json").read_text())
            self.assertTrue(record["version_override"])

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
