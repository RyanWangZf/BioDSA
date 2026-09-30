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

    def test_evidence_gap_uses_recall_at_30(self):
        ref = {"item_id":"gap", "subset":"evidence-gap-discovery", "source_split":"verifier", "task_type":"evidence_gap_retrieval", "valid_options":[], "label":{"proposed_pmids":["11","22","33","44"]}}
        answer = '<BIOMED_FINAL>{"proposed_pmids":["33","999","11"]}</BIOMED_FINAL>'
        results, summary = bdr.grade({"gap":ref}, ["gap"], {"gap":{"item_id":"gap","status":"completed","final_answer":answer}})
        self.assertEqual(results[0]["metric"], "recall@30")
        self.assertEqual(results[0]["hits"], 2)
        self.assertEqual(results[0]["score"], .5)
        self.assertEqual(results[0]["max_recall_at_30"],1.0)
        self.assertEqual(summary["primary_metric"], "mean_recall@30")
        self.assertEqual(summary["primary_score"], .5)
        self.assertEqual(summary["mean_recall_at_30"], .5)
        self.assertNotIn("accuracy", summary)

    def test_evidence_gap_rejects_invalid_ranked_lists(self):
        ref = {"task_type":"evidence_gap_retrieval"}
        invalid = (
            ["12", "12"],
            ["PMID:12"],
            [str(value) for value in range(1, 32)],
        )
        for values in invalid:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    bdr.parse_answer(f'<BIOMED_FINAL>{json.dumps({"proposed_pmids":values})}</BIOMED_FINAL>', ref)

    def test_all_evidence_gap_oracles_have_valid_pmids(self):
        path = ROOT / "benchmarks/biomedicine-deep-research/tasks/evidence-gap-discovery/tests/references/references.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual(len(rows), 20)
        for ref in rows:
            answer = '<BIOMED_FINAL>' + json.dumps({"proposed_pmids":ref["label"]["proposed_pmids"][:30]}) + '</BIOMED_FINAL>'
            parsed = bdr.parse_answer(answer, ref)
            expected = set(ref["label"]["proposed_pmids"])
            self.assertEqual(len(set(parsed) & expected) / len(expected), min(30, len(expected)) / len(expected))
        long_ref=next(ref for ref in rows if len(ref["label"]["proposed_pmids"])>30);values=long_ref["label"]["proposed_pmids"][:30];answer='<BIOMED_FINAL>'+json.dumps({"proposed_pmids":values})+'</BIOMED_FINAL>';result,summary=bdr.grade({long_ref["item_id"]:long_ref},[long_ref["item_id"]],{long_ref["item_id"]:{"status":"completed","final_answer":answer}})
        self.assertLess(result[0]["max_recall_at_30"],1.0);self.assertEqual(result[0]["score"],result[0]["max_recall_at_30"]);self.assertEqual(summary["mean_max_recall_at_30"],result[0]["max_recall_at_30"])

