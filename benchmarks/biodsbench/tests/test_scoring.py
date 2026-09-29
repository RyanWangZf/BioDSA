import ast
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value

build=module("build_biodsbench_scoring",ROOT/"benchmarks/biodsbench/scoring/compile_assertions.py")
runner=module("run_biodsbench_submission",ROOT/"benchmarks/biodsbench/scoring/run_submission.py")

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
        if not refs.is_file():self.skipTest("benchmarks/biodsbench/prepare.py has not materialized verifier references")
        for ref in map(json.loads,refs.read_text().splitlines()):
            scoring=ref["scoring"];self.assertTrue(scoring["supported"],ref["item_id"]);self.assertTrue(scoring["checks"],ref["item_id"])
            for observation in scoring["observations"]:
                node=ast.parse(observation["expression"],mode="eval").body
                self.assertNotIsInstance(node,(ast.BoolOp,ast.Compare),ref["item_id"])

if __name__=="__main__":unittest.main()
