import ast
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value

build=module("build_biodsbench_scoring",ROOT/"scripts/build_biodsbench_scoring.py")
runner=module("run_biodsbench_submission",ROOT/"scripts/run_biodsbench_submission.py")
bdr=module("harbor_bdr_grade",ROOT/"scripts/harbor_bdr_grade.py")
batch=module("bioagent_harbor_batch",ROOT/"agents/harbor_runtime/src/bioagent_harbor_runtime/batch.py")

class DeepEvidenceGraderTests(unittest.TestCase):
    def setUp(self):
        self.ref={"item_id":"one","subset":"fixture","source_split":"fit","task_type":"single_choice","valid_options":["A","B"],"label":{"selected_options":["A"]}}
        self.answer="<BIOMED_FINAL>{\"selected_options\":[\"A\"]}</BIOMED_FINAL>"

    def test_case_normalization_precedes_duplicate_check(self):
        with self.assertRaisesRegex(ValueError,"duplicate"):
            bdr.parse_answer('<BIOMED_FINAL>{"selected_options":["A","a"]}</BIOMED_FINAL>',{**self.ref,"task_type":"multi_select"})

    def test_duplicate_prediction_makes_reward_invalid(self):
        row={"item_id":"one","status":"completed","final_answer":self.answer}
        results,summary=bdr.grade({"one":self.ref},["one"],{"one":row},duplicates=["one"])
        self.assertEqual(results[0]["score"],1.0)
        self.assertIsNone(summary["accuracy"])
        self.assertEqual(summary["grading_error"],1)

    def test_unknown_prediction_makes_reward_invalid(self):
        row={"item_id":"one","status":"completed","final_answer":self.answer}
        _,summary=bdr.grade({"one":self.ref},["one"],{"one":row,"unknown":row})
        self.assertIsNone(summary["accuracy"])
        self.assertEqual(summary["unknown_prediction_ids"],["unknown"])

class BioDSBenchCompilerTests(unittest.TestCase):
    def compile(self,test):
        return build.compile_record({"unique_question_ids":"x","test_cases":test})

    def test_chained_comparison_stays_on_trusted_side(self):
        result=self.compile("assert 0 < value < 2")
        self.assertTrue(result["supported"])
        self.assertEqual(result["checks"][0]["kind"],"all")
        self.assertFalse(any(isinstance(ast.parse(x["expression"],mode="eval").body,ast.Compare) for x in result["observations"]))

    def test_membership_all_exports_values_not_boolean(self):
        result=self.compile("assert all(x in columns for x in required)")
        self.assertEqual(result["checks"][0]["kind"],"all_membership")
        self.assertEqual({x["expression"] for x in result["observations"]},{"required","columns"})

    def test_unknown_statement_and_empty_test_are_blocked(self):
        self.assertFalse(self.compile("if flag:\n    value = 1\n")["supported"])
        self.assertFalse(self.compile("value = 1\n")["supported"])

    def test_finite_evaluator_preserves_short_circuit_and_chains(self):
        self.assertTrue(runner.evaluate(ast.parse("0 < x < 2",mode="eval"),{"x":1}))
        self.assertFalse(runner.evaluate(ast.parse("False and missing",mode="eval"),{}))
        self.assertTrue(runner.evaluate(ast.parse("True or missing",mode="eval"),{}))

    def test_all_pinned_assertions_compile_without_boolean_observations(self):
        refs=ROOT/"benchmarks/biodsbench/tasks/biodsbench-python/tests/references/references.jsonl"
        if not refs.is_file():self.skipTest("prepare_harbor_dataset_tasks.py has not materialized verifier references")
        for ref in map(json.loads,refs.read_text().splitlines()):
            scoring=ref["scoring"];self.assertTrue(scoring["supported"],ref["item_id"]);self.assertTrue(scoring["checks"],ref["item_id"])
            for observation in scoring["observations"]:
                node=ast.parse(observation["expression"],mode="eval").body
                self.assertNotIsInstance(node,(ast.BoolOp,ast.Compare),ref["item_id"])

class BatchRuntimeTests(unittest.TestCase):
    def test_per_dataset_selection_is_strict(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            app=Path(directory);(app/"data").mkdir();(app/"data/items.jsonl").write_text(json.dumps({"item_id":"known","source_split":"fit"})+"\n");(app/"data/manifest.json").write_text(json.dumps({"subset":"fixture"}))
            request={"instruction":"x","split":"fit","item_ids_by_dataset":{"fixture":["missing"]}}
            with self.assertRaisesRegex(ValueError,"unknown item_ids"):
                batch._load_items(request,app,False,{"fit"})
            with self.assertRaisesRegex(ValueError,"no selection"):
                batch._load_items({"instruction":"x","split":"fit","item_ids_by_dataset":{"other":["known"]}},app,False,{"fit"})

if __name__=="__main__":unittest.main()
