import json
import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class DatasetTaskInventoryTests(unittest.TestCase):
    def test_agent_packages_depend_on_separate_runner(self):
        for name in ("coder", "dswizard", "deepevidence"):
            config = tomllib.loads((ROOT / f"agents/{name}/pyproject.toml").read_text())
            self.assertEqual(config["tool"]["setuptools"]["packages"]["find"]["where"], ["src"])
            self.assertIn("bioagent-harbor-runtime==0.1.0", config["project"]["dependencies"])

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
        deep_paths = paths(ROOT / "benchmarks/biomedicine-deep-research/jobs/deepevidence-diagnostic.yaml")
        self.assertEqual(bio_paths, {"biodsbench-python"})
        self.assertEqual(deep_paths, {p.name for p in (ROOT / "benchmarks/biomedicine-deep-research/tasks").iterdir() if p.is_dir()})
        formal = paths(ROOT / "benchmarks/biomedicine-deep-research/jobs/deepevidence.yaml")
        self.assertNotIn("evidence-gap-discovery", formal)
        self.assertEqual(len(formal), 12)

    def test_prepare_scripts_do_not_generate_static_definitions(self):
        for path in (ROOT / "benchmarks/biodsbench/prepare.py", ROOT / "benchmarks/biomedicine-deep-research/prepare.py"):
            text = path.read_text()
            self.assertNotIn('write_text(INSTRUCTION', text)
            self.assertNotIn('write_text(TOML', text)
            self.assertNotIn('write_text(ENV', text)

    def test_smoke_selection_is_shared_with_verifier(self):
        for path in (ROOT / "benchmarks/biodsbench/jobs/dswizard-smoke.yaml", ROOT / "benchmarks/biomedicine-deep-research/jobs/deepevidence-smoke.yaml"):
            text = path.read_text()
            match = re.search(r'BIOAGENT_ITEM_IDS:\s*"([^"]+)"', text)
            self.assertIsNotNone(match)
            verifier = match.group(1)
            for item_id in verifier.split(","):
                self.assertIn(f'"{item_id}"', text)

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

    def test_split_jobs_propagate_trusted_selection(self):
        for split, name in (("fit", "deepevidence-fit.yaml"), ("tune", "deepevidence-tune.yaml"), ("verifier", "deepevidence.yaml")):
            text = (ROOT / "benchmarks/biomedicine-deep-research/jobs" / name).read_text()
            self.assertIn(f'BIOAGENT_SPLIT: "{split}"', text)
            self.assertIn(f"split: {split}", text)

    def test_biodsbench_python_mapping_covers_every_item(self):
        manifest = json.loads((ROOT / "benchmarks/biodsbench/tasks/biodsbench-python/data/manifest.json").read_text())
        stats = manifest["splits"]["benchmark"]
        self.assertEqual(stats["source_count"], 118)
        self.assertEqual(stats["scorable_count"], 118)
        self.assertEqual(stats["oracle_verified"], 112)
        self.assertEqual(len(manifest["oracle_failures"]), 6)


if __name__ == "__main__":
    unittest.main()
