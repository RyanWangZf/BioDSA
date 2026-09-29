import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
path = ROOT / "benchmarks/biomedicine-deep-research/scoring/grade.py"
spec = importlib.util.spec_from_file_location("harbor_bdr_grade", path)
bdr = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bdr
spec.loader.exec_module(bdr)

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

if __name__ == "__main__": unittest.main()
