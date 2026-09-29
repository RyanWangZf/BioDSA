import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
path = ROOT / "benchmarks/biomedicine-deep-research/scoring/grade.py"
spec = importlib.util.spec_from_file_location("harbor_bdr_grade", path)
bdr = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bdr
spec.loader.exec_module(bdr)

summary_path = ROOT / "benchmarks/biomedicine-deep-research/summarize.py"
summary_spec = importlib.util.spec_from_file_location("bdr_summarize", summary_path)
bdr_summary = importlib.util.module_from_spec(summary_spec)
sys.modules[summary_spec.name] = bdr_summary
summary_spec.loader.exec_module(bdr_summary)

class DeepEvidenceGraderTests(unittest.TestCase):
    def setUp(self):
        self.ref = {"item_id":"one", "subset":"fixture", "source_split":"fit", "task_type":"single_choice", "valid_options":["A","B"], "label":{"selected_options":["A"]}}
        self.answer = '<BIOMED_FINAL>{"selected_options":["A"]}</BIOMED_FINAL>'

    def test_case_normalization_precedes_duplicate_check(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            bdr.parse_answer('<BIOMED_FINAL>{"selected_options":["A","a"]}</BIOMED_FINAL>', {**self.ref, "task_type":"multi_select"})

    def test_duplicate_prediction_makes_reward_invalid(self):
        row = {"item_id":"one", "status":"completed", "final_answer":self.answer}
        results, summary = bdr.grade({"one":self.ref}, ["one"], {"one":row}, duplicates=["one"])
        self.assertEqual(results[0]["score"], 1.0)
        self.assertIsNone(summary["accuracy"])
        self.assertEqual(summary["grading_error"], 1)

    def test_unknown_prediction_makes_reward_invalid(self):
        row = {"item_id":"one", "status":"completed", "final_answer":self.answer}
        _, summary = bdr.grade({"one":self.ref}, ["one"], {"one":row, "unknown":row})
        self.assertIsNone(summary["accuracy"])
        self.assertEqual(summary["unknown_prediction_ids"], ["unknown"])

class LeaderboardSummaryTests(unittest.TestCase):
    def make_job(self, root: Path):
        tasks = [{"path": f"benchmarks/biomedicine-deep-research/tasks/{name}"} for name in sorted(bdr_summary.FORMAL_SUBSETS)]
        (root / "config.json").write_text(json.dumps({"job_name":"formal", "tasks":tasks, "verifier":{"env":{"BIOAGENT_SPLIT":"verifier"}}}))
        for subset in sorted(bdr_summary.FORMAL_SUBSETS):
            trial = root / f"{subset}__trial"; (trial / "verifier").mkdir(parents=True)
            config = {"task":{"path":f"benchmarks/biomedicine-deep-research/tasks/{subset}"}, "agent":{"import_path":"fixture:Agent", "model_name":"model"}}
            (trial / "config.json").write_text(json.dumps(config)); (trial / "result.json").write_text(json.dumps({"exception_info":None}))
            expected = bdr_summary._expected(subset)
            rows = [{"item_id":item_id, "subset":subset, "split":"verifier", "status":"scored", "score":1.0} for item_id in sorted(expected)]
            (trial / "verifier/per_item_results.jsonl").write_text("".join(json.dumps(row)+"\n" for row in rows))
            summary = {"selection_split":"verifier", "expected_total":len(expected), "grading_error":0, "unscorable":0, "accuracy":1.0}
            (trial / "verifier/summary.json").write_text(json.dumps(summary))

    def test_complete_job_has_one_micro_score(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_job(root); result=bdr_summary.summarize(root)
            self.assertTrue(result["valid"]); self.assertEqual(len(result["evaluations"]),1)
            self.assertEqual(result["evaluations"][0]["micro_accuracy"],1.0)
            self.assertEqual(result["evaluations"][0]["expected_total"],127)

    def test_missing_trial_invalidates_whole_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_job(root)
            import shutil
            shutil.rmtree(next(root.glob("hle-biomedicine__*")))
            result=bdr_summary.summarize(root)
            self.assertFalse(result["valid"]); self.assertIsNone(result["evaluations"][0]["micro_accuracy"])

    def test_grading_error_invalidates_whole_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_job(root); trial=next(root.glob("hle-medicine__*")); path=trial/"verifier/summary.json"; summary=json.loads(path.read_text()); summary["grading_error"]=1; summary["accuracy"]=None; path.write_text(json.dumps(summary))
            result=bdr_summary.summarize(root)
            self.assertFalse(result["valid"]); self.assertIsNone(result["evaluations"][0]["micro_accuracy"])

if __name__ == "__main__": unittest.main()
