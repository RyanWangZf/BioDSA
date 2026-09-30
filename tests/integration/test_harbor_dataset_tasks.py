import json
import importlib.util
import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUPPORTED_AGENTS = (
    "coder", "dswizard", "deepevidence", "react", "trialmind_slr",
    "virtuallab", "geneagent", "trialgpt", "agentmd", "informgen",
)
MIGRATED_FIXTURE_AGENTS = (
    "react", "trialmind_slr", "virtuallab", "geneagent", "trialgpt",
    "agentmd", "informgen",
)


class DatasetTaskInventoryTests(unittest.TestCase):
    def test_agent_packages_depend_on_separate_runner(self):
        for name in SUPPORTED_AGENTS:
            config = tomllib.loads((ROOT / f"agents/{name}/pyproject.toml").read_text())
            self.assertEqual(config["tool"]["setuptools"]["packages"]["find"]["where"], ["src"])
            self.assertIn("bioagent-harbor-runtime==0.1.0", config["project"]["dependencies"])
            migration = (ROOT / f"agents/{name}/MIGRATION.md").read_text()
            self.assertIn("Behavior map", migration)
            self.assertNotIn("reference_repo", "\n".join(
                path.read_text(errors="ignore")
                for path in (ROOT / f"agents/{name}/src").rglob("*.py")
            ))

    def test_migrated_agents_have_native_behavior_fixtures(self):
        for name in MIGRATED_FIXTURE_AGENTS:
            task = ROOT / f"tests/fixtures/tasks/{name}-workflow"
            job = ROOT / f"tests/fixtures/jobs/{name}.yaml"
            self.assertTrue((task / "data/items.jsonl").is_file(), name)
            self.assertTrue((task / "environment/Dockerfile").is_file(), name)
            self.assertTrue((task / "tests/test.sh").is_file(), name)
            text = job.read_text()
            self.assertIn(f"tests/fixtures/tasks/{name}-workflow", text)
            self.assertIn(f"bioagent_{name}.harbor_agent", text)

    def test_migrated_runtime_sources_do_not_import_legacy_or_other_agents(self):
        for name in MIGRATED_FIXTURE_AGENTS:
            source = "\n".join(
                path.read_text(errors="ignore")
                for path in (ROOT / f"agents/{name}/src").rglob("*.py")
            )
            self.assertNotRegex(source, r"(?m)^(?:from|import)\s+(?:legacy|biodsa)\b", name)
            for other in MIGRATED_FIXTURE_AGENTS:
                if other != name:
                    self.assertNotIn(f"bioagent_{other}", source, name)

    def _items(self, root):
        found = {}
        for path in sorted(root.glob("*/data/items.jsonl")):
            rows = [json.loads(line) for line in path.read_text().splitlines() if line]
            self.assertEqual(len(rows), len({row["item_id"] for row in rows}), path)
            for row in rows:
                self.assertNotIn("label", row, path)
                self.assertNotIn("reference_answer", row, path)
            found[path.parent.parent.name] = rows
        return found

    def test_complete_source_inventory(self):
        bio = self._items(ROOT / "benchmarks/biodsbench/tasks")
        self.assertEqual({name: len(rows) for name, rows in bio.items()}, {"biodsbench-python": 118, "biodsbench-r": 165})
        deep = self._items(ROOT / "benchmarks/biomedicine-deep-research/tasks")
        self.assertEqual(len(deep), 13)
        self.assertEqual(sum(map(len, deep.values())), 648)
        self.assertEqual(len({row["item_id"] for rows in deep.values() for row in rows}), 648)

    def test_jobs_have_deliberate_dataset_scope(self):
        def paths(path):
            return {Path(line.split(":", 1)[1].strip()).name for line in path.read_text().splitlines() if line.strip().startswith("- path:")}
        bio_paths = paths(ROOT / "benchmarks/biodsbench/jobs/dswizard.yaml")
        self.assertEqual(bio_paths, {"biodsbench-python"})
        formal = paths(ROOT / "benchmarks/biomedicine-deep-research/jobs/deepevidence.yaml")
        self.assertIn("evidence-gap-discovery", formal)
        self.assertEqual(formal, {p.name for p in (ROOT / "benchmarks/biomedicine-deep-research/tasks").iterdir() if p.is_dir()})

    def test_formal_job_directories_only_contain_ranked_entrypoints(self):
        self.assertEqual(
            {path.name for path in (ROOT / "benchmarks/biodsbench/jobs").glob("*.yaml")},
            {"dswizard.yaml"},
        )
        self.assertEqual(
            {path.name for path in (ROOT / "benchmarks/biomedicine-deep-research/jobs").glob("*.yaml")},
            {"deepevidence.yaml"},
        )

    def test_prepare_scripts_do_not_generate_static_definitions(self):
        for path in (ROOT / "benchmarks/biodsbench/prepare.py", ROOT / "benchmarks/biomedicine-deep-research/prepare.py"):
            text = path.read_text()
            self.assertNotIn('write_text(INSTRUCTION', text)
            self.assertNotIn('write_text(TOML', text)
            self.assertNotIn('write_text(ENV', text)

    def test_smoke_selection_is_shared_with_verifier(self):
        for path in (ROOT / "benchmarks/biodsbench/tests/jobs/dswizard-mock.yaml", ROOT / "benchmarks/biomedicine-deep-research/tests/jobs/deepevidence-mock.yaml"):
            text = path.read_text()
            match = re.search(r'BIOAGENT_ITEM_IDS:\s*"([^"]+)"', text)
            self.assertIsNotNone(match)
            verifier = match.group(1)
            for item_id in verifier.split(","):
                self.assertIn(f'"{item_id}"', text)

    def test_live_smokes_use_fixed_comparable_scopes(self):
        bio_jobs=ROOT/"benchmarks/biodsbench/tests/jobs";coder=(bio_jobs/"coder-live.yaml").read_text();wizard=(bio_jobs/"dswizard-live.yaml").read_text();expected="28481359_0,29713087_1"
        self.assertIn(f'BIOAGENT_ITEM_IDS: "{expected}"',coder);self.assertIn(f'BIOAGENT_ITEM_IDS: "{expected}"',wizard)
        deep=(ROOT/"benchmarks/biomedicine-deep-research/tests/jobs/deepevidence-live.yaml").read_text()
        for subset in ("hle-biomedicine","moa-pathway-reasoning","evidence-gap-discovery"):
            match=re.search(rf'{subset}: \[(.*?)\]',deep);self.assertIsNotNone(match);self.assertEqual(match.group(1).count('"')//2,2)

    def test_deep_research_split_inventory_is_disjoint(self):
        deep = self._items(ROOT / "benchmarks/biomedicine-deep-research/tasks")
        by_split = {name: set() for name in ("fit", "tune", "verifier")}
        by_type = {}
        for rows in deep.values():
            for row in rows:
                by_split[row["source_split"]].add(row["item_id"])
                by_type[row["task_type"]] = by_type.get(row["task_type"], 0) + 1
        self.assertEqual({key: len(value) for key, value in by_split.items()}, {"fit": 388, "tune": 129, "verifier": 131})
        self.assertFalse(by_split["fit"] & by_split["tune"])
        self.assertFalse(by_split["fit"] & by_split["verifier"])
        self.assertFalse(by_split["tune"] & by_split["verifier"])
        self.assertEqual(by_type, {"single_choice": 367, "multi_select": 261, "evidence_gap_retrieval": 20})

    def test_formal_split_is_propagated_to_agent_and_verifier(self):
        text = (ROOT / "benchmarks/biomedicine-deep-research/jobs/deepevidence.yaml").read_text()
        self.assertIn('BIOAGENT_SPLIT: "verifier"', text)
        self.assertIn("split: verifier", text)

    def test_biodsbench_python_mapping_covers_every_item(self):
        manifest = json.loads((ROOT / "benchmarks/biodsbench/tasks/biodsbench-python/data/manifest.json").read_text())
        stats = manifest["splits"]["benchmark"]
        self.assertEqual(stats["source_count"], 118)
        self.assertEqual(stats["scorable_count"], 118)
        self.assertEqual(stats["oracle_verified"], 112)
        self.assertEqual(len(manifest["oracle_failures"]), 6)

    def test_deep_oracle_caps_retrieval_submissions_at_30(self):
        spec=importlib.util.spec_from_file_location("prepare_grader_oracles",ROOT/"tests/integration/prepare_grader_oracles.py");module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory);module.deep(output)
            path=output/"evidence-gap-discovery/submission/predictions.jsonl";rows=[json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(len(rows),20)
            for row in rows:
                payload=json.loads(row["final_answer"].split("<BIOMED_FINAL>",1)[1].split("</BIOMED_FINAL>",1)[0])
                self.assertLessEqual(len(payload["proposed_pmids"]),30)


if __name__ == "__main__":
    unittest.main()