class LeaderboardSummaryTests(unittest.TestCase):
    def make_job(self, root: Path):
        tasks = [{"path": f"benchmarks/biomedicine-deep-research/tasks/{name}"} for name in sorted(bdr_summary.FORMAL_SUBSETS)]
        agent={"import_path":"fixture:Agent", "model_name":"model", "kwargs":{"provider":"mock","tool_call_budget":4}}
        (root / "config.json").write_text(json.dumps({"job_name":"formal", "tasks":tasks, "agents":[agent], "verifier":{"env":{"BIOAGENT_SPLIT":"verifier"}}}))
        for subset in sorted(bdr_summary.FORMAL_SUBSETS):
            trial = root / f"{subset}__trial"; (trial / "verifier").mkdir(parents=True)
            config = {"task":{"path":f"benchmarks/biomedicine-deep-research/tasks/{subset}"}, "agent":agent}
            (trial / "config.json").write_text(json.dumps(config)); (trial / "result.json").write_text(json.dumps({"exception_info":None}))
            expected = bdr_summary._expected(subset)
            retrieval=subset=="evidence-gap-discovery";task_type="evidence_gap_retrieval" if retrieval else bdr_summary._expected_rows(subset)[next(iter(expected))]["task_type"]
            rows = [{"item_id":item_id, "subset":subset, "split":"verifier", "task_type":task_type,"status":"scored", "score":1.0,"metric":"recall@30" if retrieval else "exact_match"} for item_id in sorted(expected)]
            (trial / "verifier/per_item_results.jsonl").write_text("".join(json.dumps(row)+"\n" for row in rows))
            summary = {"selection_split":"verifier", "expected_total":len(expected),"attempted":len(expected),"validly_evaluated":len(expected), "missing":0,"agent_timeout":0,"agent_error":0,"grading_error":0, "unscorable":0, "primary_metric":"mean_recall@30" if retrieval else "accuracy","primary_score":1.0}
            (trial / "verifier/summary.json").write_text(json.dumps(summary))

    def test_complete_job_has_one_micro_score(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_job(root); result=bdr_summary.summarize(root)
            self.assertTrue(result["valid"]); self.assertEqual(len(result["evaluations"]),1)
            self.assertEqual(result["evaluations"][0]["overall_mean_item_score"],1.0)
            self.assertEqual(result["evaluations"][0]["choice_micro_accuracy"],1.0)
            self.assertEqual(result["evaluations"][0]["evidence_gap_mean_recall_at_30"],1.0)
            self.assertEqual(result["evaluations"][0]["expected_total"],131)

    def test_missing_trial_invalidates_whole_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_job(root)
            import shutil
            shutil.rmtree(next(root.glob("hle-biomedicine__*")))
            result=bdr_summary.summarize(root)
            self.assertFalse(result["valid"]); self.assertIsNone(result["evaluations"][0]["overall_mean_item_score"])

    def test_grading_error_invalidates_whole_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.make_job(root); trial=next(root.glob("hle-medicine__*")); path=trial/"verifier/summary.json"; summary=json.loads(path.read_text()); summary["grading_error"]=1; summary["primary_score"]=None; path.write_text(json.dumps(summary))
            result=bdr_summary.summarize(root)
            self.assertFalse(result["valid"]); self.assertIsNone(result["evaluations"][0]["overall_mean_item_score"])

    def test_configured_agent_without_trials_invalidates_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.make_job(root);config=json.loads((root/"config.json").read_text());config["agents"].append({"import_path":"other:Agent","model_name":"other","kwargs":{"provider":"mock"}});(root/"config.json").write_text(json.dumps(config))
            result=bdr_summary.summarize(root)
            self.assertFalse(result["valid"]);self.assertEqual(len(result["evaluations"]),2)
            self.assertTrue(any("missing trials" in error for error in result["evaluations"][1]["errors"]))

    def test_mixed_agent_config_and_invalid_rows_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.make_job(root);trial=next(root.glob("hle-medicine__*"));config=json.loads((trial/"config.json").read_text());config["agent"]["kwargs"]["tool_call_budget"]=99;(trial/"config.json").write_text(json.dumps(config))
            result=bdr_summary.summarize(root);self.assertFalse(result["valid"]);self.assertTrue(any("not present in job config" in error for error in result["errors"]))
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.make_job(root);trial=next(root.glob("hle-medicine__*"));path=trial/"verifier/per_item_results.jsonl";rows=[json.loads(line) for line in path.read_text().splitlines()];rows[0]["score"]=float("nan");path.write_text("".join(json.dumps(row)+"\n" for row in rows));result=bdr_summary.summarize(root);self.assertFalse(result["valid"]);self.assertTrue(any("finite" in error for error in result["evaluations"][0]["errors"]))

    def test_corrupt_result_is_reported_as_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.make_job(root);trial=next(root.glob("hle-medicine__*"));(trial/"verifier/summary.json").write_text("not json")
            result=bdr_summary.summarize(root);self.assertFalse(result["valid"]);self.assertTrue(any("invalid result artifact" in error for error in result["evaluations"][0]["errors"]))

    def test_row_semantics_and_summary_consistency_are_enforced(self):
        mutations=(
            lambda row:row.update(score=.5),
            lambda row:row.update(subset="wrong"),
            lambda row:row.update(status="agent_error",score=1.0),
            lambda row:row.update(task_type="evidence_gap_retrieval"),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);self.make_job(root);trial=next(root.glob("hle-medicine__*"));path=trial/"verifier/per_item_results.jsonl";rows=[json.loads(line) for line in path.read_text().splitlines()];mutate(rows[0]);path.write_text("".join(json.dumps(row)+"\n" for row in rows));result=bdr_summary.summarize(root);self.assertFalse(result["valid"])
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.make_job(root);trial=next(root.glob("hle-medicine__*"));path=trial/"verifier/summary.json";summary=json.loads(path.read_text());summary["primary_score"]=.25;path.write_text(json.dumps(summary));result=bdr_summary.summarize(root);self.assertFalse(result["valid"]);self.assertTrue(any("differs from per-item" in error for error in result["evaluations"][0]["errors"]))

    def test_malformed_model_answer_is_valid_zero_not_infrastructure_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.make_job(root);trial=next(root.glob("hle-medicine__*"));rows_path=trial/"verifier/per_item_results.jsonl";rows=[json.loads(line) for line in rows_path.read_text().splitlines()];item_id=rows[0]["item_id"]
            refs={row["item_id"]:row for row in map(json.loads,(ROOT/"benchmarks/biomedicine-deep-research/tasks/hle-medicine/tests/references/references.jsonl").read_text().splitlines())};ref=refs[item_id]
            graded,graded_summary=bdr.grade({item_id:ref},[item_id],{item_id:{"status":"completed","final_answer":"not a valid final answer"}})
            self.assertEqual(graded[0]["status"],"scored");self.assertEqual(graded[0]["score"],0.0);self.assertEqual(graded[0]["metric"],"exact_match");self.assertEqual(graded_summary["grading_error"],0)
            rows[0]=graded[0];rows_path.write_text("".join(json.dumps(row)+"\n" for row in rows));summary_path=trial/"verifier/summary.json";summary=json.loads(summary_path.read_text());summary["primary_score"]=(len(rows)-1)/len(rows);summary_path.write_text(json.dumps(summary))
            result=bdr_summary.summarize(root);self.assertTrue(result["valid"],result)

if __name__ == "__main__": unittest.main()
